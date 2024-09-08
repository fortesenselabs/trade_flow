import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from tensortrade.env.generic import Renderer
from tensortrade.env.generic import TradingEnv


class PositionChangeChart(Renderer):

    def __init__(self, fig, ax1, ax2):
        self.fig = fig
        self.ax1 = ax1
        self.ax2 = ax2

    def render(self, env: TradingEnv):
        self.ax1.clear()
        self.ax2.clear()

        history = pd.DataFrame(env.observer.renderer_history)
        actions = list(history.action)
        p = list(history.price)

        buy = {}
        sell = {}
        enter_short = {}
        exit_short = {}

        for i in range(len(actions) - 1):
            previous_action = actions[i]
            current_action = actions[i + 1]

            if current_action != previous_action and current_action != -1:
                # if the position has changed
                if current_action == 0:
                    if previous_action == 2:
                        exit_short[i] = p[i]
                    buy[i] = p[i]
                if current_action == 1:
                    if previous_action == 2:
                        exit_short[i] = p[i]
                    sell[i] = p[i]
                if current_action == 2:
                    if previous_action == 0:
                        sell[i] = p[i]
                    enter_short[i] = p[i]
                elif current_action == 3 and previous_action == 2:
                    exit_short[i] = p[i]

        buy_series = pd.Series(buy, dtype='object')
        sell_series = pd.Series(sell, dtype='object')
        enter_short_series = pd.Series(enter_short, dtype='object')
        exit_short_series = pd.Series(exit_short, dtype='object')

        self.ax1.plot(np.arange(len(p)), p, label="price", color="orange")
        self.ax1.scatter(buy_series.index,
                         buy_series.values, marker="^", color="g")
        self.ax1.scatter(sell_series.index,
                         sell_series.values, marker="^", color="r")
        self.ax1.scatter(enter_short_series.index,
                         enter_short_series.values, marker="^", color="b")
        self.ax1.scatter(exit_short_series.index,
                         exit_short_series.values, marker="^", color="y")
        self.ax1.set_title("Trading Chart")

        performance_df = pd.DataFrame().from_dict(env.reward_scheme.net_worth_history)
        performance_df.plot(ax=self.ax2)
        self.ax2.set_title("Net Worth")

    def close(self, _):
        plt.close()
