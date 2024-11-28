from datetime import datetime
from enum import Enum
from trade_flow.core import TimedIdentifiable

class TradeType(Enum):
    MARKET: str = "market"
    LIMIT: str = "limit"
    STOP: str = "stop"
    STOP_LIMIT: str = "stop_limit"

    def __str__(self) -> str:
        return self.value


class TradeSide(Enum):
    BUY: str = "buy"
    SELL: str = "sell"

    @property
    def sign(self) -> float:
        """Returns +1 for BUY and -1 for SELL."""
        return 1.0 if self == TradeSide.BUY else -1.0

    @property
    def opposite(self) -> "TradeSide":
        """Returns the opposite trade side: BUY becomes SELL and vice versa."""
        return TradeSide.SELL if self == TradeSide.BUY else TradeSide.BUY

    def instrument(self, pair: "TradingPair") -> "Instrument":
        """Returns base for BUY and quote for SELL in a trading pair."""
        return pair.base if self == TradeSide.BUY else pair.quote

    def __str__(self) -> str:
        return self.value


class Trade(TimedIdentifiable):
    """Represents a trade with details, including entry and exit points."""

    def __init__(
        self,
        order_id: str,
        step: int,
        symbol: "Symbol",
        side: TradeSide,
        trade_type: TradeType,
        quantity: "Quantity",
        commission: "Quantity",
        entry_price: float,
        exit_price: float,
        entry_time: datetime,
        exit_time: datetime,
    ):
        """
        Args:
            order_id: ID of the order.
            step: Trading episode timestep.
            symbol: Trading symbol of the Broker, e.g., "EURUSD", "GBPUSD".
            side: Trade side, either BUY or SELL.
            trade_type: Type of trade (MARKET, LIMIT, etc.).
            quantity: Quantity of the trade.
            commission: Commission paid.
            entry_price: Price at trade entry.
            exit_price: Price at trade exit.
            entry_time: Timestamp when trade was opened.
            exit_time: Timestamp when trade was closed.
        """
        super().__init__()
        self.order_id = order_id
        self.step = step
        self.symbol = symbol
        self.side = side
        self.type = trade_type
        self.quantity = quantity
        self._commission = commission
        self.entry_time = entry_time
        self.entry_price = entry_price
        self.exit_time = exit_time
        self.exit_price = exit_price

        self.exit_balance = float("nan")  # Final balance after order closure
        self.exit_equity = float("nan")  # Final equity after order closure
        self.profit = 0.0  # Profit or loss from the order
        self.margin = 0.0  # Margin used for the order
        self.closed: bool = False  # Order status (closed or open)

    @property
    def base_instrument(self) -> "Instrument":
        """Base instrument for the symbol pair."""
        return self.broker_symbol.symbol

    @property
    def size(self) -> float:
        """Size of the trade."""
        return self.quantity.size

    @property
    def is_buy(self) -> bool:
        """Checks if trade is a BUY."""
        return self.side == TradeSide.BUY

    @property
    def is_sell(self) -> bool:
        """Checks if trade is a SELL."""
        return self.side == TradeSide.SELL

    @property
    def is_limit_order(self) -> bool:
        """Checks if trade is a LIMIT order."""
        return self.type == TradeType.LIMIT

    @property
    def is_market_order(self) -> bool:
        """Checks if trade is a MARKET order."""
        return self.type == TradeType.MARKET

    def to_dict(self) -> dict:
        """Returns a dictionary representation of the trade."""
        return {
            "id": self.id,
            "order_id": self.order_id,
            "step": self.step,
            "symbol": self.symbol,
            "side": self.side,
            "type": self.type,
            "size": self.size,
            "quantity": self.quantity,
            "price": self.entry_price,
            "commission": self._commission,
            "created_at": self.created_at,
        }

    def to_json(self) -> dict:
        """Returns a JSON-serializable dictionary of the trade."""
        return {
            "id": str(self.id),
            "order_id": str(self.order_id),
            "step": int(self.step),
            "symbol": str(self.symbol),
            "side": str(self.side),
            "type": str(self.type),
            "size": float(self.size),
            "quantity": str(self.quantity),
            "price": float(self.entry_price),
            "commission": str(self._commission),
            "created_at": str(self.created_at),
        }

    def __str__(self) -> str:
        """String representation of the trade."""
        data = [f"{k}={v}" for k, v in self.to_dict().items()]
        return f"<{self.__class__.__name__}: {', '.join(data)}>"

    def __repr__(self) -> str:
        return str(self)
