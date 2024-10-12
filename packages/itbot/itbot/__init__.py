import json
from dataclasses import dataclass, asdict
from typing import Optional
from enum import Enum


class TradeType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"


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
