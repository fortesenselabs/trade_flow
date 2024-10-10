import datetime
from functools import partial
from typing import List, Optional, Tuple

import pandas as pd

from nautilus_trader.core.data import Data
from nautilus_trader.common.actor import Actor, ActorConfig

from nautilus_trader.model.data import DataType, Bar, BarSpecification
from nautilus_trader.model.identifiers import InstrumentId

from nautilus_trader.common.enums import LogColor
from nautilus_trader.core.data import Data
from nautilus_trader.core.datetime import secs_to_nanos, unix_nanos_to_dt

from trade_flow.agents.base import Agent
from trade_flow.agents.sb3_agent import SB3Agent
from packages.nt_backtest.models import Action, ModelUpdate
from packages.nt_backtest.utils import bars_to_dataframe, make_bar_type
from trade_flow.environments.utils import create_env_from_dataframe


class DRLAgentConfig(ActorConfig):
    symbol: str
    train_n_episodes: int = 2
    train_n_steps: int = 600
    bar_spec: str = "10-SECOND-LAST"
    min_model_timedelta: str = "1D"


class DRLAgent(Actor):
    def __init__(self, config: DRLAgentConfig):
        super().__init__(config=config)

        self.instrument_id = InstrumentId.from_str(config.symbol)
        self.bar_spec = BarSpecification.from_str(self.config.bar_spec)
        self.n_episodes: int = self.config.train_n_episodes
        self.n_steps: int = self.config.train_n_steps
        self.model: Optional[SB3Agent] = None  # self.config.agent
        self.hedge_ratio: Optional[float] = None
        self._min_model_timedelta = secs_to_nanos(
            pd.Timedelta(self.config.min_model_timedelta).total_seconds()
        )
        self._last_model = pd.Timestamp(0)

    def on_start(self):
        # Set instruments
        self.instrument_cache = self.cache.instrument(self.instrument_id)

        # Subscribe to bars
        self.subscribe_bars(make_bar_type(instrument_id=self.instrument_id, bar_spec=self.bar_spec))

    def on_bar(self, bar: Bar):
        self._check_model_fit(bar)
        self._predict(bar)

    @property
    def data_length_valid(self) -> bool:
        return self._check_first_tick(self.instrument_id)

    @property
    def has_fit_model_today(self):
        return unix_nanos_to_dt(self.clock.timestamp_ns()).date() == self._last_model.date()

    def _check_first_tick(self, instrument_id) -> bool:
        """Check we have enough bar data for this `instrument_id`, according to `min_model_timedelta`"""
        bars = self.cache.bars(bar_type=make_bar_type(instrument_id, bar_spec=self.bar_spec))
        if not bars:
            return False
        delta = self.clock.timestamp_ns() - bars[-1].ts_init
        return delta > self._min_model_timedelta

    def _check_model_fit(self, bar: Bar):
        # Check we have the minimum required data
        if not self.data_length_valid:
            return

        # Check we haven't fit a model yet today
        if self.has_fit_model_today:
            return

        # Generate a dataframe from cached bar data
        df = bars_to_dataframe(
            instrument_id=self.instrument_id.value,
            instrument_bars=self.cache.bars(
                bar_type=make_bar_type(self.instrument_id, bar_spec=self.bar_spec)
            ),
        )

        # Fit a model
        env = create_env_from_dataframe(dataset=df)
        self.model = SB3Agent(env)
        self.model.get_model("dqn", {"policy": "MlpPolicy"})
        self.model.train(
            n_episodes=self.n_episodes,
            n_steps=self.n_steps,
            progress_bar=True,
        )
        performance = pd.DataFrame.from_dict(
            env.action_scheme.portfolio.performance, orient="index"
        )
        print(performance)
        self.log.info(
            f"Fit model @ {unix_nanos_to_dt(bar.ts_init)}, performance: {performance}",
            color=LogColor.BLUE,
        )
        self._last_model = unix_nanos_to_dt(bar.ts_init)

        # Record std dev of predictions (used for scaling our order price)
        pred = self.model.predict(state)  # TODO: a utility function to create state
        errors = pred - Y
        std_pred = errors.std()

        # The model slope is our hedge ratio (the ratio of
        self.hedge_ratio = float(self.model.coef_[0][0])
        self.log.info(f"Computed hedge_ratio={self.hedge_ratio:0.4f}", color=LogColor.BLUE)

        # Publish model
        model_update = ModelUpdate(
            model=self.model,
            hedge_ratio=self.hedge_ratio,
            std_prediction=std_pred,
            ts_init=bar.ts_init,
        )
        self.publish_data(
            data_type=DataType(ModelUpdate, metadata={"instrument_id": self.instrument_id.value}),
            data=model_update,
        )

    def _predict(self, bar: Bar):
        if self.model is not None and bar.bar_type.instrument_id == self.instrument_id:
            action, _ = self.model.predict(
                [[bar.close]]
            )  # TODO: a utility function to create state
            action = Action(instrument_id=self.instrument_id, action=action, ts_init=bar.ts_init)
            self.publish_data(
                data_type=DataType(Action, metadata={"instrument_id": self.instrument_id.value}),
                data=action,
            )
