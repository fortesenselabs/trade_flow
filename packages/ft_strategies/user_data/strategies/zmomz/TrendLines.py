# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IStrategy, IntParameter)

# --------------------------------
# Add your lib to import here
from datetime import datetime
from typing import Optional
import pandas_ta
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib



class TrendLines5x10(IStrategy):

    INTERFACE_VERSION = 3
    can_short= True

    # roi take profit and stop loss points
    minimal_roi = {"0": 0.99}
    stoploss = -1
    use_custom_stoploss = False
    trailing_stop = False
    use_exit_signal = True
    exit_profit_only = False
    exit_profit_offset = 0.0
    ignore_roi_if_entry_signal = False
    timeframe = '1h'

    # Strategy Parameters
    ATR_Period = 11
    LBL = 10
    LBR = 10
    slope = 17.6
    average_price_period = 20
    trend_confirmation_period = 50
    xlevrage = 10

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    # Optional order type mapping.
    order_types = {
        'entry': 'market',
        'exit': 'market',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    def checkhl(self, data_back, data_forward, hl):

        if hl == 'high' or hl == 'High':
            ref = data_back[len(data_back)-1]
            for i in range(len(data_back)-1):
                if ref < data_back[i]:
                    return 0
            for i in range(len(data_forward)):
                if ref <= data_forward[i]:
                    return 0
            return 1
        if hl == 'low' or hl == 'Low':
            ref = data_back[len(data_back)-1]
            for i in range(len(data_back)-1):
                if ref > data_back[i]:
                    return 0
            for i in range(len(data_forward)):
                if ref >= data_forward[i]:
                    return 0
            return 1


    def pivot(self, osc, atr, LBL, LBR, highlow):
        breakouts = pd.Series(dtype='float64')
        pivpoint = 0
        atrpoint = 0
        counter=0
        pivots=[]
        atrs=[]
        count_list=[]
        left = []
        right = []
        for i in range(len(osc)):
            pivots.append(pivpoint)
            atrs.append(atrpoint)
            count_list.append(counter)
            counter +=1
            if i < LBL + 1:
                left.append(osc[i])
            if i > LBL:
                right.append(osc[i])
            if i > LBL + LBR:
                left.append(right[0])
                left.pop(0)
                right.pop(0)
                if self.checkhl(left, right, highlow):
                    pivots[i - LBR] = osc[i - LBR]
                    pivpoint = osc[i - LBR]
                    atrpoint = atr[i - LBR]
                    counter = 0
        slops =list(map(lambda x: x/self.slope,atrs))
        if highlow.lower() == 'low':
            breakouts = pd.Series(pivots) + (pd.Series(count_list)*pd.Series(slops))
        elif highlow.lower() == 'high':
            breakouts = pd.Series(pivots) - (pd.Series(count_list)*pd.Series(slops))
            
        return breakouts, pd.Series(pivots)


    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        # average True range for stoploss extention
        dataframe['ATR'] = pandas_ta.atr(dataframe['high'],dataframe['low'],dataframe['close'],length= self.ATR_Period)

        # main indicators for long and short breakout enteries, and exiting targets 
        # all are based on pivot points
        dataframe['short_breakout'], dataframe['long_target'] = self.pivot(osc=dataframe["high"], atr=dataframe['ATR'], 
                                                                           LBL=self.LBL,LBR=self.LBR,highlow="high")
        dataframe['long_breakout'], dataframe['short_target'] = self.pivot(osc=dataframe["low"], atr=dataframe['ATR'], 
                                                                           LBL=self.LBL,LBR=self.LBR,highlow="low")

        # moving average for trend confirmation
        dataframe['Trend_confirmation'] = ta.SMA(dataframe, timeperiod=self.trend_confirmation_period)
        
        # distance between current (average) price and targets, used for filtering 
        # low profit trades 
        dataframe['average_price'] = ta.SMA(dataframe, timeperiod=self.average_price_period)
        dataframe['dist_resistance'] = dataframe['long_target']-dataframe['average_price']
        dataframe['dist_support'] = dataframe['average_price']-dataframe['short_target']

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                # long position conditions:

                # main condition, candle crosses and closes above the long breakout line
                (qtpylib.crossed_above(dataframe['close'], dataframe['long_breakout']))

                # the whole candle body must be above the moving average for confirming up trend 
                & (dataframe['open'] > dataframe['Trend_confirmation'])

                # the candle must be green 
                & (dataframe['close'] > dataframe['open'])

                # current price must be closer to the resistance
                & (dataframe['dist_resistance'] < dataframe['dist_support'])
            ),
            'enter_long'] = 1

        dataframe.loc[
            (
                # short position conditions:
                
                # main condition, candle crosses and closes bellow the short breakout line
                (qtpylib.crossed_below(dataframe['close'], dataframe['short_breakout']))
                
                # the whole candle body must be bellow the moving average for confirming up trend 
                & (dataframe['open'] < dataframe['Trend_confirmation'])
                
                # the candle must be red 
                & (dataframe['close'] < dataframe['open'])
                
                # current price must be closer to the support
                & (dataframe['dist_resistance'] > dataframe['dist_support'])
            ),
            'enter_short'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                # exit with profit at long target
                (dataframe['close'] >= dataframe['long_target']) 
                # dynamic stoploss
                | (dataframe['close'] <= dataframe['short_target']-dataframe['ATR'])
            ),

            'exit_long'] = 1

        dataframe.loc[
            (
                # exit with profit at short target
                (dataframe['close'] <= dataframe['short_target']) 
                # dynamic stoploss
                | (dataframe['close'] >= dataframe['long_target']+dataframe['ATR']) 
            ),
            'exit_short'] = 1

        return dataframe

    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, entry_tag: Optional[str],
                 side: str, **kwargs) -> float:
                 
        entry_tag = ''
        max_leverage = self.xlevrage

        return max_leverage