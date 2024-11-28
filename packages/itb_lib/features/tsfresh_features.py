from .rolling_agg import RollingAggregations


def generate_features_tsfresh(df, config: dict, last_rows: int = 0):
    """
    This feature generator relies on tsfresh functions.

    tsfresh depends on matrixprofile for which binaries are not available for many versions.
    Therefore, the use of tsfresh may require Python 3.8
    """
    # It is imported here in order to avoid installation of tsfresh if it is not used
    import tsfresh.feature_extraction.feature_calculators as tsf

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

    windows = config.get("windows")
    if not isinstance(windows, list):
        windows = [windows]

    features = []
    for w in windows:
        ro = column.rolling(window=w, min_periods=max(1, w // 2))

        #
        # Statistics
        #
        feature_name = column_name + "_skewness_" + str(w)
        if not last_rows:
            df[feature_name] = ro.apply(tsf.skewness, raw=True)
        else:
            df[feature_name] = RollingAggregations._aggregate_last_rows(
                column, w, last_rows, tsf.skewness
            )  # OR skew (but it computes different values)
        features.append(feature_name)

        feature_name = column_name + "_kurtosis_" + str(w)
        if not last_rows:
            df[feature_name] = ro.apply(tsf.kurtosis, raw=True)
        else:
            df[feature_name] = RollingAggregations._aggregate_last_rows(
                column, w, last_rows, tsf.kurtosis
            )  # OR kurtosis
        features.append(feature_name)

        # count_above_mean, benford_correlation, mean_changes
        feature_name = column_name + "_msdc_" + str(w)
        if not last_rows:
            df[feature_name] = ro.apply(tsf.mean_second_derivative_central, raw=True)
        else:
            df[feature_name] = RollingAggregations._aggregate_last_rows(
                column, w, last_rows, tsf.mean_second_derivative_central
            )
        features.append(feature_name)

        #
        # Counts
        # first/last_location_of_maximum/minimum
        #
        feature_name = column_name + "_lsbm_" + str(w)
        if not last_rows:
            df[feature_name] = ro.apply(tsf.longest_strike_below_mean, raw=True)
        else:
            df[feature_name] = RollingAggregations._aggregate_last_rows(
                column, w, last_rows, tsf.longest_strike_below_mean
            )
        features.append(feature_name)

        feature_name = column_name + "_fmax_" + str(w)
        if not last_rows:
            df[feature_name] = ro.apply(tsf.first_location_of_maximum, raw=True)
        else:
            df[feature_name] = RollingAggregations._aggregate_last_rows(
                column, w, last_rows, tsf.first_location_of_maximum
            )
        features.append(feature_name)

    return features
