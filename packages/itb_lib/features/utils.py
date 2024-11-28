import itertools
from typing import List, Union
import numpy as np
import pandas as pd
from scipy import stats

from .rolling_agg import RollingAggregations


def fmax_fn(x):
    return np.argmax(x) / len(x) if len(x) > 0 else np.NaN


def lsbm_fn(x):
    """
    The longest consecutive interval of values higher than the mean.
    A similar feature might be higher than the last (current) value.
    Area under mean/last value is also a variation of this approach but instead of computing the sum of length, we compute their integral (along with the values).

    Equivalent of tsfresh.feature_extraction.feature_calculators.longest_strike_below_mean
    """

    def _get_length_sequences_where(x):
        # [0,1,0,0,1,1,1,0,0,1,0,1,1] -> [1, 3, 1, 2]
        # [0,True,0,0,True,True,True,0,0,True,0,True,True] -> [1, 3, 1, 2]
        # [0,True,0,0,1,True,1,0,0,True,0,1,True] -> [1, 3, 1, 2]
        if len(x) == 0:
            return [0]
        else:
            res = [len(list(group)) for value, group in itertools.groupby(x) if value == 1]
            return res if len(res) > 0 else [0]

    return np.max(_get_length_sequences_where(x < np.mean(x))) if x.size > 0 else 0


def _convert_to_relative(fn_outs: list, rel_base, rel_func, percentage):
    # Convert to relative values and percentage (except for the last output)
    rel_outs = []
    size = len(fn_outs)
    for i, feature in enumerate(fn_outs):
        if not rel_base:
            rel_out = fn_outs[i]  # No change requested
        elif (rel_base == "next" or rel_base == "last") and i == size - 1:
            rel_out = fn_outs[i]  # No change because it is the last (no next - it is the base)
        elif (rel_base == "prev" or rel_base == "first") and i == 0:
            rel_out = fn_outs[i]  # No change because it is the first (no previous - it is the base)

        elif rel_base == "next" or rel_base == "last":
            if rel_base == "next":
                base = fn_outs[i + 1]  # Relative to next
            elif rel_base == "last":
                base = fn_outs[size - 1]  # Relative to last
            else:
                raise ValueError(f"Unknown value of the 'rel_base' config parameter: {rel_base=}")

            if rel_func == "rel":
                rel_out = feature / base
            elif rel_func == "diff":
                rel_out = feature - base
            elif rel_func == "rel_diff":
                rel_out = (feature - base) / base
            else:
                raise ValueError(f"Unknown value of the 'rel_func' config parameter: {rel_func=}")

        elif rel_base == "prev" or rel_base == "first":
            if rel_base == "prev":
                base = fn_outs[i - 1]  # Relative to previous
            elif rel_base == "first":
                base = fn_outs[size - 1]  # Relative to first
            else:
                raise ValueError(f"Unknown value of the 'rel_base' config parameter: {rel_base=}")

            if rel_func == "rel":
                rel_out = feature / base
            elif rel_func == "diff":
                rel_out = feature - base
            elif rel_func == "rel_diff":
                rel_out = (feature - base) / base
            else:
                raise ValueError(f"Unknown value of the 'rel_func' config parameter: {rel_func=}")

        if percentage:
            rel_out = rel_out * 100.0

        rel_out.name = fn_outs[i].name
        rel_outs.append(rel_out)

    return rel_outs


def add_threshold_feature(df, column_name: str, thresholds: list, out_names: list):
    """

    :param df:
    :param column_name: Column with values to compare with the thresholds
    :param thresholds: List of thresholds. For each of them an output column will be generated
    :param out_names: List of output column names (same length as thresholds)
    :return: List of output column names
    """

    for i, threshold in enumerate(thresholds):
        out_name = out_names[i]
        if threshold > 0.0:  # Max high
            if abs(threshold) >= 0.75:  # Large threshold
                df[out_name] = (
                    df[column_name] >= threshold
                )  # At least one high is greater than the threshold
            else:  # Small threshold
                df[out_name] = df[column_name] <= threshold  # All highs are less than the threshold
        else:  # Min low
            if abs(threshold) >= 0.75:  # Large negative threshold
                df[out_name] = (
                    df[column_name] <= threshold
                )  # At least one low is less than the (negative) threshold
            else:  # Small threshold
                df[out_name] = (
                    df[column_name] >= threshold
                )  # All lows are greater than the (negative) threshold

    return out_names


def area_fn(x, is_future: bool) -> float:
    """
    Computes the area ratio for a series of values, comparing the area above and below a reference point.

    Parameters:
    - x: array-like - Series of values.
    - is_future: bool - Whether to use the first element (future) or last element (past) as the reference point.

    Returns:
    - float - Scaled area ratio between -1 and 1.
    """
    level = x[0] if is_future else x[-1]
    x_diff = x - level
    a = np.nansum(x_diff)
    b = np.nansum(np.abs(x_diff))
    pos = (b + a) / 2
    ratio = pos / b  # in [0, 1]
    ratio = (ratio * 2) - 1  # scale to [-1, +1]
    return ratio


def add_linear_trends(
    df,
    is_future: bool,
    column_name: str,
    windows: Union[int, List[int]],
    suffix: str = None,
    last_rows: int = 0,
) -> List[str]:
    """
    Add a linear trend feature to the DataFrame, computing the slope of the fitted line over a window.

    For past data, it computes the slope using the previous sub-series.
    For future data, it computes the slope using the subsequent sub-series.

    Parameters:
    - df: pd.DataFrame - The DataFrame to which the features will be added.
    - is_future: bool - If True, compute trends using future data; otherwise, use past data.
    - column_name: str - The column name on which to compute the trend.
    - windows: int or List[int] - The window sizes to compute the trend.
    - suffix: str, optional - Suffix to add to the new column name. Defaults to "_trend".
    - last_rows: int, optional - Number of last rows to process. Default is 0 (process all rows).

    Returns:
    - List[str] - A list of newly added feature column names.
    """
    column = df[column_name]

    if isinstance(windows, int):
        windows = [windows]

    if suffix is None:
        suffix = "_trend"

    features = []
    for w in windows:
        if last_rows == 0:
            ro = column.rolling(window=w, min_periods=max(1, w // 2))
            feature = ro.apply(slope_fn, raw=True)
        else:
            feature = RollingAggregations._aggregate_last_rows(column, w, last_rows, slope_fn)

        feature_name = f"{column_name}{suffix}_{w}"

        if is_future:
            df[feature_name] = feature.shift(periods=-(w - 1))
        else:
            df[feature_name] = feature

        features.append(feature_name)

    return features


def slope_fn(x) -> float:
    """
    Computes the slope of a fitted linear regression line for a series of values.

    Parameters:
    - x: array-like - Series of values.

    Returns:
    - float - The slope of the linear regression line.
    """
    X_array = np.arange(len(x))
    y_array = x

    if np.isnan(y_array).any():
        valid_mask = ~np.isnan(y_array)
        X_array = X_array[valid_mask]
        y_array = y_array[valid_mask]

    slope, _, _, _, _ = stats.linregress(X_array, y_array)
    return slope


def to_log_diff(sr) -> pd.Series:
    """
    Converts a series to its log differences.

    Parameters:
    - sr: pd.Series - The input series.

    Returns:
    - pd.Series - The log-differenced series.
    """
    return np.log(sr).diff()


def to_diff_NEW(sr) -> pd.Series:
    """
    Computes the percentage difference of a series.

    Parameters:
    - sr: pd.Series - The input series.

    Returns:
    - pd.Series - The percentage difference.
    """
    return 100 * sr.diff() / sr


def to_diff(sr) -> pd.Series:
    """
    Computes the percentage difference of a series relative to the current and previous values.

    Parameters:
    - sr: pd.Series - The input series.

    Returns:
    - pd.Series - The percentage difference.
    """

    def diff_fn(x):
        return 100 * (x[1] - x[0]) / x[0]

    return sr.rolling(window=2, min_periods=2).apply(diff_fn, raw=True)
