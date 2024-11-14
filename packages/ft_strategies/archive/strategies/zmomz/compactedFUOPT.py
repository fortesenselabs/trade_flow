import numpy as np
import pandas as pd
from pandas import DataFrame
from typing import Optional, Union
from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IntParameter, IStrategy, informative, merge_informative_pair)

from datetime import datetime
import talib.abstract as ta
import pandas_ta as pta
from technical import qtpylib

class compactedFUOPT(IStrategy):
    INTERFACE_VERSION = 3
    can_short: bool = True
    minimal_roi = {"0": 1}     # 100% profit after 0 minutes (virtually impossible)
    use_stop_on_candle_close = True
    use_custom_stoploss = False
    

    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = True
    ignore_roi_if_entry_signal = True
    startup_candle_count: int = 30

    # factors to optimize
    timeframe = '1h'
    stoploss = -0.333
    trailing_stop = True
    trailing_stop_positive = 0.013
    trailing_stop_positive_offset = 0.048
    trailing_only_offset_is_reached = True
    long_multiplier = DecimalParameter(1.01, 1.10, default=1.02, space='buy')
    short_multiplier = DecimalParameter(0.90, 0.99, default=0.936, space='buy')
    xlevrage = IntParameter(1, 20, default=5, space='buy')

    order_types = {
        'entry': 'market',
        'exit': 'market',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    order_time_in_force = {
        'entry': 'GTC',
        'exit': 'GTC'
    }

    @property
    def plot_config(self):
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
        if 'looking_for' not in dataframe.columns:
            dataframe['looking_for'] = 'high'
            columns_to_initialize = [
                '_of_potential','_of_current_high','_of_previous_high','_of_current_low','_of_previous_low',
                '_of_current_swing_high','_of_previous_swing_high','_of_current_swing_low','_of_previous_swing_low'
            ]
            for column in columns_to_initialize:
                dataframe[f'high{column}'] = dataframe['high']
                dataframe[f'low{column}'] = dataframe['low']
                dataframe[f'close{column}'] = dataframe['close']
            dataframe['swing_date'] = dataframe['date']

        for i in range(1, len(dataframe)):
            if dataframe['looking_for'].iloc[i - 1] == 'high':
                for col in ['high_of_current_low', 'low_of_current_low', 'close_of_current_low', 
                            'high_of_previous_low', 'low_of_previous_low', 'close_of_previous_low']:
                    dataframe.at[i, col] = dataframe[col].iloc[i - 1]

                if dataframe['close'].iloc[i] < dataframe['low_of_potential'].iloc[i - 1]:
                    for col in ['high', 'low', 'close']:
                        dataframe.at[i, f'{col}_of_current_high'] = dataframe[f'{col}_of_potential'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_potential'] = dataframe[col].iloc[i]
                        dataframe.at[i, f'{col}_of_previous_high'] = dataframe[f'{col}_of_current_high'].iloc[i - 1]
                    dataframe.at[i, 'looking_for'] = 'low'
                    if dataframe['close_of_potential'].iloc[i - 1] > dataframe['high_of_current_swing_high'].iloc[i - 1]:
                        for col in ['high', 'low', 'close']:
                            dataframe.at[i, f'{col}_of_previous_swing_high'] = dataframe[f'{col}_of_current_swing_high'].iloc[i - 1]
                            dataframe.at[i, f'{col}_of_current_swing_high'] = dataframe[f'{col}_of_potential'].iloc[i - 1]
                        range_of_current_wave = dataframe.loc[dataframe['swing_date'] == dataframe['swing_date'].iloc[i - 1]]
                        lowest_current_low = range_of_current_wave['low_of_current_low'].min()
                        dataframe.at[i, 'low_of_current_swing_low'] = lowest_current_low
                        if not range_of_current_wave.loc[range_of_current_wave['low_of_current_low'] == lowest_current_low].empty:
                            for col in ['high', 'low', 'close']:
                                dataframe.at[i, f'{col}_of_current_swing_low'] = range_of_current_wave.loc[
                                    range_of_current_wave['low_of_current_low'] == lowest_current_low][f'{col}_of_current_low'].values[0]
                        for col in ['high', 'low', 'close']:
                            dataframe.at[i, f'{col}_of_previous_swing_low'] = dataframe[f'{col}_of_current_swing_low'].iloc[i - 1]
                        dataframe.at[i, 'swing_date'] = dataframe['date'].iloc[i]
                    else:
                        for col in ['high', 'low', 'close']:
                            dataframe.at[i, f'{col}_of_current_swing_high'] = dataframe[f'{col}_of_current_swing_high'].iloc[i - 1]
                            dataframe.at[i, f'{col}_of_previous_swing_high'] = dataframe[f'{col}_of_previous_swing_high'].iloc[i - 1]
                            dataframe.at[i, f'{col}_of_current_swing_low'] = dataframe[f'{col}_of_current_swing_low'].iloc[i - 1]
                            dataframe.at[i, f'{col}_of_previous_swing_low'] = dataframe[f'{col}_of_previous_swing_low'].iloc[i - 1]
                        dataframe.at[i, 'swing_date'] = dataframe['swing_date'].iloc[i - 1]
                elif dataframe['high'].iloc[i] > dataframe['high_of_potential'].iloc[i - 1]:
                    for col in ['high', 'low', 'close']:
                        dataframe.at[i, f'{col}_of_potential'] = dataframe[col].iloc[i]
                    for col in ['high', 'low', 'close']:
                        dataframe.at[i, f'{col}_of_current_high'] = dataframe[f'{col}_of_current_high'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_high'] = dataframe[f'{col}_of_previous_high'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_current_swing_high'] = dataframe[f'{col}_of_current_swing_high'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_swing_high'] = dataframe[f'{col}_of_previous_swing_high'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_current_swing_low'] = dataframe[f'{col}_of_current_swing_low'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_swing_low'] = dataframe[f'{col}_of_previous_swing_low'].iloc[i - 1]
                        dataframe.at[i, 'swing_date'] = dataframe['swing_date'].iloc[i - 1]
                    dataframe.at[i, 'looking_for'] = 'high'
                else:
                    for col in ['high', 'low', 'close']:
                        dataframe.at[i, f'{col}_of_current_high'] = dataframe[f'{col}_of_current_high'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_potential'] = dataframe[f'{col}_of_potential'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_high'] = dataframe[f'{col}_of_previous_high'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_current_swing_high'] = dataframe[f'{col}_of_current_swing_high'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_swing_high'] = dataframe[f'{col}_of_previous_swing_high'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_current_swing_low'] = dataframe[f'{col}_of_current_swing_low'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_swing_low'] = dataframe[f'{col}_of_previous_swing_low'].iloc[i - 1]
                        dataframe.at[i, 'swing_date'] = dataframe['swing_date'].iloc[i - 1]
                    dataframe.at[i, 'looking_for'] = 'high'
            else:
                for col in ['high_of_current_high', 'low_of_current_high', 'close_of_current_high',
                            'high_of_previous_high', 'low_of_previous_high', 'close_of_previous_high']:
                    dataframe.at[i, col] = dataframe[col].iloc[i - 1]

                if dataframe['close'].iloc[i] > dataframe['high_of_potential'].iloc[i - 1]:
                    for col in ['high', 'low', 'close']:
                        dataframe.at[i, f'{col}_of_current_low'] = dataframe[f'{col}_of_potential'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_potential'] = dataframe[col].iloc[i]
                        dataframe.at[i, f'{col}_of_previous_low'] = dataframe[f'{col}_of_current_low'].iloc[i - 1]
                    dataframe.at[i, 'looking_for'] = 'high'
                    if dataframe['close_of_potential'].iloc[i - 1] < dataframe['low_of_current_swing_low'].iloc[i - 1]:
                        for col in ['high', 'low', 'close']:
                            dataframe.at[i, f'{col}_of_previous_swing_low'] = dataframe[f'{col}_of_current_swing_low'].iloc[i - 1]
                            dataframe.at[i, f'{col}_of_current_swing_low'] = dataframe[f'{col}_of_potential'].iloc[i - 1]
                        range_of_current_wave = dataframe.loc[dataframe['swing_date'] == dataframe['swing_date'].iloc[i - 1]]
                        highest_current_high = range_of_current_wave['high_of_current_high'].max()
                        dataframe.at[i, 'high_of_current_swing_high'] = highest_current_high
                        if not range_of_current_wave.loc[range_of_current_wave['high_of_current_high'] == highest_current_high].empty:
                            for col in ['high', 'low', 'close']:
                                dataframe.at[i, f'{col}_of_current_swing_high'] = range_of_current_wave.loc[
                                    range_of_current_wave['high_of_current_high'] == highest_current_high][f'{col}_of_current_high'].values[0]
                        for col in ['high', 'low', 'close']:
                            dataframe.at[i, f'{col}_of_previous_swing_high'] = dataframe[f'{col}_of_current_swing_high'].iloc[i - 1]
                        dataframe.at[i, 'swing_date'] = dataframe['date'].iloc[i]
                    else:
                        for col in ['high', 'low', 'close']:
                            dataframe.at[i, f'{col}_of_current_swing_high'] = dataframe[f'{col}_of_current_swing_high'].iloc[i - 1]
                            dataframe.at[i, f'{col}_of_previous_swing_high'] = dataframe[f'{col}_of_previous_swing_high'].iloc[i - 1]
                            dataframe.at[i, f'{col}_of_current_swing_low'] = dataframe[f'{col}_of_current_swing_low'].iloc[i - 1]
                            dataframe.at[i, f'{col}_of_previous_swing_low'] = dataframe[f'{col}_of_previous_swing_low'].iloc[i - 1]
                        dataframe.at[i, 'swing_date'] = dataframe['swing_date'].iloc[i - 1]
                elif dataframe['low'].iloc[i] < dataframe['low_of_potential'].iloc[i - 1]:
                    for col in ['high', 'low', 'close']:
                        dataframe.at[i, f'{col}_of_potential'] = dataframe[col].iloc[i]
                    for col in ['high', 'low', 'close']:
                        dataframe.at[i, f'{col}_of_current_low'] = dataframe[f'{col}_of_current_low'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_low'] = dataframe[f'{col}_of_previous_low'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_current_swing_high'] = dataframe[f'{col}_of_current_swing_high'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_swing_high'] = dataframe[f'{col}_of_previous_swing_high'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_current_swing_low'] = dataframe[f'{col}_of_current_swing_low'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_swing_low'] = dataframe[f'{col}_of_previous_swing_low'].iloc[i - 1]
                        dataframe.at[i, 'swing_date'] = dataframe['swing_date'].iloc[i - 1]
                    dataframe.at[i, 'looking_for'] = 'low'
                else:
                    for col in ['high', 'low', 'close']:
                        dataframe.at[i, f'{col}_of_current_low'] = dataframe[f'{col}_of_current_low'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_potential'] = dataframe[f'{col}_of_potential'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_low'] = dataframe[f'{col}_of_previous_low'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_current_swing_high'] = dataframe[f'{col}_of_current_swing_high'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_swing_high'] = dataframe[f'{col}_of_previous_swing_high'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_current_swing_low'] = dataframe[f'{col}_of_current_swing_low'].iloc[i - 1]
                        dataframe.at[i, f'{col}_of_previous_swing_low'] = dataframe[f'{col}_of_previous_swing_low'].iloc[i - 1]
                        dataframe.at[i, 'swing_date'] = dataframe['swing_date'].iloc[i - 1]
                    dataframe.at[i, 'looking_for'] = 'low'
        
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['close_of_current_high'] > dataframe['high_of_previous_high'] * self.long_multiplier.value) 
                &(dataframe['close_of_current_low'] > dataframe['low_of_previous_low']) 
            ),
            'enter_long'] = 1

        dataframe.loc[
            (
                (dataframe['close_of_current_low'] < dataframe['low_of_previous_low'] * self.short_multiplier.value) 
                &(dataframe['close_of_current_high'] < dataframe['high_of_previous_high']) 
            ),
            'enter_short'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe['close'] > dataframe['high_of_current_high']),
            'exit_long'] = 1

        dataframe.loc[
            (dataframe['close'] < dataframe['low_of_current_low']),
            'exit_short'] = 1

        return dataframe
            
    
    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, entry_tag: Optional[str],
                 side: str, **kwargs) -> float:
                 
        entry_tag = ''
        max_leverage = self.xlevrage.value

        return max_leverage
