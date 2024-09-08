import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from tensortrade.env.generic import Renderer
from tensortrade.env.generic import TradingEnv

class PositionChangeChart(Renderer):

    def __init__(self, ax1, ax2):
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

        for i in range(len(actions) - 1):
            a1 = actions[i]
            a2 = actions[i + 1]

            if a1 != a2:
                if a1 == 0 and a2 == 1:
                    buy[i] = p[i]
                else:
                    sell[i] = p[i]

        buy = pd.Series(buy, dtype='object')
        sell = pd.Series(sell, dtype='object')

        self.ax1.plot(np.arange(len(p)), p, label="price", color="orange")
        self.ax1.scatter(buy.index, buy.values, marker="^", color="green")
        self.ax1.scatter(sell.index, sell.values, marker="^", color="red")
        self.ax1.set_title("Trading Chart")

        performance_df = pd.DataFrame().from_dict(env.action_scheme.portfolio.performance, orient='index')
        performance_df.plot(ax=self.ax2)
        self.ax2.set_title("Net Worth")

    def close(self, _):
        plt.close()
