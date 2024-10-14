import numpy as np
import pandas as pd

import scipy.stats as stats
from .rolling_agg import RollingAggregations
from .utils import _convert_to_relative, fmax_fn, lsbm_fn, slope_fn, area_fn


def generate_features_itbstats(df, config: dict, last_rows: int = 0):
    """
    Statistical and various other features.

    In particular, it is intended to replace functions from tsfresh as well as implement
    functions which are not available in other libraries like volume weighted close price.

    Currently applied to only one input column.
    Currently generates all functions - 'functions' parameter is not used.
    """
    rel_base = config.get("parameters", {}).get("rel_base", False)
    rel_func = config.get("parameters", {}).get("rel_func", False)
    # If true, then relative values are multiplied by 100
    percentage = config.get("parameters", {}).get("percentage", False)
    # If true, then logarithm is applied to the result
    log = config.get("parameters", {}).get("log", False)

    # Transform str/list and list to dict with argument names as keys and column names as values
    column_names = config.get("columns")
    if not column_names:
        raise ValueError(f"No input column for feature generator 'stats': {column_names}")

    if isinstance(column_names, str):
        column_name = column_names
    elif isinstance(column_names, list):
        column_name = column_names[0]
    elif isinstance(column_names, dict):
        column_name = next(iter(column_names.values()))
    else:
        raise ValueError(
            f"Columns are provided as a string, list or dict. Wrong type: {type(column_names)}"
        )

    column = df[column_name].interpolate()

    func_names = config.get("functions")
    if not isinstance(func_names, list):
        func_names = [func_names]

    windows = config.get("windows")
    if not isinstance(windows, list):
        windows = [windows]

    names = config.get("names")

    #
    # For each function, make several calls for each window size
    #
    outs = []
    features = []
    for func_name in func_names:

        # Resolve function name to function reference
        args = tuple()
        bias = config.get("parameters", {}).get("bias", False)  # By default false (as in pandas)
        if func_name.lower() == "scipy_skew":
            fn = stats.skew  # scipy skew is very slow
            args = (0, bias)
        elif func_name.lower() == "pandas_skew":
            fn = lambda x: pd.Series(x).skew()
        elif func_name.lower() == "scipy_kurtosis":
            fn = stats.kurtosis
            args = (0, bias)
        elif func_name.lower() == "pandas_kurtosis":
            fn = lambda x: pd.Series(x).kurtosis()
        elif func_name.lower() == "lsbm":
            fn = lsbm_fn
        elif func_name.lower() == "fmax":
            fn = fmax_fn
        elif func_name.lower() == "mean":
            fn = np.nanmean
        elif func_name.lower() == "std":
            fn = np.nanstd
        elif func_name.lower() == "area":
            fn = area_fn
            args = (False,)
        elif func_name.lower() == "slope":
            fn = slope_fn
        else:
            raise ValueError(f"Unknown function '{func_name}' of feature generator {'itbstats'}")

        fn_outs = []
        fn_out_names = []

        # Now this function will be called for each window as a parameter
        for j, w in enumerate(windows):
            out_name = column_name + "_" + func_name + "_" + str(w)
            if not last_rows:
                ro = column.rolling(window=w, min_periods=max(1, w // 2))
                out = ro.apply(fn, args=args, raw=True)
            else:
                out = RollingAggregations._aggregate_last_rows(column, w, last_rows, fn, *args)

            fn_out_names.append(out_name)
            out.name = out_name
            fn_outs.append(out)

        # Convert to relative values and percentage (except for the last output)
        fn_outs = _convert_to_relative(fn_outs, rel_base, rel_func, percentage)

        features.extend(fn_out_names)
        outs.extend(fn_outs)

    for out in outs:
        df[out.name] = np.log(out) if log else out

    return features
