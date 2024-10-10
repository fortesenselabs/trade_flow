from dataclasses import dataclass
from typing import Optional


@dataclass
class Signal:
    """
    Signal dataclass to represent trading signals.

    Attributes:
        symbol (str): The trading symbol (e.g., "BTCUSD").
        price (str): The price of the trading signal.
        score (str): The score of the signal.
        trend (Optional[str]): The trend direction (e.g., "↑").
        zone (Optional[str]): The zone classification.
        trade_type (str): The type of trade signal (e.g., "BUY" or "SELL").
    """

    symbol: str
    price: str
    score: str
    trend: Optional[str] = None
    zone: Optional[str] = None
    trade_type: str = "None"  # Default type is set to "None"
