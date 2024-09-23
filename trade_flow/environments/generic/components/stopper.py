from abc import abstractmethod

from trade_flow.core.component import Component
from trade_flow.core import TimeIndexed


class Stopper(Component, TimeIndexed):
    """A component for determining if the environment satisfies a defined
    stopping criteria.
    """

    registered_name = "stopper"

    @abstractmethod
    def stop(self, env: "TradingEnvironment") -> bool:
        """Computes if the environment satisfies the defined stopping criteria.

        Parameters
        ----------
        env : `TradingEnv`
            The trading environment.

        Returns
        -------
        bool
            If the environment should stop or continue.
        """
        raise NotImplementedError()

    def reset(self) -> None:
        """Resets the stopper."""
        pass
