from typing import List, Union
import numpy as np
from .utils import add_linear_trends, area_fn, to_diff
from .rolling_agg import RollingAggregations


def generate_features_itblib(df, config: dict, last_rows: int = 0):
    """
    Generate derived features by adding them as new columns to the data frame.
    It is important that the same parameters are used for both training and prediction.

    Most features compute rolling aggregation. However, instead of absolute values, the difference
    of this rolling aggregation to the (longer) base rolling aggregation is computed.

    The window sizes are used for encoding feature/column names and might look like 'close_120'
    for average close price for the last 120 minutes (relative to the average base price).
    The column names are needed when preparing data for training or prediction.
    The easiest way to get them is to return from this function and copy and the
    corresponding config attribute.
    """
    use_differences = config.get("use_differences", True)
    base_window = config.get("base_window", True)
    windows = config.get("windows", True)
    functions = config.get("functions", True)

    features = []
    to_drop = []

    if use_differences:
        df["close"] = to_diff(df["close"])
        df["volume"] = to_diff(df["volume"])
        df["trades"] = to_diff(df["trades"])

    # close rolling mean. format: 'close_<window>'
    if not functions or "close_WMA" in functions:
        weight_column_name = "volume"  # None: no weighting; 'volume': volume average
        to_drop += RollingAggregations.add_past_weighted_aggregations(
            df, "close", weight_column_name, np.nanmean, base_window, suffix="", last_rows=last_rows
        )  # Base column
        features += RollingAggregations.add_past_weighted_aggregations(
            df,
            "close",
            weight_column_name,
            np.nanmean,
            windows,
            "",
            to_drop[-1],
            100.0,
            last_rows=last_rows,
        )

    # close rolling std. format: 'close_std_<window>'
    if not functions or "close_STD" in functions:
        to_drop += RollingAggregations.add_past_aggregations(
            df, "close", np.nanstd, base_window, last_rows=last_rows
        )  # Base column
        features += RollingAggregations.add_past_aggregations(
            df, "close", np.nanstd, windows, "_std", to_drop[-1], 100.0, last_rows=last_rows
        )

    # volume rolling mean. format: 'volume_<window>'
    if not functions or "volume_SMA" in functions:
        to_drop += RollingAggregations.add_past_aggregations(
            df, "volume", np.nanmean, base_window, suffix="", last_rows=last_rows
        )  # Base column
        features += RollingAggregations.add_past_aggregations(
            df, "volume", np.nanmean, windows, "", to_drop[-1], 100.0, last_rows=last_rows
        )

    # Span: high-low difference. format: 'span_<window>'
    if not functions or "span_SMA" in functions:
        df["span"] = df["high"] - df["low"]
        to_drop.append("span")
        to_drop += RollingAggregations.add_past_aggregations(
            df, "span", np.nanmean, base_window, suffix="", last_rows=last_rows
        )  # Base column
        features += RollingAggregations.add_past_aggregations(
            df, "span", np.nanmean, windows, "", to_drop[-1], 100.0, last_rows=last_rows
        )

    # Number of trades format: 'trades_<window>'
    if not functions or "trades_SMA" in functions:
        to_drop += RollingAggregations.add_past_aggregations(
            df, "trades", np.nanmean, base_window, suffix="", last_rows=last_rows
        )  # Base column
        features += RollingAggregations.add_past_aggregations(
            df, "trades", np.nanmean, windows, "", to_drop[-1], 100.0, last_rows=last_rows
        )

    # tb_base_av / volume varies around 0.5 in base currency. format: 'tb_base_<window>>'
    if not functions or "tb_base_SMA" in functions:
        df["tb_base"] = df["tb_base_av"] / df["volume"]
        to_drop.append("tb_base")
        to_drop += RollingAggregations.add_past_aggregations(
            df, "tb_base", np.nanmean, base_window, suffix="", last_rows=last_rows
        )  # Base column
        features += RollingAggregations.add_past_aggregations(
            df, "tb_base", np.nanmean, windows, "", to_drop[-1], 100.0, last_rows=last_rows
        )

    # UPDATE: do not generate, because very high correction (0.99999) with tb_base
    # tb_quote_av / quote_av varies around 0.5 in quote currency. format: 'tb_quote_<window>>'
    # df['tb_quote'] = df['tb_quote_av'] / df['quote_av']
    # to_drop.append('tb_quote')
    # to_drop += RollingAggregations.add_past_aggregations(df, 'tb_quote', np.nanmean, base_window, suffix='', last_rows=last_rows)  # Base column
    # features += RollingAggregations.add_past_aggregations(df, 'tb_quote', np.nanmean, windows, '', to_drop[-1], 100.0, last_rows=last_rows)

    # Area over and under latest close price
    if not functions or "close_AREA" in functions:
        features += add_area_ratio(
            df,
            is_future=False,
            column_name="close",
            windows=windows,
            suffix="_area",
            last_rows=last_rows,
        )

    # Linear trend
    if not functions or "close_SLOPE" in functions:
        features += add_linear_trends(
            df,
            is_future=False,
            column_name="close",
            windows=windows,
            suffix="_trend",
            last_rows=last_rows,
        )
    if not functions or "volume_SLOPE" in functions:
        features += add_linear_trends(
            df,
            is_future=False,
            column_name="volume",
            windows=windows,
            suffix="_trend",
            last_rows=last_rows,
        )

    df.drop(columns=to_drop, inplace=True)

    return features


def add_area_ratio(
    df,
    is_future: bool,
    column_name: str,
    windows: Union[int, List[int]],
    suffix: str = None,
    last_rows: int = 0,
) -> List[str]:
    """
    Add the area ratio feature to the DataFrame, comparing the area above and below a given element.

    For past data, the area is calculated by comparing each element to the preceding sub-series.
    For future data, the area is calculated by comparing each element to the subsequent sub-series.

    Parameters:
    - df: pd.DataFrame - The DataFrame to which the features will be added.
    - is_future: bool - If True, compare with future data; otherwise, with past data.
    - column_name: str - The column name on which to compute the area ratio.
    - windows: int or List[int] - The window sizes to compute the area ratio.
    - suffix: str, optional - Suffix to add to the new column name. Defaults to "_area_ratio".
    - last_rows: int, optional - Number of last rows to process. Default is 0 (process all rows).

    Returns:
    - List[str] - A list of newly added feature column names.
    """
    column = df[column_name]

    if isinstance(windows, int):
        windows = [windows]

    if suffix is None:
        suffix = "_area_ratio"

    features = []
    for w in windows:
        if last_rows == 0:
            ro = column.rolling(window=w, min_periods=max(1, w // 2))
            feature = ro.apply(area_fn, kwargs=dict(is_future=is_future), raw=True)
        else:
            feature = RollingAggregations._aggregate_last_rows(
                column, w, last_rows, area_fn, is_future
            )

        feature_name = f"{column_name}{suffix}_{w}"

        if is_future:
            df[feature_name] = feature.shift(periods=-(w - 1))
        else:
            df[feature_name] = feature

        features.append(feature_name)

    return features
