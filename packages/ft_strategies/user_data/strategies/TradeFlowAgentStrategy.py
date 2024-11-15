# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these imports ---
from functools import reduce
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from pandas import DataFrame
from typing import Optional, Union

from freqtrade.strategy import (
    IStrategy,
    Trade,
    Order,
    PairLocks,
    informative,  # @informative decorator
    BooleanParameter,
    CategoricalParameter,
    DecimalParameter,
    IntParameter,
    RealParameter,
    # timeframe helpers
    timeframe_to_minutes,
    timeframe_to_next_date,
    timeframe_to_prev_date,
    # Strategy helper functions
    merge_informative_pair,
    stoploss_from_absolute,
    stoploss_from_open,
)

# Additional libraries
import talib.abstract as ta
from technical import qtpylib
from ft_strategies.indicators import OptimizedSupportResistanceIndicator


class TradeFlowAgentStrategy(IStrategy):
    """
    A sample reinforcement learning (RL) agent strategy for Freqtrade. This strategy is
    built to interface with FreqAI for feature engineering and training.

    The strategy includes:
        - Feature engineering functions to generate technical indicators
        - Custom target setting for RL models
        - Population of entry and exit conditions based on the model's predictions

    Documentation on Freqtrade strategy customization can be found here:
    https://www.freqtrade.io/en/latest/strategy-customization/
    """

    INTERFACE_VERSION = 3  # Strategy interface version

    # Set the optimal timeframe for the strategy.
    timeframe = "3m"

    # Can this strategy go short?
    can_short: bool = False

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -0.10

    # Enable trailing stoploss functionality.
    trailing_stop = True

    # Define the number of candles required before producing valid signals
    startup_candle_count: int = 60

    def informative_pairs(self):
        """
        Define additional, informative pair/interval combinations to be cached from the exchange.
        These pair/interval combinations are non-tradeable, unless they are part
        of the whitelist as well.
        For more information, please consult the documentation
        :return: List of tuples in the format (pair, interval)
            Sample: return [("ETH/USDT", "5m"),
                            ("BTC/USDT", "15m"),
                            ]
        """
        return []

    def feature_engineering_expand_all(
        self, dataframe: DataFrame, period: int, **kwargs
    ) -> DataFrame:
        """
        Expands the defined features for the strategy, including:
        - Normalized close price series
        - Returns over various time periods (1-month, 2-month, 3-month, 1-year)
        - Volatility adjustment for returns
        - MACD indicators using TA-Lib
        - RSI (Relative Strength Index) with a 30-day lookback

        :param dataframe: The strategy dataframe to receive the features
        :param period: The period for the indicators (for example, EMA or RSI period)
        :return: The updated dataframe with new features
        """

        # Existing features (RSI, MFI, ADX, SMA, EMA)
        dataframe["%-rsi-period"] = ta.RSI(dataframe, timeperiod=30)  # RSI (Relative Strength Index) with a 30-period lookback
        dataframe["%-mfi-period"] = ta.MFI(dataframe, timeperiod=period)
        dataframe["%-adx-period"] = ta.ADX(dataframe, timeperiod=period)
        dataframe["%-sma-period"] = ta.SMA(dataframe, timeperiod=period)
        dataframe["%-ema-period"] = ta.EMA(dataframe, timeperiod=period)

        # MACD
        macd = ta.MACD(dataframe, fastperiod=12, slowperiod=26, signalperiod=9)
        dataframe["%-macd"] = macd["macd"]
        dataframe["%-macdsignal"] = macd["macdsignal"]
        dataframe["%-macdhist"] = macd["macdhist"]

        # Calculate the 63-period rolling standard deviation of prices for volatility normalization
        dataframe["%-price_volatility_63"] = dataframe["close"].rolling(window=63).std()

        # Normalize MACD indicator by dividing it by the 63-period rolling price volatility
        # dataframe["%-normalized_macd"] = macd["macd"] / dataframe["%-price_volatility_63"]

        # Normalized Close Price Series: (normalized by daily volatility adjustment)
        # Calculate daily returns
        dataframe["%-daily_returns"] = dataframe["close"].pct_change()

        # Calculate 252-period rolling volatility (standard deviation of daily returns)
        dataframe["%-volatility_252"] = (
            dataframe["%-daily_returns"].ewm(span=60, min_periods=1).std()
        )

        # Calculate returns for multiple periods (1-month, 2-months, 3-months, 1-year)
        dataframe["%-returns_one_month"] = dataframe["close"].pct_change(
            periods=21
        )  # 1 month = 21 trading periods
        dataframe["%-returns_two_months"] = dataframe["close"].pct_change(
            periods=42
        )  # 2 months = 42 trading periods
        dataframe["%-returns_three_months"] = dataframe["close"].pct_change(
            periods=63
        )  # 3 months = 63 trading periods
        dataframe["%-returns_one_year"] = dataframe["close"].pct_change(
            periods=252
        )  # 1 year = 252 trading periods

        # Normalize returns over the past 1-year period (252 periods) using daily volatility
        dataframe["%-normalized_annual_returns"] = (
            dataframe["%-daily_returns"].rolling(window=252).mean() / dataframe["%-volatility_252"]
        )

        # Bollinger Bands - Weighted (EMA based instead of SMA)
        weighted_bollinger = qtpylib.weighted_bollinger_bands(
            qtpylib.typical_price(dataframe), window=20, stds=2
        )
        dataframe["%-wbb_upperband"] = weighted_bollinger["upper"]
        dataframe["%-wbb_lowerband"] = weighted_bollinger["lower"]
        dataframe["%-wbb_middleband"] = weighted_bollinger["mid"]
        dataframe["%-wbb_percent"] = (
            (dataframe["close"] - dataframe["%-wbb_lowerband"]) /
            (dataframe["%-wbb_upperband"] - dataframe["%-wbb_lowerband"])
        )
        dataframe["%-wbb_width"] = (
            (weighted_bollinger["upper"] - weighted_bollinger["lower"]) /
            weighted_bollinger["mid"]
        )

        # Pattern Recognition - Bullish candlestick patterns
        # ------------------------------------
        # Hammer: values [0, 100]
        dataframe['%-CDLHAMMER'] = ta.CDLHAMMER(dataframe)
        # Inverted Hammer: values [0, 100]
        dataframe['%-CDLINVERTEDHAMMER'] = ta.CDLINVERTEDHAMMER(dataframe)
        # Dragonfly Doji: values [0, 100]
        dataframe['%-CDLDRAGONFLYDOJI'] = ta.CDLDRAGONFLYDOJI(dataframe)
        # Piercing Line: values [0, 100]
        dataframe['%-CDLPIERCING'] = ta.CDLPIERCING(dataframe) # values [0, 100]
        # Morningstar: values [0, 100]
        dataframe['%-CDLMORNINGSTAR'] = ta.CDLMORNINGSTAR(dataframe) # values [0, 100]
        # Three White Soldiers: values [0, 100]
        dataframe['%-CDL3WHITESOLDIERS'] = ta.CDL3WHITESOLDIERS(dataframe) # values [0, 100]

        # Pattern Recognition - Bearish candlestick patterns
        # ------------------------------------
        # Hanging Man: values [0, 100]
        dataframe['%-CDLHANGINGMAN'] = ta.CDLHANGINGMAN(dataframe)
        # Shooting Star: values [0, 100]
        dataframe['%-CDLSHOOTINGSTAR'] = ta.CDLSHOOTINGSTAR(dataframe)
        # Gravestone Doji: values [0, 100]
        dataframe['%-CDLGRAVESTONEDOJI'] = ta.CDLGRAVESTONEDOJI(dataframe)
        # Dark Cloud Cover: values [0, 100]
        dataframe['%-CDLDARKCLOUDCOVER'] = ta.CDLDARKCLOUDCOVER(dataframe)
        # Evening Doji Star: values [0, 100]
        dataframe['%-CDLEVENINGDOJISTAR'] = ta.CDLEVENINGDOJISTAR(dataframe)
        # Evening Star: values [0, 100]
        dataframe['%-CDLEVENINGSTAR'] = ta.CDLEVENINGSTAR(dataframe)

        # Pattern Recognition - Bullish/Bearish candlestick patterns
        # ------------------------------------
        # Three Line Strike: values [0, -100, 100]
        dataframe['%-CDL3LINESTRIKE'] = ta.CDL3LINESTRIKE(dataframe)
        # Spinning Top: values [0, -100, 100]
        dataframe['%-CDLSPINNINGTOP'] = ta.CDLSPINNINGTOP(dataframe) # values [0, -100, 100]
        # Engulfing: values [0, -100, 100]
        dataframe['%-CDLENGULFING'] = ta.CDLENGULFING(dataframe) # values [0, -100, 100]
        # Harami: values [0, -100, 100]
        dataframe['%-CDLHARAMI'] = ta.CDLHARAMI(dataframe) # values [0, -100, 100]
        # Three Outside Up/Down: values [0, -100, 100]
        dataframe['%-CDL3OUTSIDE'] = ta.CDL3OUTSIDE(dataframe) # values [0, -100, 100]
        # Three Inside Up/Down: values [0, -100, 100]
        dataframe['%-CDL3INSIDE'] = ta.CDL3INSIDE(dataframe) # values [0, -100, 100]

        sr_indicator = OptimizedSupportResistanceIndicator(self.raw_features)
        get_sr_levels = sr_indicator.detect(window_size=1)

        dataframe['%-support_levels'] = get_sr_levels["Support"]
        dataframe['%-resistance_levels'] = get_sr_levels["Resistance"]
        
        return dataframe

    def feature_engineering_expand_basic(self, dataframe: DataFrame, **kwargs) -> DataFrame:
        """
        Expands basic features using config-defined settings like `include_timeframes` and
        `include_shifted_candles`.

        Features added: pct-change, raw volume, raw price.

        :param dataframe: The strategy dataframe to receive the features
        :return: The updated dataframe with basic features
        """
        dataframe["%-pct-change"] = dataframe["close"].pct_change()
        # dataframe["%-raw_volume"] = dataframe["volume"]
        # dataframe["%-raw_price"] = dataframe["close"]
        return dataframe

    def feature_engineering_standard(self, dataframe: DataFrame, **kwargs) -> DataFrame:
        """
        Adds standard features necessary for RL models and custom features like `day_of_week`
        and `hour_of_day`.

        :param dataframe: The strategy dataframe to receive the features
        :return: The updated dataframe with standard features
        """
        dataframe["%-raw_close"] = dataframe["close"]
        dataframe["%-raw_open"] = dataframe["open"]
        dataframe["%-raw_high"] = dataframe["high"]
        dataframe["%-raw_low"] = dataframe["low"]
        dataframe["%-raw_volume"] = dataframe["volume"]

        dataframe["%-day_of_week"] = (dataframe["date"].dt.dayofweek + 1) / 7
        dataframe["%-hour_of_day"] = (dataframe["date"].dt.hour + 1) / 25
        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, **kwargs) -> DataFrame:
        """
        Sets the targets for the FreqAI model. For RL, this is a neutral filler until the agent
        provides its action.

        :param dataframe: The strategy dataframe to receive the targets
        :return: The updated dataframe with targets
        """
        dataframe["&-action"] = 0  # Default neutral target for RL
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Populates the indicators in the dataframe, using FreqAI's start method.

        :param dataframe: The strategy dataframe to receive the indicators
        :param metadata: Metadata associated with the strategy
        :return: The updated dataframe with indicators
        """
        dataframe = self.freqai.start(dataframe, metadata, self)
        return dataframe

    def populate_entry_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        """
        Populates the entry conditions for the strategy based on model predictions.

        :param df: The strategy dataframe to receive the entry trends
        :param metadata: Metadata associated with the strategy
        :return: The updated dataframe with entry trends
        """
        enter_long_conditions = [df["do_predict"] == 1, df["&-action"] == 1]
        if enter_long_conditions:
            df.loc[
                reduce(lambda x, y: x & y, enter_long_conditions), ["enter_long", "enter_tag"]
            ] = (1, "long")

        enter_short_conditions = [df["do_predict"] == 1, df["&-action"] == 3]
        if enter_short_conditions:
            df.loc[
                reduce(lambda x, y: x & y, enter_short_conditions), ["enter_short", "enter_tag"]
            ] = (1, "short")

        return df

    def populate_exit_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        """
        Populates the exit conditions for the strategy based on model predictions.

        :param df: The strategy dataframe to receive the exit trends
        :param metadata: Metadata associated with the strategy
        :return: The updated dataframe with exit trends
        """
        exit_long_conditions = [df["do_predict"] == 1, df["&-action"] == 2]
        if exit_long_conditions:
            df.loc[reduce(lambda x, y: x & y, exit_long_conditions), "exit_long"] = 1

        exit_short_conditions = [df["do_predict"] == 1, df["&-action"] == 4]
        if exit_short_conditions:
            df.loc[reduce(lambda x, y: x & y, exit_short_conditions), "exit_short"] = 1

        return df
