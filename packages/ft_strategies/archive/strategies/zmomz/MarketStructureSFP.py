# --- Necessary imports ---
import numpy as np
import pandas as pd
from pandas import DataFrame
from typing import Optional, Union
from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IntParameter, IStrategy, merge_informative_pair)

from datetime import datetime
import talib.abstract as ta
import pandas_ta as pta
from technical import qtpylib

class MarketStructureSFP(IStrategy):
    # Define the interface version for the strategy. This allows for new iterations of the strategy interface.
    INTERFACE_VERSION = 3

    # Set the optimal timeframe for the strategy. '1h' indicates a 1-hour candle duration.
    timeframe = '1h'

    # Specify if the strategy can take short positions. This strategy does not support shorting.
    can_short: bool = False

    # Define the minimal ROI for the strategy. This dictionary maps time (in minutes) to the desired ROI.
    minimal_roi = {
        '0': 1
    }

    # Set the optimal stop loss for the strategy. A stop loss of -10% is defined.
    stoploss = -1
    use_custom_stoploss = False

    # Enable trailing stop loss. Trailing stop loss follows the price movement to secure profits.
    trailing_stop = False

    # Configure the strategy to process only new candles. This reduces redundant calculations.
    process_only_new_candles = True

    # Define if the strategy should use exit signals, only exit at a profit, and ignore ROI if entry signal is present.
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = True

    # Set the number of candles required before the strategy starts producing valid signals.
    startup_candle_count: int = 30
    moving_average = 9

    # Optional order type mapping. This specifies the type of orders to use for entry, exit, and stoploss.
    order_types = {
        'entry': 'market',
        'exit': 'market',
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
        '''
        Configuration for plotting the indicators.
        This will add the specified indicators to the main plot and subplots for better visualization.
        '''
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
                'high_of_current_swing_high': {
                    'color': 'blue',
                    'type': 'scatter',
                    'plotly': {}
                },
                'low_of_current_swing_low': {
                    'color': 'purple',
                    'type': 'scatter',
                    'plotly': {}
                }
            }
        }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        '''
        Populate indicators for the given dataframe. This method identifies potential highs and lows in the market,
        confirms them, and updates the dataframe accordingly.
        '''
        # dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)
        # dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)

        # Initialize necessary columns on the first run
        if 'looking_for' not in dataframe.columns:
            dataframe['looking_for'] = 'high'

            # Initialize columns for potential highs/lows and confirmed highs/lows with current values
            columns_to_initialize = [
                '_of_potential','_of_current_high','_of_previous_high','_of_current_low','_of_previous_low',
                '_of_current_swing_high','_of_previous_swing_high','_of_current_swing_low','_of_previous_swing_low'
            ]
            for column in columns_to_initialize:
                dataframe[f'high{column}'] = dataframe['high']
                dataframe[f'low{column}'] = dataframe['low']
                dataframe[f'close{column}'] = dataframe['close']
                dataframe[f'open{column}'] = dataframe['open']

            # Explicitly set swing_high_date and swing_low_date columns to datetime64 type
            dataframe['swing_high_date'] = dataframe['date']
            dataframe['swing_low_date'] = dataframe['date']

        # Iterate through the dataframe to update indicators based on the previous row's values
        for i in range(1, len(dataframe)):
            # Check if we are currently looking for a high
            if dataframe['looking_for'].iloc[i - 1] == 'high':
                # Maintain previous low values by copying them to the current row
                for col in ['high_of_current_low', 'low_of_current_low', 'close_of_current_low', 'open_of_current_low',
                            'high_of_previous_low', 'low_of_previous_low', 'close_of_previous_low', 'open_of_previous_low']:
                    dataframe.at[i, col] = dataframe[col].iloc[i - 1]

                # Confirming a new high: If the current close price is less than the previous potential low
                if dataframe['close'].iloc[i] < dataframe['low_of_potential'].iloc[i - 1]:
                    # Update current high with the potential high values
                    for col in ['high', 'low', 'close', 'open']:
                        dataframe.at[i, f'{col}_of_current_high'] = dataframe[f'{col}_of_potential'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_potential'] = dataframe[col].iloc[i]
                        dataframe.at[i, f'{col}_of_previous_high'] = dataframe[f'{col}_of_current_high'].iloc[i - 1]

                    # We switch to looking for a low now that a high has been confirmed
                    dataframe.at[i, 'looking_for'] = 'low'

                    # Check if the new high is a new swing high
                    if dataframe['close_of_potential'].iloc[i - 1] > dataframe['high_of_current_swing_high'].iloc[i - 1]:
                        for col in ['high', 'low', 'close', 'open']:
                            dataframe.at[i, f'{col}_of_previous_swing_high'] = dataframe[f'{col}_of_current_swing_high'].iloc[i - 1]
                            dataframe.at[i, f'{col}_of_current_swing_high'] = dataframe[f'{col}_of_potential'].iloc[i - 1]

                        dataframe.at[i, 'swing_high_date'] = dataframe['date'].iloc[i]

                        # Determine the lowest current low in the range between the new and
                        # old swing highs

                        range_of_current_wave = dataframe.loc[dataframe['swing_high_date'] == dataframe['swing_high_date'].iloc[i - 1]]
                        lowest_current_low = range_of_current_wave['low_of_current_low'].min()
                        dataframe.at[i, 'low_of_current_swing_low'] = lowest_current_low

                        if not range_of_current_wave.loc[range_of_current_wave['low_of_current_low'] == lowest_current_low].empty:
                            for col in ['high', 'low', 'close', 'open']:
                                dataframe.at[i, f'{col}_of_current_swing_low'] = range_of_current_wave.loc[
                                    range_of_current_wave['low_of_current_low'] == lowest_current_low][f'{col}_of_current_low'].values[0]

                        for col in ['high', 'low', 'close', 'open']:
                            dataframe.at[i, f'{col}_of_previous_swing_low'] = dataframe[f'{col}_of_current_swing_low'].iloc[i - 1]

                        dataframe.at[i, 'swing_low_date'] = dataframe['date'].iloc[i]


                    # if the new high is not a new swing high
                    # we keep the previous values
                    else:
                        for col in ['high', 'low', 'close', 'open']:
                            dataframe.at[i, f'{col}_of_current_swing_high'] = dataframe[f'{col}_of_current_swing_high'].iloc[i - 1]
                            dataframe.at[i, f'{col}_of_previous_swing_high'] = dataframe[f'{col}_of_previous_swing_high'].iloc[i - 1]
                            dataframe.at[i, f'{col}_of_current_swing_low'] = dataframe[f'{col}_of_current_swing_low'].iloc[i - 1]
                            dataframe.at[i, f'{col}_of_previous_swing_low'] = dataframe[f'{col}_of_previous_swing_low'].iloc[i - 1]

                        dataframe.at[i, 'swing_high_date'] = dataframe['swing_high_date'].iloc[i - 1]
                        dataframe.at[i, 'swing_low_date'] = dataframe['swing_low_date'].iloc[i - 1]


                # checking if there is new potential high. if true so we change the potential candle
                # and keep the other candles as is

                elif dataframe['high'].iloc[i] > dataframe['high_of_potential'].iloc[i - 1]:
                    for col in ['high', 'low', 'close', 'open']:
                        dataframe.at[i, f'{col}_of_potential'] = dataframe[col].iloc[i]

                    for col in ['high', 'low', 'close', 'open']:
                        dataframe.at[i, f'{col}_of_current_high'] = dataframe[f'{col}_of_current_high'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_high'] = dataframe[f'{col}_of_previous_high'].iloc[i - 1]

                        dataframe.at[i, f'{col}_of_current_swing_high'] = dataframe[f'{col}_of_current_swing_high'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_swing_high'] = dataframe[f'{col}_of_previous_swing_high'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_current_swing_low'] = dataframe[f'{col}_of_current_swing_low'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_swing_low'] = dataframe[f'{col}_of_previous_swing_low'].iloc[i - 1]

                        dataframe.at[i, 'swing_high_date'] = dataframe['swing_high_date'].iloc[i - 1]
                        dataframe.at[i, 'swing_low_date'] = dataframe['swing_low_date'].iloc[i - 1]


                    dataframe.at[i, 'looking_for'] = 'high'

                #  if there is no new potential, we keep all the candles as is
                else:
                    for col in ['high', 'low', 'close', 'open']:
                        dataframe.at[i, f'{col}_of_current_high'] = dataframe[f'{col}_of_current_high'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_potential'] = dataframe[f'{col}_of_potential'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_high'] = dataframe[f'{col}_of_previous_high'].iloc[i - 1]


                        dataframe.at[i, f'{col}_of_current_swing_high'] = dataframe[f'{col}_of_current_swing_high'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_swing_high'] = dataframe[f'{col}_of_previous_swing_high'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_current_swing_low'] = dataframe[f'{col}_of_current_swing_low'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_swing_low'] = dataframe[f'{col}_of_previous_swing_low'].iloc[i - 1]

                        dataframe.at[i, 'swing_high_date'] = dataframe['swing_high_date'].iloc[i - 1]
                        dataframe.at[i, 'swing_low_date'] = dataframe['swing_low_date'].iloc[i - 1]

                    dataframe.at[i, 'looking_for'] = 'high'


            else:
            # We are here currently looking for a low
            # first we maintain previous high values by copying them to the current row
                for col in ['high_of_current_high', 'low_of_current_high', 'close_of_current_high', 'open_of_current_high',
                            'high_of_previous_high', 'low_of_previous_high', 'close_of_previous_high', 'open_of_previous_high']:
                    dataframe.at[i, col] = dataframe[col].iloc[i - 1]

                # Confirming a new low: If the current close price is higher than the previous potential high
                if dataframe['close'].iloc[i] > dataframe['high_of_potential'].iloc[i - 1]:
                    for col in ['high', 'low', 'close', 'open']:
                        dataframe.at[i, f'{col}_of_current_low'] = dataframe[f'{col}_of_potential'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_potential'] = dataframe[col].iloc[i]
                        dataframe.at[i, f'{col}_of_previous_low'] = dataframe[f'{col}_of_current_low'].iloc[i - 1]

                    # We switch to looking for a high now that a high has been confirmed
                    dataframe.at[i, 'looking_for'] = 'high'

                    # Check if the new low is a new swing low
                    if dataframe['close_of_potential'].iloc[i - 1] < dataframe['low_of_current_swing_low'].iloc[i - 1]:
                        for col in ['high', 'low', 'close', 'open']:
                            dataframe.at[i, f'{col}_of_previous_swing_low'] = dataframe[f'{col}_of_current_swing_low'].iloc[i - 1]
                            dataframe.at[i, f'{col}_of_current_swing_low'] = dataframe[f'{col}_of_potential'].iloc[i - 1]

                        dataframe.at[i, 'swing_low_date'] = dataframe['date'].iloc[i]

                        # Determine the highst current high in the range between the new and
                        # old swing lows

                        range_of_current_wave = dataframe.loc[dataframe['swing_low_date'] == dataframe['swing_low_date'].iloc[i - 1]]
                        highest_current_high = range_of_current_wave['high_of_current_high'].max()
                        dataframe.at[i, 'high_of_current_swing_high'] = highest_current_high

                        if not range_of_current_wave.loc[range_of_current_wave['high_of_current_high'] == highest_current_high].empty:
                            for col in ['high', 'low', 'close', 'open']:
                                dataframe.at[i, f'{col}_of_current_swing_high'] = range_of_current_wave.loc[
                                    range_of_current_wave['high_of_current_high'] == highest_current_high][f'{col}_of_current_high'].values[0]

                        for col in ['high', 'low', 'close', 'open']:
                            dataframe.at[i, f'{col}_of_previous_swing_high'] = dataframe[f'{col}_of_current_swing_high'].iloc[i - 1]

                        dataframe.at[i, 'swing_high_date'] = dataframe['date'].iloc[i]

                    # if the new low is not a new swing low
                    # we keep the previous values
                    else:
                        for col in ['high', 'low', 'close', 'open']:
                            dataframe.at[i, f'{col}_of_current_swing_high'] = dataframe[f'{col}_of_current_swing_high'].iloc[i - 1]
                            dataframe.at[i, f'{col}_of_previous_swing_high'] = dataframe[f'{col}_of_previous_swing_high'].iloc[i - 1]
                            dataframe.at[i, f'{col}_of_current_swing_low'] = dataframe[f'{col}_of_current_swing_low'].iloc[i - 1]
                            dataframe.at[i, f'{col}_of_previous_swing_low'] = dataframe[f'{col}_of_previous_swing_low'].iloc[i - 1]

                        dataframe.at[i, 'swing_high_date'] = dataframe['swing_high_date'].iloc[i - 1]
                        dataframe.at[i, 'swing_low_date'] = dataframe['swing_low_date'].iloc[i - 1]

                # checking if there is new potential low. if true so we change the potential candle
                # and keep the other candles as is

                elif dataframe['low'].iloc[i] < dataframe['low_of_potential'].iloc[i - 1]:
                    for col in ['high', 'low', 'close', 'open']:
                        dataframe.at[i, f'{col}_of_potential'] = dataframe[col].iloc[i]

                    for col in ['high', 'low', 'close', 'open']:
                        dataframe.at[i, f'{col}_of_current_low'] = dataframe[f'{col}_of_current_low'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_low'] = dataframe[f'{col}_of_previous_low'].iloc[i - 1]

                        dataframe.at[i, f'{col}_of_current_swing_high'] = dataframe[f'{col}_of_current_swing_high'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_swing_high'] = dataframe[f'{col}_of_previous_swing_high'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_current_swing_low'] = dataframe[f'{col}_of_current_swing_low'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_swing_low'] = dataframe[f'{col}_of_previous_swing_low'].iloc[i - 1]

                        dataframe.at[i, 'swing_high_date'] = dataframe['swing_high_date'].iloc[i - 1]
                        dataframe.at[i, 'swing_low_date'] = dataframe['swing_low_date'].iloc[i - 1]

                    dataframe.at[i, 'looking_for'] = 'low'

                #  if there is no new potential, we keep all the candles as is
                else:
                    for col in ['high', 'low', 'close', 'open']:
                        dataframe.at[i, f'{col}_of_current_low'] = dataframe[f'{col}_of_current_low'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_potential'] = dataframe[f'{col}_of_potential'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_low'] = dataframe[f'{col}_of_previous_low'].iloc[i - 1]


                        dataframe.at[i, f'{col}_of_current_swing_high'] = dataframe[f'{col}_of_current_swing_high'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_swing_high'] = dataframe[f'{col}_of_previous_swing_high'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_current_swing_low'] = dataframe[f'{col}_of_current_swing_low'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_swing_low'] = dataframe[f'{col}_of_previous_swing_low'].iloc[i - 1]

                        dataframe.at[i, 'swing_high_date'] = dataframe['swing_high_date'].iloc[i - 1]
                        dataframe.at[i, 'swing_low_date'] = dataframe['swing_low_date'].iloc[i - 1]

                    dataframe.at[i, 'looking_for'] = 'low'
            
            # print(dataframe.tail(40).to_string())

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        '''
        Define conditions for entering a long position based on Swing failure (SFP).
        '''
        dataframe.loc[
            (
                (dataframe['low_of_current_low'] < dataframe['low_of_previous_low']) &
                (dataframe['close_of_current_low'] > dataframe['low_of_previous_low']) 
                # &(dataframe['rsi'] < 30)
            ),
            'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        '''
        Define conditions for exiting a long position based on profit.
        Exit if the candle closes higher than the previous high.
        '''
        dataframe.loc[
            (
                (dataframe['close'] > dataframe['high_of_current_high'])
            ),
            'exit_long'] = 1

        return dataframe

    def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime, current_rate: float,
                        current_profit: float, **kwargs) -> float:
        '''
        Custom stop loss logic to place the stop loss under the previous low by ATR.
        '''
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        last_row = dataframe.iloc[-1]
        stop_loss_price = last_row['low_of_current_low']
        return stop_loss_price
