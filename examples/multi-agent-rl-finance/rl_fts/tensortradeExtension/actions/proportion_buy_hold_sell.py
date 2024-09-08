from tensortrade.env.default.actions import TensorTradeActionScheme
from gym.spaces import Discrete, Tuple, Box
from tensortrade.oms.wallets import Wallet, Portfolio
from tensortrade.oms.instruments import ExchangePair, TradingPair

from tensortrade.oms.orders import (
    Order,
    proportion_order,
)

class PBSH(TensorTradeActionScheme):
    """
        An action scheme which has both continuos and discrete outputs.
        The options are to buy, sell, or hold.

    Parameters
    ----------
    cash : `Wallet`
        The wallet to hold funds in the base intrument.
    asset : `Wallet`
        The wallet to hold funds in the quote instrument.
    """

    registered_name = "pbsh"

    def __init__(self, cash: 'Wallet', asset: 'Wallet'):
        super().__init__()
        self.cash = cash
        self.asset = asset
        # USD-TTC
        traing_pair = TradingPair(self.cash.balance.instrument, self.asset.balance.instrument)
        # sine-wave-USD-TTC
        self.exchange_pair = ExchangePair(self.cash.exchange, traing_pair)

        self.listeners = []
        self.action = -1
        self.proportion = -1
        self.proportion_steps = 10

    @property
    def action_space(self):
        """
          (0, x) -> Convert x% of cash to asset
          (1, y) -> Convert y% of asset to cash
          Note:
            1. If the action is the same as the previous action, we implement a hold
            2. we do nothing until the agent requests a buy
        """
        return Tuple((Discrete(2), Discrete(self.proportion_steps)))

    def attach(self, listener):
        self.listeners += [listener]
        return self

    def get_orders(self, actions: Tuple, portfolio: 'Portfolio') -> 'Order':
        action, proportion = actions 
        order = None

        if abs(action - self.action) > 0:
            if action == 0:
                src = self.cash
                tgt = self.asset
            else:
                src = self.asset
                tgt = self.cash

            if src.balance == 0:  # We need to check, regardless of the proposed order, if we have balance in 'src'
                return []  # Otherwise just return an empty order list

            if not proportion == 0:
                proportion = proportion / self.proportion_steps

                if proportion < 0.0:
                    print("error")
                if proportion > 1.0:
                    print("error")
            
                order = proportion_order(portfolio, src, tgt, proportion)
                self.action = action
                self.proportion = proportion

        for listener in self.listeners:
            listener.on_action(actions)

        return [order]

    def reset(self):
        super().reset()
        self.action = -1
