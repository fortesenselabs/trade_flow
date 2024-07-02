import pandas as pd
from datetime import datetime, timezone, timedelta
from apscheduler.triggers.cron import CronTrigger

# from binance.helpers import date_to_milliseconds, interval_to_milliseconds
# from common.gen_features import *


#
# Binance specific
#
def klines_to_df(klines, df):

    data = pd.DataFrame(
        klines,
        columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_av",
            "trades",
            "tb_base_av",
            "tb_quote_av",
            "ignore",
        ],
    )
    data["timestamp"] = pd.to_datetime(data["timestamp"], unit="ms")
    dtypes = {
        "open": "float64",
        "high": "float64",
        "low": "float64",
        "close": "float64",
        "volume": "float64",
        "close_time": "int64",
        "quote_av": "float64",
        "trades": "int64",
        "tb_base_av": "float64",
        "tb_quote_av": "float64",
        "ignore": "float64",
    }
    data = data.astype(dtypes)

    if df is None or len(df) == 0:
        df = data
    else:
        df = pd.concat([df, data])

    # Drop duplicates
    df = df.drop_duplicates(subset=["timestamp"], keep="last")
    # df = df[~df.index.duplicated(keep='last')]  # alternatively, drop duplicates in index

    df.set_index("timestamp", inplace=True)

    return df


def binance_klines_to_df(klines: list):
    """
    Convert a list of klines to a data frame.
    """
    columns = [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_av",
        "trades",
        "tb_base_av",
        "tb_quote_av",
        "ignore",
    ]

    df = pd.DataFrame(klines, columns=columns)

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")

    df["open"] = pd.to_numeric(df["open"])
    df["high"] = pd.to_numeric(df["high"])
    df["low"] = pd.to_numeric(df["low"])
    df["close"] = pd.to_numeric(df["close"])
    df["volume"] = pd.to_numeric(df["volume"])

    df["quote_av"] = pd.to_numeric(df["quote_av"])
    df["trades"] = pd.to_numeric(df["trades"])
    df["tb_base_av"] = pd.to_numeric(df["tb_base_av"])
    df["tb_quote_av"] = pd.to_numeric(df["tb_quote_av"])

    if "timestamp" in df.columns:
        df.set_index("timestamp", inplace=True)

    return df


def binance_freq_from_pandas(freq: str) -> str:
    """
    Map pandas frequency to binance API frequency

    :param freq: pandas frequency https://pandas.pydata.org/docs/user_guide/timeseries.html#timeseries-offset-aliases
    :return: binance frequency https://developers.binance.com/docs/derivatives/coin-margined-futures/market-data/Kline-Candlestick-Data
    """
    if freq.endswith("min"):  # Binance: 1m, 3m, 5m, 15m, 30m
        freq = freq.replace("min", "m")
    elif freq.endswith("D"):
        freq = freq.replace("D", "d")  # Binance: 1d, 3d
    elif freq.endswith("W"):
        freq = freq.replace("W", "w")
    elif freq == "BMS":
        freq = freq.replace("BMS", "M")

    if len(freq) == 1:
        freq = "1" + freq

    if (
        not (2 <= len(freq) <= 3)
        or not freq[:-1].isdigit()
        or freq[-1] not in ["m", "h", "d", "w", "M"]
    ):
        raise ValueError(
            f"Not supported Binance frequency {freq}. It should be one or two digits followed by a character."
        )

    return freq


def binance_get_interval(freq: str, timestamp: int = None):
    """
    Return a triple of interval start (including), end (excluding) in milliseconds for the specified timestamp or now

    INFO:
    https://github.com/sammchardy/python-binance/blob/master/binance/helpers.py
        interval_to_milliseconds(interval) - binance freq string (like 1m) to millis

    :param freq: binance frequency https://developers.binance.com/docs/derivatives/coin-margined-futures/market-data/Kline-Candlestick-Data
    :return: tuple of start (inclusive) and end (exclusive) of the interval in millis
    :rtype: (int, int)
    """
    if not timestamp:
        timestamp = datetime.utcnow()  # datetime.now(timezone.utc)
    elif isinstance(timestamp, int):
        timestamp = pd.to_datetime(timestamp, unit="ms").to_pydatetime()

    # Although in 3.6 (at least), datetime.timestamp() assumes a timezone naive (tzinfo=None) datetime is in UTC
    timestamp = timestamp.replace(microsecond=0, tzinfo=timezone.utc)

    if freq == "1s":
        start = timestamp.timestamp()
        end = timestamp + timedelta(seconds=1)
        end = end.timestamp()
    elif freq == "5s":
        reference_timestamp = timestamp.replace(second=0)
        now_duration = timestamp - reference_timestamp

        freq_duration = timedelta(seconds=5)

        full_intervals_no = (
            now_duration.total_seconds() // freq_duration.total_seconds()
        )

        start = reference_timestamp + freq_duration * full_intervals_no
        end = start + freq_duration

        start = start.timestamp()
        end = end.timestamp()
    elif freq == "1m":
        timestamp = timestamp.replace(second=0)
        start = timestamp.timestamp()
        end = timestamp + timedelta(minutes=1)
        end = end.timestamp()
    elif freq == "5m":
        # Here we need to find 1 h border (or 1 day border) by removing minutes
        # Then divide (now-1hourstart) by 5 min interval length by finding 5 min border for now
        print(f"Frequency 5m not implemented.")
    elif freq == "1h":
        timestamp = timestamp.replace(minute=0, second=0)
        start = timestamp.timestamp()
        end = timestamp + timedelta(hours=1)
        end = end.timestamp()
    else:
        print(f"Unknown frequency.")

    return int(start * 1000), int(end * 1000)


#
# Date and time
#


def freq_to_CronTrigger(freq: str):
    # Add small time after interval end to get a complete interval from the server
    if freq.endswith("min"):
        if freq[:-3] == "1":
            trigger = CronTrigger(minute="*", second="1", timezone="UTC")
        else:
            trigger = CronTrigger(minute="*/" + freq[:-3], second="1", timezone="UTC")
    elif freq.endswith("h"):
        if freq[:-1] == "1":
            trigger = CronTrigger(hour="*", second="2", timezone="UTC")
        else:
            trigger = CronTrigger(hour="*/" + freq[:-1], second="2", timezone="UTC")
    elif freq.endswith("D"):
        if freq[:-1] == "1":
            trigger = CronTrigger(day="*", second="5", timezone="UTC")
        else:
            trigger = CronTrigger(day="*/" + freq[:-1], second="5", timezone="UTC")
    elif freq.endswith("W"):
        if freq[:-1] == "1":
            trigger = CronTrigger(week="*", second="10", timezone="UTC")
        else:
            trigger = CronTrigger(day="*/" + freq[:-1], second="10", timezone="UTC")
    elif freq.endswith("MS"):
        if freq[:-2] == "1":
            trigger = CronTrigger(month="*", second="30", timezone="UTC")
        else:
            trigger = CronTrigger(month="*/" + freq[:-1], second="30", timezone="UTC")
    else:
        raise ValueError(f"Cannot convert frequency '{freq}' to cron.")

    return trigger


def notnull_tail_rows(df):
    """Maximum number of tail rows without nulls."""

    nan_df = df.isnull()
    nan_cols = nan_df.any()  # Series with columns having at least one NaN
    nan_cols = nan_cols[nan_cols].index.to_list()
    if len(nan_cols) == 0:
        return len(df)

    # Indexes of last NaN for all columns and then their minimum
    tail_rows = nan_df[nan_cols].values[::-1].argmax(axis=0).min()

    return tail_rows
