from typing import List, Dict
import pandas as pd
from nautilus_trader.core.datetime import nanos_to_secs
from nautilus_trader.core.data import Data
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import AggregationSource
from nautilus_trader.model.identifiers import InstrumentId
from sklearn.linear_model import LinearRegression


def bars_to_dataframe(
    instrument_data: Dict[str, List[Bar]], columns: List[str] = ["close"]
) -> pd.DataFrame:
    """
    Converts a dictionary of instrument data, where each instrument has a list of Bar objects, into a multi-indexed
    DataFrame. Each instrument's bars are processed to form a consistent DataFrame structure with specified columns
    and filled forward for any missing data points.

    Parameters:
    ----------
    instrument_data : Dict[str, List[Bar]]
        A dictionary mapping each instrument ID (as a string) to a list of `Bar` objects representing the instrument's
        historical price data. Each `Bar` object must include timestamp (`ts_init`) and other fields that match the
        column names specified in the `columns` parameter.

    columns : List[str], optional
        A list of column names to include in the resulting DataFrame (default is `["close"]`). Each specified column
        will be converted to float and used to build the resulting DataFrame.

    Returns:
    -------
    pd.DataFrame
        A multi-indexed DataFrame where each level of the index corresponds to a combination of the instrument ID and
        timestamp (`ts_init`). The columns in the DataFrame match the specified `columns` parameter, with missing
        values filled forward and rows containing any NaN values dropped.

    Notes:
    ------
    - This function assumes that each `Bar` object in the list provided for each instrument can be converted to a
      dictionary using a `to_dict()` method.
    - Missing values in the specified columns are filled forward using the method `ffill`.
    - Rows where any of the specified columns still contain NaN values after forward-filling are removed.

    Example:
    --------
    >>> bars = {
    >>>     "AAPL": [Bar(ts_init="2023-01-01 09:30:00", close=150.5), ...],
    >>>     "MSFT": [Bar(ts_init="2023-01-01 09:30:00", close=250.0), ...]
    >>> }
    >>> df = bars_to_dataframe(bars, columns=["close", "volume"])
    >>> print(df)

    """

    def _bars_to_frame(bars, instrument_id):
        # Create DataFrame for each instrument and cast specified columns to float
        df = pd.DataFrame([Bar.to_dict(t) for t in bars]).astype({col: float for col in columns})
        return df.assign(instrument_id=instrument_id).set_index(["instrument_id", "ts_init"])

    # Convert each instrument's bars to DataFrame and concatenate them
    all_dataframes = [
        _bars_to_frame(bars=instrument_bars, instrument_id=instrument_id)
        for instrument_id, instrument_bars in instrument_data.items()
    ]

    # Concatenate data for all instruments and select specified columns
    data = pd.concat(all_dataframes)[columns].unstack(0).sort_index().fillna(method="ffill")

    # Convert index to datetime and drop rows with NaN values in the specified columns
    data.index = pd.to_datetime(data.index)
    return data.dropna()


def make_bar_type(instrument_id: InstrumentId, bar_spec) -> BarType:
    return BarType(
        instrument_id=instrument_id,
        bar_spec=bar_spec,
        aggregation_source=AggregationSource.EXTERNAL,
    )


def one(iterable):
    if len(iterable) == 0:
        return None
    elif len(iterable) > 1:
        raise AssertionError("Too many values")
    else:
        return iterable[0]


def pair_bars_to_dataframe(
    source_id: str, source_bars: List[Bar], target_id: str, target_bars: List[Bar]
) -> pd.DataFrame:
    def _bars_to_frame(bars, instrument_id):
        df = pd.DataFrame([t.to_dict(t) for t in bars]).astype({"close": float})
        return df.assign(instrument_id=instrument_id).set_index(["instrument_id", "ts_init"])

    ldf = _bars_to_frame(bars=source_bars, instrument_id=source_id)
    rdf = _bars_to_frame(bars=target_bars, instrument_id=target_id)
    data = pd.concat([ldf, rdf])["close"].unstack(0).sort_index().fillna(method="ffill")
    return data.dropna()


def human_readable_duration(ns: float):
    from dateutil.relativedelta import relativedelta  # type: ignore

    seconds = nanos_to_secs(ns)
    delta = relativedelta(seconds=seconds)
    attrs = ["months", "days", "hours", "minutes", "seconds"]
    return ", ".join(
        [
            f"{getattr(delta, attr)} {attr if getattr(delta, attr) > 1 else attr[:-1]}"
            for attr in attrs
            if getattr(delta, attr)
        ]
    )


class ModelUpdate(Data):
    def __init__(
        self,
        model: LinearRegression,
        hedge_ratio: float,
        std_prediction: float,
        ts_init: int,
    ):
        super().__init__(ts_init=ts_init, ts_event=ts_init)
        self.model = model
        self.hedge_ratio = hedge_ratio
        self.std_prediction = std_prediction


class Prediction(Data):
    def __init__(
        self,
        instrument_id: str,
        prediction: float,
        ts_init: int,
    ):
        super().__init__(ts_init=ts_init, ts_event=ts_init)
        self.instrument_id = instrument_id
        self.prediction = prediction
