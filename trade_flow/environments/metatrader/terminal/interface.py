import platform
from enum import Enum
from datetime import datetime
import numpy as np


def detect_system() -> str:
    system = platform.system()
    if system == "Windows":
        return "Windows"
    elif system == "Linux":
        return "Linux"
    else:
        return "Unknown OS"


os_type = detect_system()
if os_type == "Windows":
    try:
        import MetaTrader5 as mt5
        from MetaTrader5 import SymbolInfo as MTSymbolInfo

        MT5_AVAILABLE = True
    except ImportError:
        MTSymbolInfo = object
        MT5_AVAILABLE = False
else:
    try:
        from packages.mt5any import MetaTrader5 as _mt5

        MTSymbolInfo = object

        MT5_AVAILABLE = True
    except ImportError:
        MTSymbolInfo = object
        MT5_AVAILABLE = False


class Timeframe(Enum):
    """
    Enumeration for MetaTrader5 timeframes, providing mappings between custom
    constants and the corresponding MetaTrader5 timeframe values.
    """

    M1 = 1  # 1 minute
    M2 = 2  # 2 minutes
    M3 = 3  # 3 minutes
    M4 = 4  # 4 minutes
    M5 = 5  # 5 minutes
    M6 = 6  # 6 minutes
    M10 = 10  # 10 minutes
    M12 = 12  # 12 minutes
    M15 = 15  # 15 minutes
    M20 = 20  # 20 minutes
    M30 = 30  # 30 minutes
    H1 = 1 | 0x4000  # 1 hour
    H2 = 2 | 0x4000  # 2 hours
    H3 = 3 | 0x4000  # 3 hours
    H4 = 4 | 0x4000  # 4 hours
    H6 = 6 | 0x4000  # 6 hours
    H8 = 8 | 0x4000  # 8 hours
    H12 = 12 | 0x4000  # 12 hours
    D1 = 24 | 0x4000  # 1 day
    W1 = 1 | 0x8000  # 1 week
    MN1 = 1 | 0xC000  # 1 month


def initialize() -> bool:
    """
    Initializes MetaTrader5 terminal for interaction.

    Returns:
        bool: True if initialization is successful, False otherwise.

    Raises:
        OSError: If MetaTrader5 is not available on the current platform.
    """
    _check_mt5_available()
    return mt5.initialize()


def shutdown() -> None:
    """
    Shuts down MetaTrader5 terminal.

    Raises:
        OSError: If MetaTrader5 is not available on the current platform.
    """
    _check_mt5_available()
    mt5.shutdown()


def copy_rates_range(
    symbol: str, timeframe: Timeframe, date_from: datetime, date_to: datetime
) -> np.ndarray:
    """
    Retrieves historical data for a given symbol within a specific date range.

    Args:
        symbol (str): The trading symbol to retrieve data for.
        timeframe (Timeframe): The timeframe to fetch data (e.g., M1, H1).
        date_from (datetime): The starting date for the range.
        date_to (datetime): The ending date for the range.

    Returns:
        np.ndarray: A structured array of price data.

    Raises:
        OSError: If MetaTrader5 is not available on the current platform.
    """
    _check_mt5_available()
    return mt5.copy_rates_range(symbol, timeframe.value, date_from, date_to)


def symbol_info(symbol: str) -> MTSymbolInfo:
    """
    Retrieves symbol information for a given trading symbol.

    Args:
        symbol (str): The trading symbol to fetch information for.

    Returns:
        MTSymbolInfo: MetaTrader5's SymbolInfo object containing symbol data.

    Raises:
        OSError: If MetaTrader5 is not available on the current platform.
    """
    _check_mt5_available()
    return mt5.symbol_info(symbol)


def _check_mt5_available() -> None:
    """
    Checks if MetaTrader5 is available, raises an exception if not.

    Raises:
        OSError: If MetaTrader5 is not available on the current platform.
    """
    global mt5

    if not MT5_AVAILABLE:
        raise OSError("MetaTrader5 is not available on your platform.")

    mt5 = _mt5()
