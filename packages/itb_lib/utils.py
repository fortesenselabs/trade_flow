import importlib
import re
import json
from typing import Any, Tuple
import pytz
import pandas as pd
from pathlib import Path
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from datetime import datetime, timedelta, timezone


# Set the package root directory
PACKAGE_ROOT = Path(__file__).parent.parent


def load_config(config_file: str) -> dict:
    """
    Loads and parses a JSON configuration file, removing comments.

    Args:
        config_file (str): Relative path to the configuration file.

    Returns:
        dict: Parsed JSON configuration.

    Raises:
        FileNotFoundError: If the configuration file doesn't exist.
        json.JSONDecodeError: If the file contains invalid JSON.

    Example:
        config = load_config("config/settings.json")
    """
    if config_file:
        config_file_path = PACKAGE_ROOT / config_file

        with open(config_file_path, encoding="utf-8") as json_file:
            # Read the configuration file as a string
            conf_str = json_file.read()

            # Remove any comments that start with // (single-line comments)
            conf_str = re.sub(r"//.*$", "", conf_str, flags=re.M)

            # Parse the cleaned JSON string
            conf_json = json.loads(conf_str)

            return conf_json


def resolve_generator_name(gen_name: str) -> Any:
    """
    Resolve the specified generator name to a function reference.
    The fully qualified name consists of the module name and function name separated by a colon,
    for example: 'mod1.mod2.mod3:my_func'.

    Example: fn = resolve_generator_name("features.gen_features_topbot:generate_labels_topbot3")
    """
    mod_and_func = gen_name.split(":", 1)
    mod_name = mod_and_func[0] if len(mod_and_func) > 1 else None
    func_name = mod_and_func[-1]

    if not mod_name:
        return None

    try:
        mod = importlib.import_module(mod_name)
    except Exception:
        return None

    try:
        func = getattr(mod, func_name)
    except AttributeError:
        return None

    return func


#
# Decimal Utilities
#


def to_decimal(value, precision=8):
    """Convert a value to a Decimal with specified precision.

    The value can be a string, float, or Decimal. This function ensures
    the resulting Decimal is rounded down to the specified precision.

    Args:
        value (Union[str, float, Decimal]): The value to convert.
        precision (int): The number of decimal places to retain. Default is 8.

    Returns:
        Decimal: The converted value as a Decimal with specified precision.
    """
    rounding_unit = Decimal(1) / (Decimal(10) ** precision)
    result = Decimal(str(value)).quantize(rounding_unit, rounding=ROUND_DOWN)
    return result


def round_str(value, digits):
    """Round a value to a specified number of decimal places and return as a string.

    This function rounds the given value to the specified number of decimal places
    using the ROUND_HALF_UP method.

    Args:
        value (Union[str, float, Decimal]): The value to round.
        digits (int): The number of decimal places to round to.

    Returns:
        str: The rounded value as a string.
    """
    rounding_unit = Decimal(1) / (Decimal(10) ** digits)
    result = Decimal(str(value)).quantize(rounding_unit, rounding=ROUND_HALF_UP)
    return f"{result:.{digits}f}"


def round_down_str(value, digits):
    """Round down a value to a specified number of decimal places and return as a string.

    This function rounds down the given value to the specified number of decimal
    places using the ROUND_DOWN method.

    Args:
        value (Union[str, float, Decimal]): The value to round down.
        digits (int): The number of decimal places to round down to.

    Returns:
        str: The rounded down value as a string.
    """
    rounding_unit = Decimal(1) / (Decimal(10) ** digits)
    result = Decimal(str(value)).quantize(rounding_unit, rounding=ROUND_DOWN)
    return f"{result:.{digits}f}"


#
# Binance specific
#


def klines_to_df(klines, df=None):
    """
    Convert a list of klines into a DataFrame, appending to an existing DataFrame if provided.
    """
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
    data = data.astype(
        {
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
    )

    # Append to existing DataFrame if provided
    df = pd.concat([df, data]) if df is not None else data

    # Drop duplicates
    df = df.drop_duplicates(subset=["timestamp"], keep="last")
    df.set_index("timestamp", inplace=True)

    return df


def binance_klines_to_df(klines: list) -> pd.DataFrame:
    """
    Convert a list of klines to a DataFrame.
    """
    df = pd.DataFrame(
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

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")

    for col in [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_av",
        "trades",
        "tb_base_av",
        "tb_quote_av",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df.set_index("timestamp", inplace=True)

    return df


def binance_freq_from_pandas(freq: str) -> str:
    """
    Map pandas frequency to Binance API frequency.
    """
    freq_mapping = {"min": "m", "D": "d", "W": "w", "BMS": "M"}
    for key, value in freq_mapping.items():
        if freq.endswith(key):
            return freq.replace(key, value)

    # Ensure length constraints for the frequency
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


def binance_get_interval(freq: str, timestamp: int = None) -> Tuple[int, int]:
    """
    Return a tuple of interval start (including) and end (excluding) in milliseconds.
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    elif isinstance(timestamp, int):
        timestamp = pd.to_datetime(timestamp, unit="ms").to_pydatetime()

    timestamp = timestamp.replace(microsecond=0, tzinfo=timezone.utc)

    # Initialize start and end
    start = end = None

    if freq == "1s":
        start = timestamp.timestamp()
        end = start + 1
    elif freq == "5s":
        reference_timestamp = timestamp.replace(second=0)
        full_intervals_no = (timestamp - reference_timestamp).total_seconds() // 5
        start = reference_timestamp.timestamp() + (5 * full_intervals_no)
        end = start + 5
    elif freq in ["1m", "5m", "1h"]:
        # Additional logic for handling 5m and 1m intervals
        if freq == "1m":
            timestamp = timestamp.replace(second=0)
        elif freq == "5m":
            timestamp = timestamp.replace(minute=timestamp.minute // 5 * 5, second=0)

        start = timestamp.timestamp()
        end = start + (1 if freq == "1m" else 5) * 60  # 1m or 5m in seconds
    else:
        raise ValueError(f"Unknown frequency: {freq}")

    return int(start * 1000), int(end * 1000)


def pandas_get_interval(freq: str, timestamp: int = None) -> Tuple[int, int]:
    """
    Find a discrete interval for the given timestamp and return its start and end.
    """
    if timestamp is None:
        timestamp = int(datetime.now(pytz.utc).timestamp())
    elif isinstance(timestamp, datetime):
        timestamp = int(timestamp.replace(tzinfo=pytz.utc).timestamp())
    elif isinstance(timestamp, int):
        pass
    else:
        raise ValueError(
            f"Error converting timestamp {timestamp} to millis. Unknown type {type(timestamp)}."
        )

    interval_length_sec = pandas_interval_length_ms(freq) / 1000
    start = (timestamp // interval_length_sec) * interval_length_sec
    end = start + interval_length_sec

    return int(start * 1000), int(end * 1000)


def pandas_interval_length_ms(freq: str) -> int:
    """
    Returns the length of the given frequency in milliseconds.
    """
    return int(pd.Timedelta(freq).total_seconds() * 1000)


#
# Date and time
#
