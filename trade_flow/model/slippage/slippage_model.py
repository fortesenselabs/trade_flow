from abc import abstractmethod

from trade_flow.core import Component
from trade_flow.model.orders import Trade


class SlippageModel(Component):
    """A model for simulating slippage on an exchange trade."""

    registered_name = "slippage"

    def __init__(self):
        pass

    @abstractmethod
    def adjust_trade(self, trade: Trade, **kwargs) -> Trade:
        """Simulate slippage on a trade ordered on a specific exchange.

        Parameters
        ----------
        trade : `Trade`
            The trade executed on the exchange.
        **kwargs : keyword arguments
            Any other arguments necessary for the model.

        Returns
        -------
        `Trade`
            A filled trade with the `price` and `size` adjusted for slippage.
        """
        raise NotImplementedError()
