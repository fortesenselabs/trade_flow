from dataclasses import dataclass
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
