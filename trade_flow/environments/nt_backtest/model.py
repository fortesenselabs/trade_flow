import datetime
from functools import partial
from typing import List, Optional, Tuple

import pandas as pd

from nautilus_trader.core.data import Data
from nautilus_trader.common.actor import Actor, ActorConfig

from nautilus_trader.model.data import DataType
from nautilus_trader.model.data import Bar, BarSpecification
from nautilus_trader.model.identifiers import InstrumentId

from nautilus_trader.common.enums import LogColor
from nautilus_trader.core.data import Data
from nautilus_trader.core.datetime import secs_to_nanos, unix_nanos_to_dt

from sklearn.metrics import r2_score
from sklearn.linear_model import LinearRegression

from trade_flow.environments.nt_backtest.utils import bars_to_dataframe, make_bar_type

# from nautilus_trader.persistence.catalog import ParquetDataCatalog as DataCatalog


class ModelUpdate(Data):
    def __init__(
        self,
        model: LinearRegression,
        hedge_ratio: float,
        std_prediction: float,
        ts_init: int,
    ):
        super().__init__(ts_init=ts_init, ts_event=ts_init)
        self.model = model
        self.hedge_ratio = hedge_ratio
        self.std_prediction = std_prediction


class Prediction(Data):
    def __init__(
        self,
        instrument_id: str,
        prediction: float,
        ts_init: int,
    ):
        super().__init__(ts_init=ts_init, ts_event=ts_init)
        self.instrument_id = instrument_id
        self.prediction = prediction


#
# The model Interface here would be the Agent Interface instead of LinearRegression
#
class DRLAgentConfig(ActorConfig):
    source_symbol: str
    target_symbol: str
    bar_spec: str = "10-SECOND-LAST"
    min_model_timedelta: str = "1D"


class DRLAgent(Actor):
    def __init__(self, config: DRLAgentConfig):
        super().__init__(config=config)

        self.source_id = InstrumentId.from_str(config.source_symbol)
        self.target_id = InstrumentId.from_str(config.target_symbol)
        self.bar_spec = BarSpecification.from_str(self.config.bar_spec)
        self.model: Optional[LinearRegression] = None
        self.hedge_ratio: Optional[float] = None
        self._min_model_timedelta = secs_to_nanos(
            pd.Timedelta(self.config.min_model_timedelta).total_seconds()
        )
        self._last_model = pd.Timestamp(0)

    def on_start(self):
        # Set instruments
        self.left = self.cache.instrument(self.source_id)
        self.right = self.cache.instrument(self.target_id)

        # Subscribe to bars
        self.subscribe_bars(make_bar_type(instrument_id=self.source_id, bar_spec=self.bar_spec))
        self.subscribe_bars(make_bar_type(instrument_id=self.target_id, bar_spec=self.bar_spec))

    def on_bar(self, bar: Bar):
        self._check_model_fit(bar)
        self._predict(bar)

    @property
    def data_length_valid(self) -> bool:
        return self._check_first_tick(self.source_id) and self._check_first_tick(self.target_id)

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
            source_id=self.source_id.value,
            source_bars=self.cache.bars(
                bar_type=make_bar_type(self.source_id, bar_spec=self.bar_spec)
            ),
            target_id=self.target_id.value,
            target_bars=self.cache.bars(
                bar_type=make_bar_type(self.target_id, bar_spec=self.bar_spec)
            ),
        )

        # Format the arrays for scikit-learn
        X = df.loc[:, self.source_id.value].astype(float).values.reshape(-1, 1)
        Y = df.loc[:, self.target_id.value].astype(float).values.reshape(-1, 1)

        # Fit a model
        self.model = LinearRegression(fit_intercept=False)
        self.model.fit(X, Y)
        self.log.info(
            f"Fit model @ {unix_nanos_to_dt(bar.ts_init)}, r2: {r2_score(Y, self.model.predict(X))}",
            color=LogColor.BLUE,
        )
        self._last_model = unix_nanos_to_dt(bar.ts_init)

        # Record std dev of predictions (used for scaling our order price)
        pred = self.model.predict(X)
        errors = pred - Y
        std_pred = errors.std()

        # The model slope is our hedge ratio (the ratio of source
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
            data_type=DataType(ModelUpdate, metadata={"instrument_id": self.target_id.value}),
            data=model_update,
        )

    def _predict(self, bar: Bar):
        if self.model is not None and bar.bar_type.instrument_id == self.source_id:
            pred = self.model.predict([[bar.close]])[0][0]
            prediction = Prediction(
                instrument_id=self.target_id, prediction=pred, ts_init=bar.ts_init
            )
            self.publish_data(
                data_type=DataType(Prediction, metadata={"instrument_id": self.target_id.value}),
                data=prediction,
            )
