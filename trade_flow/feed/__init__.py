import os
import pandas as pd
from . import generic
from . import float
from . import boolean
from . import string

from trade_flow.feed.base import Stream, NameSpace
from trade_flow.feed.feed import DataFeed
from trade_flow.feed.operators import Apply

# from .utils import load_dataset as _load_dataset


def _load_dataset(name, index_name):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "data", name + ".csv")
    df = pd.read_csv(path, parse_dates=True, index_col=index_name)
    return df


# Load FOREX datasets
FOREX_EURUSD_1H_ASK = _load_dataset("FOREX_EURUSD_1H_ASK", "Time")

# Load Stocks datasets
STOCKS_GOOGL = _load_dataset("STOCKS_GOOGL", "Date")
