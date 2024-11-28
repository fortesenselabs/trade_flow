from abc import abstractmethod

from trade_flow.core import Component
from trade_flow.environments.default.engine.orders import Trade


class SpreadModel(Component):
    """A model for simulating a broker's spread."""

    registered_name = "spread"

    def __init__(self):
        pass

    @abstractmethod
    def adjust_trade(self, trade: Trade, **kwargs) -> Trade:
        """Simulate spread on a trade ordered on a specific broker.

        Parameters
        ----------
        trade : `Trade`
            The trade executed on the broker.
        **kwargs : keyword arguments
            Any other arguments necessary for the model.

        Returns
        -------
        `Trade`
            A filled trade with the `price` and `size` adjusted for spread.
        """
        raise NotImplementedError()
