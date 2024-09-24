from abc import abstractmethod, ABCMeta
from typing import Any

from gymnasium.spaces import Space

from trade_flow.core.component import Component
from trade_flow.core import TimeIndexed


class ActionScheme(Component, TimeIndexed, metaclass=ABCMeta):
    """A component for determining the action to take at each step of an
    episode.
    """

    registered_name = "actions"

    @property
    @abstractmethod
    def action_space(self) -> Space:
        """The action space of the `TradingEnv`. (`Space`, read-only)"""
        raise NotImplementedError()

    @abstractmethod
    def perform(self, env: "TradingEnvironment", action: Any) -> None:
        """Performs an action on the environment.

        Parameters
        ----------
        env : `TradingEnv`
            The trading environment to perform the `action` on.
        action : Any
            The action to perform on `env`.
        """
        raise NotImplementedError()

    def reset(self) -> None:
        """Resets the action scheme."""
        pass
