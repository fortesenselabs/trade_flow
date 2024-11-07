import random
from typing import Any, Dict, Optional, Tuple
import uuid
from nautilus_trader.backtest.node import BacktestEngineConfig
from nautilus_trader.backtest.engine import BacktestEngine
import numpy as np
from trade_flow.environments.generic.environment import TradingEnvironment
from trade_flow.environments.generic import (
    ActionScheme,
    RewardScheme,
    Observer,
    Stopper,
    Informer,
    Renderer,
)

# TODO: Convert data coming from nautilus to gym's format and vice versa


class NautilusTraderEnv(TradingEnvironment):
    """A trading environment built for use with Gym-compatible reinforcement
    learning algorithms, designed to interface with the NautilusTrader backtesting engine.

    This environment encapsulates a trading simulation, allowing RL agents to interact
    with the NautilusTrader backtesting engine using custom action and reward schemes,
    observation handling, and other optional elements like renderers and informers.

    Parameters
    ----------
    engine_config : BacktestEngineConfig
        Configuration for the NautilusTrader backtesting engine, defining settings
        like trading venues, risk parameters, and data sources.
    action_scheme : ActionScheme
        Component responsible for processing and executing actions in the environment.
    reward_scheme : RewardScheme
        Component for computing rewards after each environment step based on defined
        profit/loss or risk metrics.
    observer : Observer
        Component responsible for generating observations to provide to the agent at
        each step.
    stopper : Stopper
        Component that defines conditions to end an episode, such as a stop-loss or max steps.
    informer : Informer
        Component for providing additional information or metrics after each step.
    renderer : Renderer
        Component responsible for visualizing the trading environment.
    min_periods : int, optional
        Minimum periods (or steps) required to start the episode. Useful for time series data.
    max_episode_steps : int, optional
        Maximum number of steps per episode; can be used to end the episode after a set duration.
    random_start_pct : float, default=0.0
        Percentage for a random starting point in the data; useful for variation in episode start times.
    kwargs : keyword arguments
        Additional arguments to configure the environment further, such as venue settings or
        custom data providers.

    Example
    -------
    >>> env = NautilusTraderEnv(
    ...     engine_config=my_engine_config,
    ...     action_scheme=my_action_scheme,
    ...     reward_scheme=my_reward_scheme,
    ...     observer=my_observer,
    ...     stopper=my_stopper,
    ...     informer=my_informer,
    ...     renderer=my_renderer
    ... )
    >>> state = env.reset()
    >>> done = False
    >>> while not done:
    ...     action = env.action_space.sample()
    ...     state, reward, done, info = env.step(action)
    """

    def __init__(
        self,
        engine_config: BacktestEngineConfig,
        action_scheme: ActionScheme,
        reward_scheme: RewardScheme,
        observer: Observer,
        stopper: Stopper,
        informer: Informer,
        renderer: Renderer,
        min_periods: Optional[int] = None,
        max_episode_steps: Optional[int] = None,
        random_start_pct: float = 0.00,
        **kwargs,
    ):
        super().__init__(
            action_scheme,
            reward_scheme,
            observer,
            stopper,
            informer,
            renderer,
            min_periods,
            max_episode_steps,
            random_start_pct,
            **kwargs,
        )

        # Initialize the backtest engine with the given configuration
        self._create_engine(engine_config, **kwargs)

    def _create_engine(
        self,
        config: BacktestEngineConfig,
        **kwargs,
    ) -> BacktestEngine:
        """Initializes and configures the NautilusTrader backtesting engine.

        Creates the engine, adds venues, and sets up the trader instance
        with the necessary actors and message bus for action execution.

        Parameters
        ----------
        config : BacktestEngineConfig
            Configuration for the NautilusTrader backtest engine.
        kwargs : keyword arguments
            Additional arguments for venue setup or custom actor components.
        """

        self.engine = BacktestEngine(config=config)
        self.engine.add_venue(**kwargs)
        # self.engine.add_actor(**kwargs)

        log_guard = self.engine.kernel.get_log_guard()
        if log_guard:
            self._logger = log_guard

        else:
            # add logger
            pass

        # OR Communication in the engine can be done through an actor take a look at nautilus_talks repo or the nt_example.
        # OR msgbus

        self.trader = self.engine.trader
        self.msgbus = self.trader._msgbus

        return

    def _get_observation(self) -> Dict[str, Any]:
        """Generates an observation for the agent.

        Pulls data from various sources, such as positions, fills, and order history.

        Returns
        -------
        Dict[str, Any]
            The observation data for the current step.
        """

        orders = self.trader.generate_orders_report()
        order_fills = self.trader.generate_order_fills_report()
        fills = self.trader.generate_fills_report()
        positions = self.trader.generate_positions_report()
        # account = self.trader.generate_account_report(venue)

        print(f"Positions: {positions}")
        return

    def _calculate_reward(self) -> float:
        """Calculates the reward based on the current state.

        Uses the defined reward scheme to compute a reward based
        on factors such as profit/loss or custom metrics.

        Returns
        -------
        float
            The computed reward for the current step.
        """
        reward = random.randint(2, 6)
        return reward

    def step(self, action: Any) -> Tuple[np.array, float, bool, bool, dict]:

        print(f"Action: {action}")

        # TODO: Send action to engine
        # TODO: get result of action

        # self.msgbus.publish(action)

        # self.msgbus.publish_data(
        #         data_type=DataType(Prediction, metadata={"instrument_id": self.target_id.value}),
        #         data=prediction,
        #     )

        # self._position_history.append(self._position)

        obs = self._get_observation()
        reward = self._calculate_reward()
        terminated = self.stopper.stop(self)
        truncated = False
        info = self.informer.info(self)
        # self._update_history(info)

        self.clock.increment()

        return obs, reward, terminated, truncated, info

    def reset(self, seed=None, options=None) -> Tuple[np.array, Dict[str, Any]]:
        if self.random_start_pct > 0.00:
            size = len(self.observer.feed.process[-1].inputs[0].iterable)
            random_start = random.randint(0, int(size * self.random_start_pct))
        else:
            random_start = 0

        self.agent_id = self.engine.trader_id
        self.episode_id = str(uuid.uuid4())
        self.engine_id = self.engine.instance_id

        self.engine.reset()
        self.clock.reset()

        for c in self.components.values():
            if hasattr(c, "reset"):
                if isinstance(c, Observer):
                    c.reset(random_start=random_start)
                else:
                    c.reset()

        obs = {}
        info = self.informer.info(self)

        self.clock.increment()

        return obs, info

    def close(self) -> None:
        """Closes the environment."""
        self.renderer.close()
        self.engine.dispose()
