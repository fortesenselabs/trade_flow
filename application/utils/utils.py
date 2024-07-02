import pytz
import dateparser
import pandas as pd
from datetime import datetime, timezone
from typing import List
from application.models import ServerTimeResponse


def get_server_time() -> ServerTimeResponse:
    """
    Retrieves the current server time as a Unix timestamp and timezone.

    Returns:
        ServerTimeResponse: Current server time with timezone and Unix timestamp.
    """
    now = datetime.now(timezone.utc)
    response = {"timezone": "UTC", "unix_timestamp": int(now.timestamp())}
    return ServerTimeResponse(**response)


def detect_format(date_str: str, formats: List[str]) -> str:
    for date_format in formats:
        try:
            datetime.strptime(date_str, date_format)
            return date_format
        except ValueError:
            continue

    raise ValueError(f"Time data '{date_str}' does not match any known formats.")


def date_to_timestamp(date_str: str) -> int:
    # List of potential date formats
    date_formats = [
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y.%m.%d %H:%M",
        "%Y-%m-%d %H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y.%m.%d %H:%M",
        "%Y/%m/%d %H:%M:%S.%f%z",
        "%Y/%m/%d %H:%M:%S%z",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
    ]

    # Detect the correct date format
    date_format = detect_format(date_str, date_formats)

    # Convert the date string to a datetime object
    dt_obj = datetime.strptime(date_str, date_format)

    # Convert the datetime object to a timestamp
    timestamp = int(dt_obj.timestamp())

    return timestamp


def pandas_get_interval(freq: str, timestamp: int = None):
    """
    Find a discrete interval for the given timestamp and return its start and end.

    :param freq: pandas frequency
    :param timestamp: milliseconds (13 digits)
    :return: triple (start, end)
    """
    if not timestamp:
        timestamp = int(datetime.now(pytz.utc).timestamp())  # seconds (10 digits)
        # Alternatively: timestamp = int(datetime.utcnow().replace(tzinfo=pytz.utc).timestamp())
    elif isinstance(timestamp, datetime):
        timestamp = int(timestamp.replace(tzinfo=pytz.utc).timestamp())
    elif isinstance(timestamp, int):
        pass
    else:
        ValueError(
            f"Error converting timestamp {timestamp} to millis. Unknown type {type(timestamp)} "
        )

    # Interval length for the given frequency
    interval_length_sec = pandas_interval_length_ms(freq) / 1000

    start = (timestamp // interval_length_sec) * interval_length_sec
    end = start + interval_length_sec

    return int(start * 1000), int(end * 1000)


def pandas_interval_length_ms(freq: str):
    return int(pd.Timedelta(freq).to_pytimedelta().total_seconds() * 1000)


def now_timestamp():
    """
    INFO:
    https://github.com/sammchardy/python-binance/blob/master/binance/helpers.py
    date_to_milliseconds(date_str) - UTC date string to millis

    :return: timestamp in millis
    :rtype: int
    """
    return int(datetime.utcnow().replace(tzinfo=timezone.utc).timestamp() * 1000)


def find_index(df: pd.DataFrame, date_str: str, column_name: str = "timestamp"):
    """
    Return index of the record with the specified datetime string.

    :return: row id in the input data frame which can be then used in iloc function
    :rtype: int
    """
    d = dateparser.parse(date_str)
    try:
        res = df[df[column_name] == d]
    except TypeError:  # "Cannot compare tz-naive and tz-aware datetime-like objects"
        # Change timezone (set UTC timezone or reset timezone)
        if d.tzinfo is None or d.tzinfo.utcoffset(d) is None:
            d = d.replace(tzinfo=pytz.utc)
        else:
            d = d.replace(tzinfo=None)

        # Repeat
        res = df[df[column_name] == d]

    if res is None or len(res) == 0:
        raise ValueError(
            f"Cannot find date '{date_str}' in the column '{column_name}'. Either it does not exist or wrong format"
        )

    id = res.index[0]

    return id
