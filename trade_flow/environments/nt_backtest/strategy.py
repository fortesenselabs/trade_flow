import datetime
from functools import partial
from typing import Optional

import pandas as pd
from trade_flow.environments.nt_backtest.model import ModelUpdate, Prediction
from nautilus_trader.common.enums import LogColor
from nautilus_trader.config import StrategyConfig
from nautilus_trader.core.data import Data
from nautilus_trader.core.datetime import unix_nanos_to_dt
from nautilus_trader.core.message import Event
from nautilus_trader.model.data.bar import Bar, BarSpecification
from nautilus_trader.model.data.base import DataType
from nautilus_trader.model.enums import OrderSide, PositionSide, TimeInForce
from nautilus_trader.model.events.position import (
    PositionChanged,
    PositionClosed,
    PositionEvent,
    PositionOpened,
)
from nautilus_trader.model.identifiers import InstrumentId, PositionId
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.model.position import Position
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.functions import order_side_to_str
from trade_flow.environments.nt_backtest.utils import human_readable_duration, make_bar_type


class RepeatedEventComplete(Exception):
    pass


class PairTraderConfig(StrategyConfig):
    source_symbol: str
    target_symbol: str
    notional_trade_size_usd: int = 10_000
    min_model_timedelta: datetime.timedelta = datetime.timedelta(days=1)
    trade_width_std_dev: float = 2.5
    bar_spec: str = "10-SECOND-LAST"
    ib_long_short_margin_requirement = (0.25 + 0.17) / 2.0


class PairTrader(Strategy):
    def __init__(self, config: PairTraderConfig):
        super().__init__(config=config)
        self.source_id = InstrumentId.from_str(config.source_symbol)
        self.target_id = InstrumentId.from_str(config.target_symbol)
        self.model: Optional[ModelUpdate] = None
        self.hedge_ratio: Optional[float] = None
        self.std_pred: Optional[float] = None
        self.prediction: Optional[float] = None
        self._current_edge: float = 0.0
        self._current_required_edge: float = 0.0
        self.bar_spec = BarSpecification.from_str(self.config.bar_spec)
        self._summarised: set = set()
        self._position_id: int = 0

    def on_start(self):
        # Set instruments
        self.source = self.cache.instrument(self.source_id)
        self.target = self.cache.instrument(self.target_id)

        # Subscribe to bars
        self.subscribe_bars(make_bar_type(instrument_id=self.source_id, bar_spec=self.bar_spec))
        self.subscribe_bars(make_bar_type(instrument_id=self.target_id, bar_spec=self.bar_spec))

        # Subscribe to model and predictions
        self.subscribe_data(
            data_type=DataType(ModelUpdate, metadata={"instrument_id": self.target_id.value})
        )
        self.subscribe_data(
            data_type=DataType(Prediction, metadata={"instrument_id": self.target_id.value})
        )

    def on_bar(self, bar: Bar):
        self._update_theoretical()
        self._check_for_entry(bar)
        self._check_for_exit(timer=None, bar=bar)

    def on_data(self, data: Data):
        if isinstance(data, ModelUpdate):
            self._on_model_update(data)
        elif isinstance(data, Prediction):
            self._on_prediction(data)
        else:
            raise TypeError()

    def on_event(self, event: Event):
        self._check_for_hedge(timer=None, event=event)
        if isinstance(event, (PositionOpened, PositionChanged)):
            position = self.cache.position(event.position_id)
            self._log.info(f"{position}", color=LogColor.YELLOW)
            assert position.quantity < 200  # Runtime check for bug in code

    def _on_model_update(self, model_update: ModelUpdate):
        self.model = model_update.model
        self.hedge_ratio = model_update.hedge_ratio
        self.std_pred = model_update.std_prediction

    def _on_prediction(self, prediction: Prediction):
        self.prediction = prediction.prediction
        self._update_theoretical()

    def _update_theoretical(self):
        """We've either received an update Bar market or a new prediction, update our `current_edge`"""
        if not self.prediction:
            return

        quote_right: Bar = self.cache.bar(make_bar_type(self.target_id, bar_spec=self.bar_spec))
        if not quote_right:
            return

        self._current_edge = 0
        close_target = quote_right.close
        if (self.prediction - close_target) > 0:
            self._current_edge = self.prediction - close_target
        elif (close_target - self.prediction) > 0:
            self._current_edge = close_target - self.prediction

    def _check_for_entry(self, bar: Bar):
        if bar.bar_type.instrument_id == self.target_id and self.prediction is not None:
            # Send in orders
            quote_target: Bar = self.cache.bar(
                make_bar_type(self.target_id, bar_spec=self.bar_spec)
            )
            if not quote_target:
                return

            market_right = quote_target.close
            self._current_required_edge = self.std_pred * self.config.trade_width_std_dev

            if self._current_edge > self._current_required_edge:
                # Our theoretical price is above the market; we want to buy
                side = OrderSide.BUY
                max_volume = int(self.config.notional_trade_size_usd / market_right)
                capped_volume = self._cap_volume(
                    instrument_id=self.target_id, max_quantity=max_volume
                )
                price = self.prediction - self._current_required_edge
                self._log.debug(f"{side} {max_volume=} {capped_volume=} {price=}")
            elif self._current_edge < -self._current_required_edge:
                # Our theoretical price is below the market; we want to sell
                side = OrderSide.SELL
                max_volume = int(self.config.notional_trade_size_usd / market_right)
                capped_volume = self._cap_volume(
                    instrument_id=self.target_id, max_quantity=max_volume
                )
                price = self.prediction + self._current_required_edge
                self._log.debug(f"{side} {max_volume=} {capped_volume=} {price=}")
            else:
                return
            if capped_volume == 0:
                # We're at our max limit, cancel any remaining orders and return
                for order in self.cache.orders_open(
                    instrument_id=self.target_id, strategy_id=self.id
                ):
                    self.cancel_order(order=order)
                return
            self._log.info(
                f"Entry opportunity: {side} market={market_right}, "
                f"theo={self.prediction:0.3f} {capped_volume=} ({self._current_edge=:0.3f}, "
                f"{self._current_required_edge=:0.3f})",
                color=LogColor.GREEN,
            )
            # Cancel any existing orders
            for order in self.cache.orders_open(instrument_id=self.target_id, strategy_id=self.id):
                self.cancel_order(order=order)
            order = self.order_factory.limit(
                instrument_id=self.target_id,
                order_side=side,
                price=Price(price, self.target.price_precision),
                quantity=Quantity.from_int(capped_volume),
                time_in_force=TimeInForce.IOC,
            )
            self._log.info(f"ENTRY {order.info()}", color=LogColor.BLUE)
            self.submit_order(order, PositionId(f"target-{self._position_id}"))

    def _cap_volume(self, instrument_id: InstrumentId, max_quantity: int) -> int:
        position_quantity = 0
        position = self.current_position(instrument_id)
        if position is not None:
            position_quantity = position.quantity
        return max(0, max_quantity - position_quantity)

    def _check_for_hedge(self, timer=None, event: Optional[Event] = None):
        if not ((isinstance(event, (PositionEvent,)) and event.instrument_id == self.target_id)):
            return

        timer_name = f"hedge-{self.id}"
        try:
            self._hedge_position(event)
            # Keep scheduling this method to run until we're hedged
            if timer_name in self.clock.timer_names:
                self.clock.cancel_timer(timer_name)
            self.clock.set_time_alert(
                name=timer_name,
                alert_time=self.clock.utc_now() + pd.Timedelta(seconds=2),
                callback=partial(self._check_for_hedge, event=event),
            )
        except RepeatedEventComplete:
            # Hedge is complete, return
            if timer_name in self.clock.timer_names:
                self.clock.cancel_timer(timer_name)
            return

    def _hedge_position(self, event: PositionEvent):
        # We've opened or changed position in our source instrument, we will likely need to hedge.
        target_position = self.cache.position(event.position_id)
        hedge_quantity = int(round(target_position.quantity * self.hedge_ratio, 0))
        quantity = 0
        if isinstance(event, PositionClosed):
            # (possibly) Reducing our position in the target instrument
            source_position: Position = self.current_position(self.source_id)
            if source_position is not None and source_position.is_closed:
                if source_position.id.value not in self._summarised:
                    self._summarise_position()
                    self._position_id += 1
                quantity = source_position.quantity
                side = self._opposite_side(source_position.side)
        else:
            # (possibly) Increasing our position in hedge instrument
            side = self._opposite_side(target_position.side)
            quantity = self._cap_volume(instrument_id=self.source_id, max_quantity=hedge_quantity)

        if quantity == 0:
            # Fully hedged, cancel any existing orders
            for order in self.cache.orders_open(instrument_id=self.source_id, strategy_id=self.id):
                self.cancel_order(order=order)
            raise RepeatedEventComplete
        elif self.cache.orders_inflight(instrument_id=self.source_id, strategy_id=self.id):
            # Don't send more orders if we have some currently in-flight
            return

        # Cancel any existing orders
        for order in self.cache.orders_open(instrument_id=self.source_id, strategy_id=self.id):
            self.cancel_order(order=order)
        order = self.order_factory.market(
            instrument_id=self.source_id,
            order_side=side,
            quantity=Quantity.from_int(quantity),
        )
        self._log.info(f"ENTRY HEDGE {order.info()}", color=LogColor.BLUE)
        self.submit_order(order, PositionId(f"source-{self._position_id}"))
        return order

    def _check_for_exit(self, timer=None, bar: Optional[Bar] = None):
        if not self.cache.positions(strategy_id=self.id):
            return

        # Keep checking that we have successfully got a hedge
        timer_name = f"exit-{self.id}"
        try:
            self._exit_position(bar=bar)
            # Keep scheduling this method to run until we're exited
            if timer_name in self.clock.timer_names:
                self.clock.cancel_timer(timer_name)
            self.clock.set_time_alert(
                name=timer_name,
                alert_time=self.clock.utc_now() + pd.Timedelta(seconds=2),
                callback=partial(self._check_for_exit, bar=bar),
            )
        except RepeatedEventComplete:
            # Hedge is complete, return
            if timer_name in self.clock.timer_names:
                self.clock.cancel_timer(timer_name)
            return

    def _exit_position(self, bar: Bar):
        position: Position = self.current_position(self.target_id)
        if position is not None:
            if position.is_closed:
                raise RepeatedEventComplete()
            if self._current_edge < (self._current_required_edge * 0.25):
                if self.cache.orders_inflight(instrument_id=self.target_id, strategy_id=self.id):
                    # Order currently in-flight, don't send again
                    return
                self._log.info(
                    f"Trigger to close position {self._current_edge=:0.3f} {self._current_required_edge=:0.3f} (* 0.25)",
                    color=LogColor.CYAN,
                )
                # We're close back to fair value, we should try and close our position
                order = self.order_factory.market(
                    instrument_id=self.target_id,
                    order_side=self._opposite_side(position.side),
                    quantity=position.quantity,
                )
                self._log.info(f"CLOSE {order.info()}", color=LogColor.BLUE)
                self.submit_order(order, PositionId(f"target-{self._position_id}"))

    def current_position(self, instrument_id: InstrumentId) -> Optional[Position]:
        try:
            side = {self.source_id: "source", self.target_id: "target"}[instrument_id]
            return self.cache.position(PositionId(f"{side}-{self._position_id}"))
        except AssertionError:
            return None

    def _opposite_side(self, side: PositionSide):
        return {
            PositionSide.LONG: OrderSide.SELL,
            PositionSide.SHORT: OrderSide.BUY,
            PositionSide.FLAT: None,
        }[side]

    def _summarise_position(self):
        src_pos: Position = self.current_position(instrument_id=self.source_id)
        tgt_pos: Position = self.current_position(instrument_id=self.target_id)
        self.log.warning("Hedge summary:", color=LogColor.BLUE)
        self.log.warning(
            f"target: {order_side_to_str(tgt_pos.events[0].order_side)} {tgt_pos.peak_qty}, "
            f"{tgt_pos.avg_px_open=}, {tgt_pos.avg_px_close=}, {tgt_pos.realized_return=:0.4f}",
            color=LogColor.NORMAL,
        )
        self.log.warning(
            f"source: {order_side_to_str(src_pos.events[0].order_side)} {src_pos.peak_qty}, "
            f"{src_pos.avg_px_open=}, {src_pos.avg_px_close=}, {src_pos.realized_return=:0.4f}",
            color=LogColor.NORMAL,
        )

        def peak_notional(pos):
            entry_order = self.cache.order(pos.events[0].client_order_id)
            return (
                pos.peak_qty
                * {OrderSide.BUY: 1.0, OrderSide.SELL: -1.0}[entry_order.side]
                * pos.avg_px_open
            )

        tgt_notional = peak_notional(tgt_pos)
        src_notional = peak_notional(src_pos)
        margin_requirements = (
            abs(tgt_notional) + abs(src_notional)
        ) * self.config.ib_long_short_margin_requirement
        pnl = src_pos.realized_pnl + tgt_pos.realized_pnl
        return_bps = float(pnl) / margin_requirements * 10_000
        self.log.warning(
            f"position duration = {human_readable_duration(src_pos.duration_ns)} "
            f"(opened={unix_nanos_to_dt(src_pos.ts_opened)}, closed={unix_nanos_to_dt(src_pos.ts_closed)}",
            color=LogColor.NORMAL,
        )
        self.log.warning(
            f"Spread=({tgt_notional:.0f}/{src_notional:.0f}), total_margin_required={margin_requirements:0.1f} "
            f"PNL=${pnl}, margin_return={return_bps:0.1f}bps\n",
            color=LogColor.GREEN if pnl > 0 else LogColor.RED,
        )

        self._summarised.add(src_pos.id.value)

    def on_stop(self):
        self.close_all_positions(self.source_id)
        self.close_all_positions(self.target_id)
