import numpy as np

from trade_flow.model.slippage.slippage_model import SlippageModel
from trade_flow.model.orders import Trade, TradeType, TradeSide


class RandomUniformSlippageModel(SlippageModel):
    """A uniform random slippage model.

    Parameters
    ----------
    max_slippage_percent : float, default 3.0
        The maximum random slippage to be applied to the fill price.
    """

    def __init__(self, max_slippage_percent: float = 3.0):
        super().__init__()
        self.max_slippage_percent = self.default("max_slippage_percent", max_slippage_percent)

    def adjust_trade(self, trade: "Trade", **kwargs) -> "Trade":
        price_slippage = np.random.uniform(0, self.max_slippage_percent / 100)

        initial_price = trade.price

        if trade.type == TradeType.MARKET:
            if trade.side == TradeSide.BUY:
                trade.price = max(initial_price * (1 + price_slippage), 1e-3)
            else:
                trade.price = max(initial_price * (1 - price_slippage), 1e-3)
        else:
            if trade.side == TradeSide.BUY:
                trade.price = max(initial_price * (1 + price_slippage), 1e-3)

                if trade.price > initial_price:
                    trade.size *= min(initial_price / trade.price, 1)
            else:
                trade.price = max(initial_price * (1 - price_slippage), 1e-3)

                if trade.price < initial_price:
                    trade.size *= min(trade.price / initial_price, 1)

        return trade
