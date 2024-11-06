import numpy as np

from trade_flow.environments.metatrader.engine.orders import Trade, TradeType, TradeSide
from trade_flow.environments.metatrader.engine.spread.spread_model import SpreadModel


class RandomUniformSpreadModel(SpreadModel):
    """A uniform random spread model.

    Parameters
    ----------
    max_spread_percent : float, default 3.0
        The maximum random spread to be applied to the fill price.
    """

    def __init__(self, max_spread_percent: float = 3.0):
        super().__init__()
        self.max_spread_percent = self.default("max_spread_percent", max_spread_percent)

    def adjust_trade(self, trade: "Trade", **kwargs) -> "Trade":
        price_spread = np.random.uniform(0, self.max_spread_percent / 100)

        initial_price = trade.price

        if trade.type == TradeType.MARKET:
            if trade.side == TradeSide.BUY:
                trade.price = max(initial_price * (1 + price_spread), 1e-3)
            else:
                trade.price = max(initial_price * (1 - price_spread), 1e-3)
        else:
            if trade.side == TradeSide.BUY:
                trade.price = max(initial_price * (1 + price_spread), 1e-3)

                if trade.price > initial_price:
                    trade.size *= min(initial_price / trade.price, 1)
            else:
                trade.price = max(initial_price * (1 - price_spread), 1e-3)

                if trade.price < initial_price:
                    trade.size *= min(trade.price / initial_price, 1)

        return trade
