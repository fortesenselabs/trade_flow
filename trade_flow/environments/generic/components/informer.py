from abc import abstractmethod

from trade_flow.core.component import Component
from trade_flow.core.base import TimeIndexed


class Informer(Component, TimeIndexed):
    """A component to provide information at each step of an episode."""

    registered_name = "monitor"

    @abstractmethod
    def info(self, env: "TradingEnvironment") -> dict:
        """Provides information at a given step of an episode.

        Parameters
        ----------
        env: 'TradingEnv'
            The trading environment.

        Returns
        -------
        dict:
            A dictionary of information about the portfolio and net worth.
        """
        raise NotImplementedError()

    def reset(self):
        """Resets the informer."""
        pass
