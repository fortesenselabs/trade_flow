import json
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import timedelta
from nautilus_trader.core.data import Data
from nautilus_trader.core.message import Event
from nautilus_trader.model.data import DataType
from nautilus_trader.model.data import Bar, BarSpecification
from nautilus_trader.model.events.position import PositionChanged, PositionOpened
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.orders import MarketOrder
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.common.enums import LogColor

from nautilus_trader.config import StrategyConfig
from nautilus_trader.trading.strategy import Strategy
from packages.tf_trade.tf_trade.types import TradeType
from trade_flow.environments.nautilus_trader.utils import make_bar_type


class TradeType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"


class ModelType(Enum):
    SKLEARN = "SKLEARN"
    TORCH = "TORCH"


@dataclass
class Signal:
    """
    Signal dataclass to represent trading signals.

    Attributes:
        symbol (str): The trading symbol (e.g., "BTCUSD").
        price (float): The price of the trading signal.
        score (float): The score of the signal.
        trend (Optional[str]): The trend direction (e.g., "↑").
        zone (Optional[str]): The zone classification.
        trade_type (TradeType): The type of trade signal (e.g., TradeType.BUY or TradeType.SELL).
        position_size (float): The size of the position for the trade.
    """

    symbol: str
    price: float
    score: float
    trend: Optional[str] = None
    zone: Optional[str] = None
    trade_type: TradeType = TradeType.NEUTRAL  # Default type set to TradeType.NEUTRAL
    position_size: float = 0.01  # Default position size set to 0.01

    def to_json(self) -> str:
        """
        Convert the Signal instance to a JSON string.

        Returns:
            str: The JSON string representation of the Signal.
        """
        # Convert the dataclass to a dict and handle TradeType conversion
        signal_dict = asdict(self)
        signal_dict["trade_type"] = self.trade_type.name  # Store TradeType as a string
        return json.dumps(signal_dict)

    @staticmethod
    def from_json(json_str: str) -> "Signal":
        """
        Create a Signal instance from a JSON string.

        Args:
            json_str (str): The JSON string representing a Signal.

        Returns:
            Signal: A new Signal instance created from the JSON data.
        """
        # Parse JSON string into a dict
        signal_dict = json.loads(json_str)
        # Convert trade_type back to TradeType enum
        signal_dict["trade_type"] = TradeType[signal_dict["trade_type"]]
        return Signal(**signal_dict)


class ModelUpdate(Data):
    def __init__(
        self,
        model: Any,
        hedge_ratio: float,
        ts_init: int,
    ):
        super().__init__(ts_init=ts_init, ts_event=ts_init)
        self.model = model
        self.hedge_ratio = hedge_ratio


class Prediction(Data):
    def __init__(
        self,
        instrument_id: str,
        signal: Signal,
        ts_init: int,
    ):
        super().__init__(ts_init=ts_init, ts_event=ts_init)
        self.instrument_id = instrument_id
        self.signal = signal


class AgentStrategyConfig(StrategyConfig):
    instrument_symbols: List[str]
    notional_trade_size_usd: int = 10_000
    min_model_timedelta: timedelta = timedelta(days=1)
    bar_spec: str = "10-SECOND-LAST"
    # ib_long_short_margin_requirement: float = (0.25 + 0.17) / 2.0


class AgentStrategy(Strategy):
    def __init__(self, config: AgentStrategyConfig):
        super().__init__(config=config)
        # Initialize multiple instruments from config
        self.instrument_ids = [
            InstrumentId.from_str(symbol) for symbol in config.instrument_symbols
        ]
        self.model: Optional[ModelUpdate] = None
        self.hedge_ratios: Dict[str, Optional[float]] = {
            symbol: None for symbol in config.instrument_symbols
        }
        self.std_preds: Dict[str, Optional[float]] = {
            symbol: None for symbol in config.instrument_symbols
        }
        self.predictions: Dict[str, Optional[float]] = {
            symbol: None for symbol in config.instrument_symbols
        }
        self._current_edge: float = 0.0
        self._current_required_edge: float = 0.0
        self.bar_spec = BarSpecification.from_str(self.config.bar_spec)
        self._summarised: set = set()
        self._position_id: int = 0

    def on_start(self):
        # Set and subscribe to each instrument
        self.instruments = {
            instrument_id: self.cache.instrument(instrument_id)
            for instrument_id in self.instrument_ids
        }

        for instrument_id in self.instrument_ids:
            # Subscribe to bars for each instrument
            self.subscribe_bars(make_bar_type(instrument_id=instrument_id, bar_spec=self.bar_spec))
            # Subscribe to model and predictions
            self.subscribe_data(
                data_type=DataType(ModelUpdate, metadata={"instrument_id": instrument_id.value})
            )
            self.subscribe_data(
                data_type=DataType(Prediction, metadata={"instrument_id": instrument_id.value})
            )

    def on_bar(self, bar: Bar):
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

    def buy(self) -> None:
        """
        simple buy method (example).
        """
        order: MarketOrder = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.BUY,
            quantity=self.instrument.make_qty(self.trade_size),
            # time_in_force=TimeInForce.FOK,
        )

        self.submit_order(order)

    def sell(self) -> None:
        """
        simple sell method (example).
        """
        order: MarketOrder = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.SELL,
            quantity=self.instrument.make_qty(self.trade_size),
            # time_in_force=TimeInForce.FOK,
        )

        self.submit_order(order)

    def on_stop(self):
        # Close positions for all instruments
        for instrument_id in self.instrument_ids:
            self.close_all_positions(instrument_id)

    def _on_model_update(self, model_update: ModelUpdate):
        instrument_id = model_update.instrument_id
        self.model = model_update.model
        self.hedge_ratios[instrument_id] = model_update.hedge_ratio
        self.std_preds[instrument_id] = model_update.std_prediction

    def _on_prediction(self, prediction: Prediction):
        instrument_id = prediction.instrument_id
        self.predictions[instrument_id] = prediction.signal

        if prediction.signal.trade_type == TradeType.BUY:
            self.buy()
        elif prediction.signal.trade_type == TradeType.SELL:
            self.sell()
        else:
            pass

        # self._calculate_reward()

    # def _calculate_reward(self):
    #     self.
    #     pass
