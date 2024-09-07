import uuid
import logging

from typing import Dict, Any, Optional, Tuple
from random import randint

import gymnasium
import numpy as np

from trade_flow.core import TimeIndexed, Clock, AssetClass, AgentId, Component
from trade_flow.environments.generic import (
    ActionScheme,
    RewardScheme,
    Observer,
    Stopper,
    Informer,
    Renderer,
)


class TradingEnvironment(gymnasium.Env, TimeIndexed):
    """A trading environment made for use with Gym-compatible reinforcement
    learning algorithms.

    Parameters
    ----------
    action_scheme : `ActionScheme`
        A component for generating an action to perform at each step of the
        environment.
    reward_scheme : `RewardScheme`
        A component for computing reward after each step of the environment.
    observer : `Observer`
        A component for generating observations after each step of the
        environment.
    informer : `Informer`
        A component for providing information after each step of the
        environment.
    renderer : `Renderer`
        A component for rendering the environment.
    kwargs : keyword arguments
        Additional keyword arguments needed to create the environment.
    """

    agent_id: Optional[AgentId] = None
    episode_id: str = None

    def __init__(
        self,
        asset_class: AssetClass,
        action_scheme: ActionScheme,
        reward_scheme: RewardScheme,
        observer: Observer,
        stopper: Stopper,
        informer: Informer,
        renderer: Renderer,
        min_periods: int = None,
        max_episode_steps: int = None,
        random_start_pct: float = 0.00,
        **kwargs,
    ) -> None:
        super().__init__()
        self.clock = Clock()
        self.asset_class = asset_class

        self.action_scheme = action_scheme
        self.reward_scheme = reward_scheme
        self.observer = observer
        self.stopper = stopper
        self.informer = informer
        self.renderer = renderer
        self.min_periods = min_periods
        self.random_start_pct = random_start_pct

        for c in self.components.values():
            c.clock = self.clock

        self.action_space = action_scheme.action_space
        self.observation_space = observer.observation_space

        self._enable_logger = kwargs.get("enable_logger", False)
        if self._enable_logger:
            self.logger = logging.getLogger(kwargs.get("logger_name", __name__))
            self.logger.setLevel(kwargs.get("log_level", logging.DEBUG))

    @property
    def components(self) -> "Dict[str, Component]":
        """The components of the environment. (`Dict[str,Component]`, read-only)"""
        return {
            "action_scheme": self.action_scheme,
            "reward_scheme": self.reward_scheme,
            "observer": self.observer,
            "stopper": self.stopper,
            "informer": self.informer,
            "renderer": self.renderer,
        }

    def step(self, action: Any) -> "Tuple[np.array, float, bool, dict]":
        """Makes one step through the environment.

        Parameters
        ----------
        action : Any
            An action to perform on the environment.

        Returns
        -------
        `np.array`
            The observation of the environment after the action being
            performed.
        float
            The computed reward for performing the action.
        bool
            Whether or not the episode is complete.
        dict
            The information gathered after completing the step.
        """
        self.action_scheme.perform(self, action)

        obs = self.observer.observe(self)
        reward = self.reward_scheme.reward(self)
        terminated = self.stopper.stop(self)
        truncated = False
        info = self.informer.info(self)

        self.clock.increment()

        return obs, reward, terminated, truncated, info

    def reset(self, seed=None, options=None) -> tuple["np.array", dict[str, Any]]:
        """Resets the environment.

        Returns
        -------
        obs : `np.array`
            The first observation of the environment.
        """
        if self.random_start_pct > 0.00:
            size = len(self.observer.feed.process[-1].inputs[0].iterable)
            random_start = randint(0, int(size * self.random_start_pct))
        else:
            random_start = 0

        self.episode_id = str(uuid.uuid4())
        self.clock.reset()

        for c in self.components.values():
            if hasattr(c, "reset"):
                if isinstance(c, Observer):
                    c.reset(random_start=random_start)
                else:
                    c.reset()

        obs = self.observer.observe(self)
        info = self.informer.info(self)

        self.clock.increment()

        return obs, info

    def render(self, **kwargs) -> None:
        """Renders the environment."""
        self.renderer.render(self, **kwargs)

    def save(self) -> None:
        """Saves the rendered view of the environment."""
        self.renderer.save()

    def close(self) -> None:
        """Closes the environment."""
        self.renderer.close()
