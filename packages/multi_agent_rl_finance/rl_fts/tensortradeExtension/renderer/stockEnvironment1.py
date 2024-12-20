import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from trade_flow.environments.generic import Renderer
from trade_flow.environments.generic import TradingEnv


class Chart(Renderer):

    def __init__(self, ax1, ax2):
        self.ax1 = ax1
        self.ax2 = ax2

    def render(self, env: TradingEnv):
        self.ax1.clear()
        self.ax2.clear()

        history = pd.DataFrame(env.observer.renderer_history)
        actions = list(history.action)
        p = list(history.price)
        f = list(history.fast)
        m = list(history.medium)
        s = list(history.slow)
        lr = list(history.lr)

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

        buy = pd.Series(buy, dtype="object")
        sell = pd.Series(sell, dtype="object")
        # price
        self.ax1.plot(np.arange(len(p)), p, label="price", color="orange")
        # fast
        self.ax1.plot(np.arange(len(f)), f, label="fast", color="blue")
        # medium
        self.ax1.plot(np.arange(len(m)), m, label="medium", color="green")
        # slow
        self.ax1.plot(np.arange(len(s)), s, label="slow", color="purple")
        # lr
        self.ax1.plot(np.arange(len(lr)), lr, label="lr", color="gray")

        # actions
        self.ax1.scatter(buy.index, buy.values, marker="^", color="green")
        self.ax1.scatter(sell.index, sell.values, marker="^", color="red")
        self.ax1.set_title("Trading Chart")

        performance_df = pd.DataFrame().from_dict(
            env.action_scheme.portfolio.performance, orient="index"
        )
        performance_df.plot(ax=self.ax2)
        self.ax2.set_title("Net Worth")

    def close(self):
        plt.close()
