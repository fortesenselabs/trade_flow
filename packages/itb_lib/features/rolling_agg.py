import numpy as np
import pandas as pd
from typing import Union, List
from sklearn import linear_model

"""
TODO: Make the static methods in RollingAggregations functions
"""

class RollingAggregations:
    """
    A class to compute rolling aggregations and trends on a DataFrame.

    This class provides methods to compute various aggregations (weighted and unweighted),
    area ratios, linear trends, and other transformations on specified columns in a DataFrame.
    """

    @staticmethod
    def add_past_weighted_aggregations(
        df,
        column_name: str,
        weight_column_name: str,
        fn,
        windows: Union[int, List[int]],
        suffix=None,
        rel_column_name: str = None,
        rel_factor: float = 1.0,
        last_rows: int = 0,
    ):
        """
        Compute past weighted aggregations on the specified column.

        Args:
            df (pd.DataFrame): Input DataFrame.
            column_name (str): The name of the column to aggregate.
            weight_column_name (str): The name of the column with weights.
            fn: The aggregation function to apply.
            windows (Union[int, List[int]]): Window size(s) for aggregation.
            suffix (str, optional): Suffix for the output column name.
            rel_column_name (str, optional): Column for relative calculation.
            rel_factor (float, optional): Factor to multiply results.
            last_rows (int, optional): Number of last rows to aggregate.

        Returns:
            List[str]: Names of the newly created feature columns.
        """
        return RollingAggregations._add_weighted_aggregations(
            df,
            False,
            column_name,
            weight_column_name,
            fn,
            windows,
            suffix,
            rel_column_name,
            rel_factor,
            last_rows,
        )

    @staticmethod
    def add_past_aggregations(
        df,
        column_name: str,
        fn,
        windows: Union[int, List[int]],
        suffix=None,
        rel_column_name: str = None,
        rel_factor: float = 1.0,
        last_rows: int = 0,
    ):
        """
        Compute past aggregations on the specified column.

        Args:
            df (pd.DataFrame): Input DataFrame.
            column_name (str): The name of the column to aggregate.
            fn: The aggregation function to apply.
            windows (Union[int, List[int]]): Window size(s) for aggregation.
            suffix (str, optional): Suffix for the output column name.
            rel_column_name (str, optional): Column for relative calculation.
            rel_factor (float, optional): Factor to multiply results.
            last_rows (int, optional): Number of last rows to aggregate.

        Returns:
            List[str]: Names of the newly created feature columns.
        """
        return RollingAggregations._add_aggregations(
            df, False, column_name, fn, windows, suffix, rel_column_name, rel_factor, last_rows
        )

    @staticmethod
    def add_future_aggregations(
        df,
        column_name: str,
        fn,
        windows: Union[int, List[int]],
        suffix=None,
        rel_column_name: str = None,
        rel_factor: float = 1.0,
        last_rows: int = 0,
    ):
        """
        Compute future aggregations on the specified column.

        Args:
            df (pd.DataFrame): Input DataFrame.
            column_name (str): The name of the column to aggregate.
            fn: The aggregation function to apply.
            windows (Union[int, List[int]]): Window size(s) for aggregation.
            suffix (str, optional): Suffix for the output column name.
            rel_column_name (str, optional): Column for relative calculation.
            rel_factor (float, optional): Factor to multiply results.
            last_rows (int, optional): Number of last rows to aggregate.

        Returns:
            List[str]: Names of the newly created feature columns.
        """
        return RollingAggregations._add_aggregations(
            df, True, column_name, fn, windows, suffix, rel_column_name, rel_factor, last_rows
        )

    @staticmethod
    def _add_aggregations(
        df,
        is_future: bool,
        column_name: str,
        fn,
        windows: Union[int, List[int]],
        suffix=None,
        rel_column_name: str = None,
        rel_factor: float = 1.0,
        last_rows: int = 0,
    ):
        """
        Compute moving aggregations over past or future values of the specified base column using the specified windows.

        Args:
            df (pd.DataFrame): Input DataFrame.
            is_future (bool): Flag indicating future aggregation.
            column_name (str): The name of the column to aggregate.
            fn: The aggregation function to apply.
            windows (Union[int, List[int]]): Window size(s) for aggregation.
            suffix (str, optional): Suffix for the output column name.
            rel_column_name (str, optional): Column for relative calculation.
            rel_factor (float, optional): Factor to multiply results.
            last_rows (int, optional): Number of last rows to aggregate.

        Returns:
            List[str]: Names of the newly created feature columns.
        """
        column = df[column_name]

        if isinstance(windows, int):
            windows = [windows]

        if rel_column_name:
            rel_column = df[rel_column_name]

        if suffix is None:
            suffix = "_" + fn.__name__

        features = []
        for w in windows:
            if not last_rows:
                feature = column.rolling(window=w, min_periods=max(1, w // 2)).apply(fn, raw=True)
            else:
                feature = RollingAggregations._aggregate_last_rows(column, w, last_rows, fn)

            if is_future:
                feature = feature.shift(periods=-w)

            feature_name = column_name + suffix + "_" + str(w)
            features.append(feature_name)
            if rel_column_name:
                df[feature_name] = rel_factor * (feature - rel_column) / rel_column
            else:
                df[feature_name] = rel_factor * feature

        return features

    @staticmethod
    def _add_weighted_aggregations(
        df,
        is_future: bool,
        column_name: str,
        weight_column_name: str,
        fn,
        windows: Union[int, List[int]],
        suffix=None,
        rel_column_name: str = None,
        rel_factor: float = 1.0,
        last_rows: int = 0,
    ):
        """
        Compute weighted rolling aggregations on the specified column.

        Args:
            df (pd.DataFrame): Input DataFrame.
            is_future (bool): Flag indicating future aggregation.
            column_name (str): The name of the column to aggregate.
            weight_column_name (str): The name of the column with weights.
            fn: The aggregation function to apply.
            windows (Union[int, List[int]]): Window size(s) for aggregation.
            suffix (str, optional): Suffix for the output column name.
            rel_column_name (str, optional): Column for relative calculation.
            rel_factor (float, optional): Factor to multiply results.
            last_rows (int, optional): Number of last rows to aggregate.

        Returns:
            List[str]: Names of the newly created feature columns.
        """
        column = df[column_name]

        weight_column = (
            df[weight_column_name]
            if weight_column_name
            else pd.Series(data=1.0, index=column.index)
        )
        products_column = column * weight_column

        if isinstance(windows, int):
            windows = [windows]

        if rel_column_name:
            rel_column = df[rel_column_name]

        if suffix is None:
            suffix = "_" + fn.__name__

        features = []
        for w in windows:
            if not last_rows:
                feature = products_column.rolling(window=w, min_periods=max(1, w // 2)).apply(
                    fn, raw=True
                )
                weights = weight_column.rolling(window=w, min_periods=max(1, w // 2)).apply(
                    fn, raw=True
                )
            else:
                feature = RollingAggregations._aggregate_last_rows(
                    products_column, w, last_rows, fn
                )
                weights = RollingAggregations._aggregate_last_rows(weight_column, w, last_rows, fn)

            feature = feature / weights

            if is_future:
                feature = feature.shift(periods=-w)

            feature_name = column_name + suffix + "_" + str(w)
            features.append(feature_name)
            if rel_column_name:
                df[feature_name] = rel_factor * (feature - rel_column) / rel_column
            else:
                df[feature_name] = rel_factor * feature

        return features

    @staticmethod
    def add_area_ratio(
        df,
        is_future: bool,
        column_name: str,
        windows: Union[int, List[int]],
        suffix=None,
        last_rows: int = 0,
    ):
        """
        Compute area ratios based on the specified column.

        Args:
            df (pd.DataFrame): Input DataFrame.
            is_future (bool): Flag indicating future area ratio.
            column_name (str): The name of the column to compute ratios.
            windows (Union[int, List[int]]): Window size(s) for aggregation.
            suffix (str, optional): Suffix for the output column name.
            last_rows (int, optional): Number of last rows to aggregate.

        Returns:
            List[str]: Names of the newly created feature columns.
        """
        column = df[column_name]

        if isinstance(windows, int):
            windows = [windows]

        if suffix is None:
            suffix = "_" + "area_ratio"

        features = []
        for w in windows:
            if not last_rows:
                feature = column.rolling(window=w, min_periods=max(1, w // 2)).sum()
            else:
                feature = RollingAggregations._aggregate_last_rows(column, w, last_rows, np.sum)

            if is_future:
                feature = feature.shift(periods=-w)

            feature_name = column_name + suffix + "_" + str(w)
            features.append(feature_name)
            df[feature_name] = feature / column

        return features

    @staticmethod
    def add_linear_trend(df, column_name: str, windows: Union[int, List[int]], suffix=None):
        """
        Compute linear trends for the specified column using ordinary least squares regression.

        Args:
            df (pd.DataFrame): Input DataFrame.
            column_name (str): The name of the column to compute trends.
            windows (Union[int, List[int]]): Window size(s) for regression.
            suffix (str, optional): Suffix for the output column name.

        Returns:
            List[str]: Names of the newly created feature columns.
        """
        column = df[column_name]

        if isinstance(windows, int):
            windows = [windows]

        if suffix is None:
            suffix = "_linear_trend"

        features = []
        for w in windows:
            feature_name = column_name + suffix + "_" + str(w)
            features.append(feature_name)

            # Rolling linear regression
            def linear_trend(series):
                if len(series) < 2:
                    return np.nan
                x = np.arange(len(series)).reshape(-1, 1)
                y = series.values
                model = linear_model.LinearRegression()
                model.fit(x, y)
                return model.coef_[0]

            df[feature_name] = column.rolling(window=w, min_periods=1).apply(
                linear_trend, raw=False
            )

        return features

    @staticmethod
    def _aggregate_last_rows(column, w, last_rows, fn):
        """
        Aggregate the last rows based on the specified function.

        Args:
            column (pd.Series): The column to aggregate.
            w (int): Window size.
            last_rows (int): Number of last rows to aggregate.
            fn: The aggregation function to apply.

        Returns:
            pd.Series: Aggregated results.
        """
        if last_rows >= w:
            return column.rolling(window=w, min_periods=w).apply(fn, raw=True)
        else:
            return (
                column.rolling(window=w, min_periods=1)
                .apply(fn, raw=True)
                .shift(periods=-(w - last_rows))
            )



    @staticmethod
    def fillna(df, column_name: str, value=None):
        """
        Fill NaN values in the specified column.

        Args:
            df (pd.DataFrame): Input DataFrame.
            column_name (str): The name of the column to fill.
            value: The value to fill NaNs with.

        Returns:
            pd.DataFrame: DataFrame with NaNs filled.
        """
        df[column_name].fillna(value, inplace=True)
        return df
        
