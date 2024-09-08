from tensortrade.env.default.actions import TensorTradeActionScheme
from gym.spaces import Discrete
from tensortrade.oms.wallets import Wallet, Portfolio
from tensortrade.oms.instruments import ExchangePair, TradingPair

from tensortrade.oms.orders import (
    Order,
    proportion_order,
)

class BSH(TensorTradeActionScheme):
    """A simple discrete action scheme where the only options are to buy, sell,
    or hold.

    Parameters
    ----------
    cash : `Wallet`
        The wallet to hold funds in the base intrument.
    asset : `Wallet`
        The wallet to hold funds in the quote instrument.
    """

    registered_name = "bsh"

    def __init__(
        self, cash: 'Wallet', 
        asset: 'Wallet',
        **kwargs):
        super().__init__()
        self.cash = cash
        self.asset = asset
        # instrument--instrument
        traing_pair = TradingPair(self.cash.balance.instrument, self.asset.balance.instrument)
        # exchange-instrument-instrument
        self.exchange_pair = ExchangePair(self.cash.exchange, traing_pair)

        self.listeners = []
        self.action = -1

    @property
    def action_space(self):
        """
          0 -> Buy everything
          1 -> Sell everything
          Note:
            If the action is the same as the previous action, we implement a hold
        """
        return Discrete(2)

    def attach(self, listener):
        self.listeners += [listener]
        return self

    def get_orders(self, action: int, portfolio: 'Portfolio') -> 'Order':
        order = None

        if abs(action - self.action) > 0:
            src = self.cash if self.action == 0 else self.asset
            tgt = self.asset if self.action == 0 else self.cash

            if src.balance == 0:  # We need to check, regardless of the proposed order, if we have balance in 'src'
                return []  # Otherwise just return an empty order list

            order = proportion_order(portfolio, src, tgt, 1.0)
            self.action = action

        for listener in self.listeners:
            if hasattr(listener, 'on_action'):
                listener.on_action(action)

        return [order]

    def reset(self):
        super().reset()
        self.action = 0

    # def get_best_actions(self, price_stream):
