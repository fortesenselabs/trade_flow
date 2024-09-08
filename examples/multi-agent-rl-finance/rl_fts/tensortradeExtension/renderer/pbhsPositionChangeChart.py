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
        proportions = list(history.proportion)
        p = list(history.price)

        buy = {}
        buy_proportions = []
        sell = {}
        sell_proportions = []

        for i in range(len(actions) - 1):
            previous_action = actions[i]
            current_action = actions[i + 1]
            current_proportion = proportions[i + 1]

            if current_action != previous_action and current_action != -1:
                if current_action == 0:
                    buy[i] = p[i]
                    buy_proportions.append(current_proportion)
                else:
                    sell[i] = p[i]
                    sell_proportions.append(current_proportion)

        buy = pd.Series(buy, dtype='object')
        sell = pd.Series(sell, dtype='object')
        

        self.ax1.plot(np.arange(len(p)), p, label="price", color="orange")
        if buy.values.size > 0:   
            self.ax1.scatter(buy.index, buy.values, marker="^", color="green")
        # for i, txt in enumerate(n):
        #     plt.annotate(txt, (z[i], y[i]))
        if sell.values.size > 0: 
            self.ax1.scatter(sell.index, sell.values, marker="^", color="red")
        self.ax1.set_title("Trading Chart")

        performance_df = pd.DataFrame().from_dict(env.action_scheme.portfolio.performance, orient='index')
        performance_df.plot(ax=self.ax2)
        self.ax2.set_title("Net Worth")

    def close(self):
        plt.close()
