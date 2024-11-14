import numba
import numpy as np
import pandas as pd
from ft_strategies.indicators.base import Indicator


class SupportResistanceIndicator(Indicator):
    """
    Class for calculating support and resistance levels using pivot points and local min/max detection.

    References:
    -----------
        - https://trendspider.com/learning-center/enhancing-your-trading-strategy-with-rolling-window-indicators/
        - https://www.babypips.com/learn/forex/how-to-calculate-pivot-points

    """

    def __init__(self, df: pd.DataFrame):
        """
        Initialize the SupportResistanceIndicator with a DataFrame.

        Parameters:
        -----------
            df (pd.DataFrame): The input DataFrame containing 'high', 'low', and 'close' columns.
        """
        super().__init__(df)

    def calculate_pivot_points(self):
        """
        Calculate pivot points and support/resistance levels for each row in the DataFrame.

        Returns:
            pd.DataFrame: DataFrame with calculated pivot points and support/resistance levels.
        """
        pivot_points = pd.DataFrame()
        pivot_points["Pivot"] = (self.df["high"] + self.df["low"] + self.df["close"]) / 3
        pivot_points["Resistance_1"] = (2 * pivot_points["Pivot"]) - self.df["low"]
        pivot_points["Support_1"] = (2 * pivot_points["Pivot"]) - self.df["high"]
        pivot_points["Resistance_2"] = pivot_points["Pivot"] + (self.df["high"] - self.df["low"])
        pivot_points["Support_2"] = pivot_points["Pivot"] - (self.df["high"] - self.df["low"])
        pivot_points["Resistance_3"] = self.df["high"] + 2 * (
            pivot_points["Pivot"] - self.df["low"]
        )
        pivot_points["Support_3"] = self.df["low"] - 2 * (self.df["high"] - pivot_points["Pivot"])

        return pivot_points

    def detect_local_min_max(self, window_size: int = 5):
        """
        Detect local minima and maxima in the DataFrame to identify support and resistance levels.

        Parameters:
        -----------
            window_size (int): Size of the rolling window to detect local peaks and troughs.

        Returns:
        --------
            tuple: Lists of tuples for support levels and resistance levels.
        """
        support_levels = []
        resistance_levels = []

        # Rolling window to check local minima and maxima
        for i in range(window_size, len(self.df) - window_size):
            # Check local low (support)
            if self.df["low"][i] == self.df["low"][i - window_size : i + window_size].min():
                support_levels.append((self.df.index[i], self.df["low"][i]))
            # Check local high (resistance)
            if self.df["high"][i] == self.df["high"][i - window_size : i + window_size].max():
                resistance_levels.append((self.df.index[i], self.df["high"][i]))

        return support_levels, resistance_levels

    def get_all_indicators(self, window_size: int = 5):
        """
        Get both pivot points and local min/max support and resistance levels.

        Parameters:
            window_size (int): Size of the rolling window to detect local peaks and troughs.

        Returns:
            dict: A dictionary containing pivot points and local support/resistance levels.
        """
        pivot_points = self.calculate_pivot_points()
        support_levels, resistance_levels = self.detect_local_min_max(window_size=window_size)

        return {
            "pivot_points": pivot_points,
            "support_levels": support_levels,
            "resistance_levels": resistance_levels,
        }


"""
    Optimized for calculating support and resistance levels using pivot points and local min/max detection.   
"""


@numba.njit
def calculate_pivot_points_array(high, low, close):
    """
    Numba-optimized calculation of pivot points and support/resistance levels.
    """
    length = len(high)
    pivot_points = np.empty(length)
    resistance_1 = np.empty(length)
    support_1 = np.empty(length)
    resistance_2 = np.empty(length)
    support_2 = np.empty(length)
    resistance_3 = np.empty(length)
    support_3 = np.empty(length)

    for i in range(length):
        pivot = (high[i] + low[i] + close[i]) / 3
        pivot_points[i] = pivot
        resistance_1[i] = (2 * pivot) - low[i]
        support_1[i] = (2 * pivot) - high[i]
        resistance_2[i] = pivot + (high[i] - low[i])
        support_2[i] = pivot - (high[i] - low[i])
        resistance_3[i] = high[i] + 2 * (pivot - low[i])
        support_3[i] = low[i] - 2 * (high[i] - pivot)

    return pivot_points, resistance_1, support_1, resistance_2, support_2, resistance_3, support_3


@numba.njit
def _op_detect_local_min_max(lows, highs, window_size):
    """
    Numba-optimized function to detect local minima and maxima.

    Parameters:
        lows (numpy.ndarray): Array of low prices.
        highs (numpy.ndarray): Array of high prices.
        window_size (int): Size of the rolling window.

    Returns:
        tuple: Indices of support levels and resistance levels.
    """
    length = len(lows)
    support_indices = []
    resistance_indices = []

    for i in range(window_size, length - window_size):
        if lows[i] == np.min(lows[i - window_size : i + window_size]):
            support_indices.append(i)
        if highs[i] == np.max(highs[i - window_size : i + window_size]):
            resistance_indices.append(i)

    return support_indices, resistance_indices


class OptimizedSupportResistanceIndicator(SupportResistanceIndicator):
    """
    Optimized class for calculating support and resistance levels using pivot points and local min/max detection.

    References:
    -----------
        - https://trendspider.com/learning-center/enhancing-your-trading-strategy-with-rolling-window-indicators/
        - https://www.babypips.com/learn/forex/how-to-calculate-pivot-points
    """

    def __init__(self, df: pd.DataFrame):
        """
        Initialize the SupportResistanceIndicator with a DataFrame.

        Parameters:
        -----------
        df (pd.DataFrame): The input DataFrame containing 'high', 'low', and 'close' columns.
        """
        super().__init__(df)

    def calculate_pivot_points(self):
        """
        Calculate pivot points and support/resistance levels for each row in the DataFrame.

        Returns:
            pd.DataFrame: DataFrame with calculated pivot points and support/resistance levels.
        """
        high = self.df["high"].values
        low = self.df["low"].values
        close = self.df["close"].values

        pivot_points, resistance_1, support_1, resistance_2, support_2, resistance_3, support_3 = (
            calculate_pivot_points_array(high, low, close)
        )

        pivot_points_df = pd.DataFrame(
            {
                "Pivot": pivot_points,
                "Resistance_1": resistance_1,
                "Support_1": support_1,
                "Resistance_2": resistance_2,
                "Support_2": support_2,
                "Resistance_3": resistance_3,
                "Support_3": support_3,
            }
        )

        return pivot_points_df

    def detect_local_min_max(self, window_size: int = 5):
        """
        Detect local minima and maxima in the DataFrame to identify support and resistance levels.

        Parameters:
            window_size (int): Size of the rolling window to detect local peaks and troughs.

        Returns:
            tuple: Lists of tuples for support levels and resistance levels.
        """
        lows = self.df["low"].values
        highs = self.df["high"].values
        dates = self.df.index.values

        support_indices, resistance_indices = _op_detect_local_min_max(lows, highs, window_size)

        support_levels = [(dates[i], lows[i]) for i in support_indices]
        resistance_levels = [(dates[i], highs[i]) for i in resistance_indices]

        return support_levels, resistance_levels

    def get_all_indicators(self, window_size: int = 5):
        """
        Get both pivot points and local min/max support and resistance levels.

        Parameters:
            window_size (int): Size of the rolling window to detect local peaks and troughs.

        Returns:
            dict: A dictionary containing pivot points and local support/resistance levels.
        """
        pivot_points = self.calculate_pivot_points()
        support_levels, resistance_levels = self.detect_local_min_max(window_size=window_size)

        return {
            "pivot_points": pivot_points,
            "support_levels": support_levels,
            "resistance_levels": resistance_levels,
        }
