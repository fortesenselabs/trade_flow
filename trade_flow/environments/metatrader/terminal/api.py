from typing import Tuple
import pytz
import calendar
from datetime import datetime
import pandas as pd
from . import interface as mt
from .symbol import SymbolInfo


def retrieve_data(
    symbol: str,
    from_dt: datetime,
    to_dt: datetime,
    timeframe: mt.Timeframe,
    shutdown_terminal: bool = True,
) -> Tuple[SymbolInfo, pd.DataFrame]:
    """
    Retrieves historical data for a given symbol within a specified date range and timeframe.

    Args:
        symbol (str): The trading symbol to retrieve data for.
        from_dt (datetime): The start date for the data retrieval (in local timezone).
        to_dt (datetime): The end date for the data retrieval (in local timezone).
        timeframe (mt.Timeframe): The MetaTrader timeframe to use for data retrieval.
        shutdown_terminal (bool): Whether to shutdown MetaTrader after retrieval. Default is True.

    Returns:
        Tuple[SymbolInfo, pd.DataFrame]: A tuple containing symbol information and the price data.
    """

    # Initialize MetaTrader
    if not mt.initialize():
        raise ConnectionError("MetaTrader cannot be initialized")

    symbol_info = _get_symbol_info(symbol)

    # Convert local time to UTC
    utc_from = _local_to_utc(from_dt)
    utc_to = _local_to_utc(to_dt)

    all_rates = []
    partial_from = utc_from
    partial_to = _add_months(partial_from, 1)

    # Fetch data in monthly chunks to avoid excessive data loads
    while partial_from < utc_to:
        rates = mt.copy_rates_range(symbol, timeframe, partial_from, partial_to)
        all_rates.extend(rates)
        partial_from = _add_months(partial_from, 1)
        partial_to = min(_add_months(partial_to, 1), utc_to)

    # Convert the data into a pandas DataFrame
    rates_frame = pd.DataFrame(
        [list(r) for r in all_rates],
        columns=["Time", "Open", "High", "Low", "Close", "Volume", "_", "_"],
    )
    rates_frame["Time"] = pd.to_datetime(rates_frame["Time"], unit="s", utc=True)

    # Filter and clean the DataFrame
    data = rates_frame[["Time", "Open", "Close", "Low", "High", "Volume"]].set_index("Time")
    data = data.loc[~data.index.duplicated(keep="first")]

    if shutdown_terminal:
        mt.shutdown()

    return symbol_info, data


def _get_symbol_info(symbol: str) -> SymbolInfo:
    """
    Fetches the symbol information from MetaTrader.

    Args:
        symbol (str): The trading symbol.

    Returns:
        SymbolInfo: Object containing detailed symbol information.
    """
    info = mt.symbol_info(symbol)
    return SymbolInfo(info)


def _local_to_utc(dt: datetime) -> datetime:
    """
    Converts a local datetime object to UTC.

    Args:
        dt (datetime): A timezone-aware local datetime.

    Returns:
        datetime: The equivalent UTC datetime.
    """
    return dt.astimezone(pytz.timezone("Etc/UTC"))


def _add_months(sourcedate: datetime, months: int) -> datetime:
    """
    Adds a number of months to a given datetime object, handling month overflow.

    Args:
        sourcedate (datetime): The original datetime.
        months (int): The number of months to add.

    Returns:
        datetime: The new datetime with the months added.
    """
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])

    return datetime(
        year,
        month,
        day,
        sourcedate.hour,
        sourcedate.minute,
        sourcedate.second,
        tzinfo=sourcedate.tzinfo,
    )
