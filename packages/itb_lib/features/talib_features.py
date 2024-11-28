import sys
import importlib

import numpy as np
import pandas as pd

from .utils import _convert_to_relative



"""
Feature generators. 
A feature generator knows how to generate features from its delcarative specification in the config file.
"""


def generate_features_talib(df, config: dict, last_rows: int = 0):
    """
    Apply TA functions from talib according to the specified configuration parameters.

    config = {
        "parameters": {"relative": True, "relative_to_last": True, "percentage": True},
        "columns": ["close"],
        "functions": ["SMA"],
        "windows": [2, 3],  # If numbers, then to argument timeperiod. If dict, then
        "args": {},  # Pass to the function as additional arguments
        "names": "my_output",  # How the output feature(s) will be named
    }

    TA-lib is very sensitive to NaN values so that one NaN somewhere in the input series can produce
    NaN in output even if formally it does not influence it. For example, one NaN in the beginning of
    input series will produce NaN of SMA in the end with small window like 2.
    Therefore, NaN should be completely removed to get meaningful results (even if they formally do
    not influence the result values you are interested in).

    TODO Future extensions and improvement todos:
    * Column parameters:
        * Add math functions with two (or more) columns passed to certain arguments, no windows or parameters. Two TA-lib arguments: real0, real1. Alternatively, pass as a list (no argument names)
        * Currently it works only for one column (second ignored). Make it work for two and more input columns
        * If columns list is a dict, then key is argument to ta function, and value is column name (if ta function takes some custom arguments)
    * Window list parameter:
        * Currently, we can pass only one window per function. However, some TA-lib functions may take 2 or more windows. Think about how to pass such windows
        * Currently, windows are passed as a list. Introduce windows as a dict. The keys are used as argument names for this call.
    * args config parameter. It is passed in unchanged form to each TA-lib call
    * Post-processing and pre-processing parameters:
        * use_differences: if true then compute differences first
        * In addition to differences, another parameter is using log=2,10 etc.

    :param config:
    :return:
    """
    rel_base = config.get("parameters", {}).get("rel_base", False)
    rel_func = config.get("parameters", {}).get("rel_func", False)
    # If true, then relative values are multiplied by 100
    percentage = config.get("parameters", {}).get("percentage", False)
    # If true, then logarithm is applied to the result
    log = config.get("parameters", {}).get("log", False)

    #
    # talib module where all ta functions are defined. we use it below to resolve TA function names
    #
    mod_name = "talib"  # Functions are applied to a (rolling) series of windows
    talib_mod = sys.modules.get(mod_name)  # Try to load
    if talib_mod is None:  # If not yet imported
        try:
            talib_mod = importlib.import_module(mod_name)  # Try to import
        except Exception as e:
            raise ValueError(
                f"Cannot import module {mod_name}. Check if talib is installed correctly"
            )

    mod_name = "talib.stream"  # Functions which are applied to single window and return one value
    talib_mod_stream = sys.modules.get(mod_name)  # Try to load
    if talib_mod_stream is None:  # If not yet imported
        try:
            talib_mod_stream = importlib.import_module(mod_name)  # Try to import
        except Exception as e:
            raise ValueError(
                f"Cannot import module {mod_name}. Check if talib is installed correctly"
            )

    mod_name = "talib.abstract"  # We need this to get function annotations, particularly, if they are unstable (support stream mode)
    talib_mod_abstract = sys.modules.get(mod_name)  # Try to load
    if talib_mod_abstract is None:  # If not yet imported
        try:
            talib_mod_abstract = importlib.import_module(mod_name)  # Try to import
        except Exception as e:
            raise ValueError(
                f"Cannot import module {mod_name}. Check if talib is installed correctly"
            )

    #
    # Process configuration parameters and prepare all needed for feature generation
    #

    # Transform str/list and list to dict with argument names as keys and column names as values
    column_names = config.get("columns")
    if isinstance(column_names, str):
        column_names = {"real": column_names}  # Single default input series
    elif isinstance(column_names, list) and len(column_names) == 1:
        column_names = {"real": column_names[0]}  # Single default input series
    elif isinstance(column_names, list):
        column_names = {
            f"real{i}": col for i, col in enumerate(column_names)
        }  # Multiple default input series
    elif isinstance(column_names, dict):
        pass  # Do nothing
    else:
        raise ValueError(
            f"Columns are provided as a string, list or dict. Wrong type: {type(column_names)}"
        )

    # For each key, resolve name and interpolate data
    # Interpolate (we should always do it because one NaN in input can produce all NaNs in output)
    columns = {arg: df[col_name].interpolate() for arg, col_name in column_names.items()}

    col_out_names = "_".join(column_names.values())  # Join all column names

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
        fn_outs = []
        fn_out_names = []

        # Determine if the function support stream mode
        try:
            fn = getattr(talib_mod_abstract, func_name)  # Resolve function name
        except AttributeError as e:
            raise ValueError(
                f"Cannot resolve talib function name '{func_name}'. Check the (existence of) name of the function"
            )
        is_streamable_function = (
            fn.function_flags is None or "Function has an unstable period" not in fn.function_flags
        )

        # TODO: Currently disable stream functions
        is_streamable_function = False

        # Now this function will be called for each window as a parameter
        for j, w in enumerate(windows):

            #
            # Offline: The function will be executed in a rolling manner and applied to rolling windows
            # Only aggregation functions have window argument (arithmetic row-level functions do not have it)
            #
            if not last_rows or not w or not is_streamable_function:
                try:
                    fn = getattr(talib_mod, func_name)  # Resolve function name
                except AttributeError as e:
                    raise ValueError(
                        f"Cannot resolve talib function name '{func_name}'. Check the (existence of) name of the function"
                    )

                args = columns.copy()
                if w:
                    args["timeperiod"] = w
                if (
                    w == 1 and len(columns) == 1
                ):  # For window 1 use the original values (because talib fails to do this)
                    out = next(iter(columns.values()))
                else:
                    out = fn(**args)

            #
            # Online: In a loop, compute the specified number of single values for the manually prepared windows
            #
            else:
                try:
                    fn = getattr(talib_mod_stream, func_name)  # Resolve function name
                except AttributeError as e:
                    raise ValueError(
                        f"Cannot resolve talib.stream function name '{func_name}'. Check the (existence of) name of the function"
                    )

                # Here fn (function) is a different function from a different module (this function is applied to a single window rather than to rolling windows)
                out_values = []
                for r in range(last_rows):
                    # Remove r elements from the end
                    # Note that we do not remove elements from the start so the length is limited from one side only
                    args = {k: v.iloc[: len(v) - r] for k, v in columns.items()}
                    if w:
                        args["timeperiod"] = w

                    if (
                        w == 1 and len(columns) == 1
                    ):  # For window 1 use the original values (because talib fails to do this)
                        col = next(iter(columns.values()))
                        out_val = col.iloc[-r - 1]
                    else:
                        out_val = fn(**args)
                    out_values.append(out_val)

                # Then these values are transformed to a series
                out = pd.Series(data=np.nan, index=df.index, dtype=float)
                out.iloc[-last_rows:] = list(
                    reversed(out_values)
                )  # Assign values to the last elements

            #
            # Name of the output column
            #
            # Now combin[e: columnnames + functionname + [if prefix null window [i] | elif prefix str + window[i] | else if list prefix[i]]
            if not w:
                if not names:
                    out_name = f"{col_out_names}_{func_name}"
                elif isinstance(names, str):
                    out_name = names
                elif isinstance(names, list):
                    out_name = names[j]  # Should not happen
            else:
                out_name = f"{col_out_names}_{func_name}_"
                win_name = str(w)
                if not names:
                    out_name = out_name + win_name
                elif isinstance(names, str):
                    out_name = out_name + names + "_" + win_name
                elif isinstance(names, list):
                    out_name = out_name + names[j]

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
