from abc import abstractmethod

from trade_flow.core.component import Component
from trade_flow.core.base import TimeIndexed


class RewardScheme(Component, TimeIndexed):
    """A component to compute the reward at each step of an episode."""

    registered_name = "rewards"

    @abstractmethod
    def reward(self, env: "TradingEnvironment") -> float:
        """Computes the reward for the current step of an episode.

        Parameters
        ----------
        env : `TradingEnv`
            The trading environment

        Returns
        -------
        float
            The computed reward.
        """
        raise NotImplementedError()

    def reset(self) -> None:
        """Resets the reward scheme."""
        pass
