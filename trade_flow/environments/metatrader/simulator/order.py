from enum import IntEnum
from datetime import datetime


class OrderType(IntEnum):
    """
    Enum for representing the type of an order: Buy or Sell.
    """

    Sell = 0  # Represents a sell order
    Buy = 1  # Represents a buy order

    @property
    def sign(self) -> float:
        """
        Returns the sign associated with the order type.
        +1 for Buy, -1 for Sell.
        """
        return 1.0 if self == OrderType.Buy else -1.0

    @property
    def opposite(self) -> "OrderType":
        """
        Returns the opposite order type.
        Sell returns Buy, and Buy returns Sell.
        """
        return OrderType.Buy if self == OrderType.Sell else OrderType.Sell


class Order:
    """
    Represents a trading order with its details, including entry and exit points.
    """

    def __init__(
        self,
        id: int,
        type: OrderType,
        symbol: str,
        volume: float,
        fee: float,
        entry_time: datetime,
        entry_price: float,
        exit_time: datetime,
        exit_price: float,
    ) -> None:
        """
        Initializes a new trading order.

        Args:
            id (int): Unique identifier for the order.
            type (OrderType): Type of the order (Buy or Sell).
            symbol (str): Trading symbol (e.g., "EURUSD").
            volume (float): Volume of the trade.
            fee (float): Fee associated with the trade.
            entry_time (datetime): Timestamp when the order was opened.
            entry_price (float): Price at which the order was opened.
            exit_time (datetime): Timestamp when the order was closed.
            exit_price (float): Price at which the order was closed.
        """
        self.id = id
        self.type = type
        self.symbol = symbol
        self.volume = volume
        self.fee = fee
        self.entry_time = entry_time
        self.entry_price = entry_price
        self.exit_time = exit_time
        self.exit_price = exit_price

        self.exit_balance = float("nan")  # Final balance after order closure
        self.exit_equity = float("nan")  # Final equity after order closure
        self.profit = 0.0  # Profit or loss from the order
        self.margin = 0.0  # Margin used for the order
        self.closed: bool = False  # Order status (closed or open)
