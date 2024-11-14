# --- Necessary imports ---
import numpy as np
import pandas as pd
from pandas import DataFrame
from typing import Optional, Union
from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IntParameter, IStrategy, merge_informative_pair)
import talib.abstract as ta
import pandas_ta as pta
from technical import qtpylib


class MarketStructureStrategy(IStrategy):
    # Define the interface version for the strategy. This allows for new iterations of the strategy interface.
    INTERFACE_VERSION = 3

    # Set the optimal timeframe for the strategy. '1h' indicates a 1-hour candle duration.
    timeframe = '1h'

    # Specify if the strategy can take short positions. This strategy does not support shorting.
    can_short: bool = False

    # Define the minimal ROI for the strategy. This dictionary maps time (in minutes) to the desired ROI.
    minimal_roi = {
        "60": 0.01,
        "30": 0.02,
        "0": 0.04
    }

    # Set the optimal stop loss for the strategy. A stop loss of -10% is defined.
    stoploss = -0.10

    # Disable trailing stop loss. Trailing stop loss follows the price movement to secure profits.
    trailing_stop = False

    # Configure the strategy to process only new candles. This reduces redundant calculations.
    process_only_new_candles = True

    # Define if the strategy should use exit signals, only exit at a profit, and ignore ROI if entry signal is present.
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Set the number of candles required before the strategy starts producing valid signals.
    startup_candle_count: int = 30

    # Define strategy parameters for RSI. These parameters are adjustable within the specified range.
    buy_rsi = IntParameter(10, 40, default=30, space="buy")
    sell_rsi = IntParameter(60, 90, default=70, space="sell")

    # Optional order type mapping. This specifies the type of orders to use for entry, exit, and stoploss.
    order_types = {
        'entry': 'limit',
        'exit': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Optional order time in force. This specifies the duration for which an order remains active.
    order_time_in_force = {
        'entry': 'GTC',  # Good 'Til Canceled
        'exit': 'GTC'
    }

    @property
    def plot_config(self):
        """
        Configuration for plotting the indicators.
        This will add the specified indicators to the main plot and subplots for better visualization.
        """
        return {
            'main_plot': {
                'high_of_current_high': {
                    'color': 'green',
                    'type': 'scatter',
                    'plotly': {}
                },
                'low_of_current_low': {
                    'color': 'red',
                    'type': 'scatter',
                    'plotly': {}
                },
                'high_of_previous_high': {
                    'color': 'blue',
                    'type': 'scatter',
                    'plotly': {}
                },
                'low_of_previous_low': {
                    'color': 'purple',
                    'type': 'scatter',
                    'plotly': {}
                }
            },
            'subplots': {
                "Potential Highs and Lows": {
                    'high_of_potential': {
                        'color': 'orange',
                        'type': 'scatter',
                        'plotly': {}
                    },
                    'low_of_potential': {
                        'color': 'brown',
                        'type': 'scatter',
                        'plotly': {}
                    }
                }
            }
        }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Populate indicators for the given dataframe. This method identifies potential highs and lows in the market,
        confirms them, and updates the dataframe accordingly.
        """

        # Initialize necessary columns on the first run
        if 'looking_for' not in dataframe.columns:
            dataframe['looking_for'] = "high"  # Start by looking for a high initially

            # Initialize columns for potential highs/lows and confirmed highs/lows with current values
            dataframe['high_of_potential'] = dataframe['high']
            dataframe['low_of_potential'] = dataframe['low']
            dataframe['close_of_potential'] = dataframe['close']
            dataframe['open_of_potential'] = dataframe['open']

            dataframe['high_of_current_high'] = dataframe['high']
            dataframe['low_of_current_high'] = dataframe['low']
            dataframe['close_of_current_high'] = dataframe['close']
            dataframe['open_of_current_high'] = dataframe['open']

            dataframe['high_of_previous_high'] = dataframe['high']
            dataframe['low_of_previous_high'] = dataframe['low']
            dataframe['close_of_previous_high'] = dataframe['close']
            dataframe['open_of_previous_high'] = dataframe['open']

            dataframe['high_of_current_low'] = dataframe['high']
            dataframe['low_of_current_low'] = dataframe['low']
            dataframe['close_of_current_low'] = dataframe['close']
            dataframe['open_of_current_low'] = dataframe['open']

            dataframe['high_of_previous_low'] = dataframe['high']
            dataframe['low_of_previous_low'] = dataframe['low']
            dataframe['close_of_previous_low'] = dataframe['close']
            dataframe['open_of_previous_low'] = dataframe['open']

        # Iterate through the dataframe to update indicators based on the previous row's values
        for i in range(1, len(dataframe)):
            # Check if we are currently looking for a high
            if dataframe['looking_for'].iloc[i-1] == "high":
                # Maintain previous low values by copying them to the current row
                dataframe.at[i, 'high_of_current_low'] = dataframe['high_of_current_low'].iloc[i-1]
                dataframe.at[i, 'low_of_current_low'] = dataframe['low_of_current_low'].iloc[i-1]
                dataframe.at[i, 'close_of_current_low'] = dataframe['close_of_current_low'].iloc[i-1]
                dataframe.at[i, 'open_of_current_low'] = dataframe['open_of_current_low'].iloc[i-1]

                dataframe.at[i, 'high_of_previous_low'] = dataframe['high_of_previous_low'].iloc[i-1]
                dataframe.at[i, 'low_of_previous_low'] = dataframe['low_of_previous_low'].iloc[i-1]
                dataframe.at[i, 'close_of_previous_low'] = dataframe['close_of_previous_low'].iloc[i-1]
                dataframe.at[i, 'open_of_previous_low'] = dataframe['open_of_previous_low'].iloc[i-1]

                # Confirming a new high: If the current close price is less than the previous potential low
                if dataframe['close'].iloc[i] < dataframe['low_of_potential'].iloc[i-1]:
                    # Update current high with the potential high values
                    dataframe.at[i, 'high_of_current_high'] = dataframe['high_of_potential'].iloc[i-1]
                    dataframe.at[i, 'low_of_current_high'] = dataframe['low_of_potential'].iloc[i-1]
                    dataframe.at[i, 'close_of_current_high'] = dataframe['close_of_potential'].iloc[i-1]
                    dataframe.at[i, 'open_of_current_high'] = dataframe['open_of_potential'].iloc[i-1]

                    # Set new potential high values to current values
                    dataframe.at[i, 'high_of_potential'] = dataframe['high'].iloc[i]
                    dataframe.at[i, 'low_of_potential'] = dataframe['low'].iloc[i]
                    dataframe.at[i, 'close_of_potential'] = dataframe['close'].iloc[i]
                    dataframe.at[i, 'open_of_potential'] = dataframe['open'].iloc[i]

                    # Update previous high with the current high values
                    dataframe.at[i, 'high_of_previous_high'] = dataframe['high_of_current_high'].iloc[i-1]
                    dataframe.at[i, 'low_of_previous_high'] = dataframe['low_of_current_high'].iloc[i-1]
                    dataframe.at[i, 'close_of_previous_high'] = dataframe['close_of_current_high'].iloc[i-1]
                    dataframe.at[i, 'open_of_previous_high'] = dataframe['open_of_current_high'].iloc[i-1]

                    # We switch to looking for a low now that a high has been confirmed
                    dataframe.at[i, 'looking_for'] = 'low'
                # Checking if there's a new potential high: If the current close price is higher than the previous potential close
                elif dataframe['close'].iloc[i] > dataframe['close_of_potential'].iloc[i-1]:
                    # Update the potential high values with current values
                    dataframe.at[i, 'low_of_potential'] = dataframe['low'].iloc[i]
                    dataframe.at[i, 'high_of_potential'] = dataframe['high'].iloc[i]
                    dataframe.at[i, 'close_of_potential'] = dataframe['close'].iloc[i]
                    dataframe.at[i, 'open_of_potential'] = dataframe['open'].iloc[i]

                    # Maintain current and previous high values
                    dataframe.at[i, 'high_of_current_high'] = dataframe['high_of_current_high'].iloc[i-1]
                    dataframe.at[i, 'low_of_current_high'] = dataframe['low_of_current_high'].iloc[i-1]
                    dataframe.at[i, 'close_of_current_high'] = dataframe['close_of_current_high'].iloc[i-1]
                    dataframe.at[i, 'open_of_current_high'] = dataframe['open_of_current_high'].iloc[i-1]

                    dataframe.at[i, 'high_of_previous_high'] = dataframe['high_of_previous_high'].iloc[i-1]
                    dataframe.at[i, 'low_of_previous_high'] = dataframe['low_of_previous_high'].iloc[i-1]
                    dataframe.at[i, 'close_of_previous_high'] = dataframe['close_of_previous_high'].iloc[i-1]
                    dataframe.at[i, 'open_of_previous_high'] = dataframe['open_of_previous_high'].iloc[i-1]

                    # Continue looking for a high
                    dataframe.at[i, 'looking_for'] = 'high'
                else:
                    # No new high or potential high: maintain all current and previous values
                    dataframe.at[i, 'high_of_current_high'] = dataframe['high_of_current_high'].iloc[i-1]
                    dataframe.at[i, 'low_of_current_high'] = dataframe['low_of_current_high'].iloc[i-1]
                    dataframe.at[i, 'close_of_current_high'] = dataframe['close_of_current_high'].iloc[i-1]
                    dataframe.at[i, 'open_of_current_high'] = dataframe['open_of_current_high'].iloc[i-1]

                    dataframe.at[i, 'high_of_potential'] = dataframe['high_of_potential'].iloc[i-1]
                    dataframe.at[i, 'low_of_potential'] = dataframe['low_of_potential'].iloc[i-1]
                    dataframe.at[i, 'close_of_potential'] = dataframe['close_of_potential'].iloc[i-1]
                    dataframe.at[i, 'open_of_potential'] = dataframe['open_of_potential'].iloc[i-1]

                    dataframe.at[i, 'high_of_previous_high'] = dataframe['high_of_previous_high'].iloc[i-1]
                    dataframe.at[i, 'low_of_previous_high'] = dataframe['low_of_previous_high'].iloc[i-1]
                    dataframe.at[i, 'close_of_previous_high'] = dataframe['close_of_previous_high'].iloc[i-1]
                    dataframe.at[i, 'open_of_previous_high'] = dataframe['open_of_previous_high'].iloc[i-1]

                    # Continue looking for a high
                    dataframe.at[i, 'looking_for'] = 'high'
            else:
                # Maintain previous high values by copying them to the current row
                dataframe.at[i, 'high_of_current_high'] = dataframe['high_of_current_high'].iloc[i-1]
                dataframe.at[i, 'low_of_current_high'] = dataframe['low_of_current_high'].iloc[i-1]
                dataframe.at[i, 'close_of_current_high'] = dataframe['close_of_current_high'].iloc[i-1]
                dataframe.at[i, 'open_of_current_high'] = dataframe['open_of_current_high'].iloc[i-1]

                dataframe.at[i, 'high_of_previous_high'] = dataframe['high_of_previous_high'].iloc[i-1]
                dataframe.at[i, 'low_of_previous_high'] = dataframe['low_of_previous_high'].iloc[i-1]
                dataframe.at[i, 'close_of_previous_high'] = dataframe['close_of_previous_high'].iloc[i-1]
                dataframe.at[i, 'open_of_previous_high'] = dataframe['open_of_previous_high'].iloc[i-1]

                # Confirming a new low: If the current close price is higher than the previous potential high
                if dataframe['close'].iloc[i] > dataframe['high_of_potential'].iloc[i-1]:
                    # Update current low with the potential low values
                    dataframe.at[i, 'high_of_current_low'] = dataframe['high_of_potential'].iloc[i-1]
                    dataframe.at[i, 'low_of_current_low'] = dataframe['low_of_potential'].iloc[i-1]
                    dataframe.at[i, 'close_of_current_low'] = dataframe['close_of_potential'].iloc[i-1]
                    dataframe.at[i, 'open_of_current_low'] = dataframe['open_of_potential'].iloc[i-1]

                    # Set new potential low values to current values
                    dataframe.at[i, 'high_of_potential'] = dataframe['high'].iloc[i]
                    dataframe.at[i, 'low_of_potential'] = dataframe['low'].iloc[i]
                    dataframe.at[i, 'close_of_potential'] = dataframe['close'].iloc[i]
                    dataframe.at[i, 'open_of_potential'] = dataframe['open'].iloc[i]

                    # Update previous low with the current low values
                    dataframe.at[i, 'high_of_previous_low'] = dataframe['high_of_current_low'].iloc[i-1]
                    dataframe.at[i, 'low_of_previous_low'] = dataframe['low_of_current_low'].iloc[i-1]
                    dataframe.at[i, 'close_of_previous_low'] = dataframe['close_of_current_low'].iloc[i-1]
                    dataframe.at[i, 'open_of_previous_low'] = dataframe['open_of_current_low'].iloc[i-1]

                    # We switch to looking for a high now that a low has been confirmed
                    dataframe.at[i, 'looking_for'] = 'high'
                # Checking if there's a new potential low: If the current close price is lower than the previous potential close
                elif dataframe['close'].iloc[i] < dataframe['close_of_potential'].iloc[i-1]:
                    # Update the potential low values with current values
                    dataframe.at[i, 'low_of_potential'] = dataframe['low'].iloc[i]
                    dataframe.at[i, 'high_of_potential'] = dataframe['high'].iloc[i]
                    dataframe.at[i, 'close_of_potential'] = dataframe['close'].iloc[i]
                    dataframe.at[i, 'open_of_potential'] = dataframe['open'].iloc[i]

                    # Maintain current and previous low values
                    dataframe.at[i, 'high_of_current_low'] = dataframe['high_of_current_low'].iloc[i-1]
                    dataframe.at[i, 'low_of_current_low'] = dataframe['low_of_current_low'].iloc[i-1]
                    dataframe.at[i, 'close_of_current_low'] = dataframe['close_of_current_low'].iloc[i-1]
                    dataframe.at[i, 'open_of_current_low'] = dataframe['open_of_current_low'].iloc[i-1]

                    dataframe.at[i, 'high_of_previous_low'] = dataframe['high_of_previous_low'].iloc[i-1]
                    dataframe.at[i, 'low_of_previous_low'] = dataframe['low_of_previous_low'].iloc[i-1]
                    dataframe.at[i, 'close_of_previous_low'] = dataframe['close_of_previous_low'].iloc[i-1]
                    dataframe.at[i, 'open_of_previous_low'] = dataframe['open_of_previous_low'].iloc[i-1]

                    # Continue looking for a low
                    dataframe.at[i, 'looking_for'] = 'low'
                else:
                    # No new low or potential low: maintain all current and previous values
                    dataframe.at[i, 'high_of_current_low'] = dataframe['high_of_current_low'].iloc[i-1]
                    dataframe.at[i, 'low_of_current_low'] = dataframe['low_of_current_low'].iloc[i-1]
                    dataframe.at[i, 'close_of_current_low'] = dataframe['close_of_current_low'].iloc[i-1]
                    dataframe.at[i, 'open_of_current_low'] = dataframe['open_of_current_low'].iloc[i-1]

                    dataframe.at[i, 'high_of_potential'] = dataframe['high_of_potential'].iloc[i-1]
                    dataframe.at[i, 'low_of_potential'] = dataframe['low_of_potential'].iloc[i-1]
                    dataframe.at[i, 'close_of_potential'] = dataframe['close_of_potential'].iloc[i-1]
                    dataframe.at[i, 'open_of_potential'] = dataframe['open_of_potential'].iloc[i-1]

                    dataframe.at[i, 'high_of_previous_low'] = dataframe['high_of_previous_low'].iloc[i-1]
                    dataframe.at[i, 'low_of_previous_low'] = dataframe['low_of_previous_low'].iloc[i-1]
                    dataframe.at[i, 'close_of_previous_low'] = dataframe['close_of_previous_low'].iloc[i-1]
                    dataframe.at[i, 'open_of_previous_low'] = dataframe['open_of_previous_low'].iloc[i-1]

                    # Continue looking for a low
                    dataframe.at[i, 'looking_for'] = 'low'

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Define conditions for entering a long position based on Change of Character (CHOCH).
        """
        # Create a new column 'enter_long' in the dataframe
        # Set the value to 1 if the conditions for entering a long position are met
        dataframe.loc[
            (
                (dataframe['looking_for'] == 'low') &  # Check if the last state was looking for a low
                (dataframe['close'] > dataframe['high_of_current_high'])  # Confirm a new high
            ),
            'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Define conditions for exiting a long position based on profit.
        Exit if the candle closes higher than the previous high.
        """
        # Create a new column 'exit_long' in the dataframe
        # Set the value to 1 if the conditions for exiting a long position are met
        dataframe.loc[
            (
                (dataframe['close'] > dataframe['high_of_previous_high'])  # Exit condition based on profit
            ),
            'exit_long'] = 1

        return dataframe

    def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime, current_rate: float,
                        current_profit: float, **kwargs) -> float:
        """
        Custom stop loss logic to place the stop loss under the previous low by ATR.
        """
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)

        # Calculate the ATR (Average True Range) for volatility-based stop loss
        atr = ta.ATR(dataframe, timeperiod=14).iloc[-1]

        # Get the last row from the dataframe
        last_row = dataframe.iloc[-1]

        # Calculate the stop loss price as previous low minus ATR
        stop_loss_price = last_row['low_of_previous_low'] - atr

        # Ensure the stop loss is not higher than the current rate (no protective stop loss higher than entry price)
        stop_loss_pct = (current_rate - stop_loss_price) / current_rate

        # Return the stop loss percentage as a negative value
        return stop_loss_pct
