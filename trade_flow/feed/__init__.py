from .generic import *
from .float import *
from .boolean import *
from .string import *

from .base import Stream, NameSpace
from .feed import DataFeed
from .operators import Apply
from .cdd import *

# from .utils import load_dataset as _load_dataset
import os
import pandas as pd


def _load_dataset(name, index_name):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "data", name + ".csv")
    df = pd.read_csv(path, parse_dates=True, index_col=index_name)
    return df


# Load FOREX datasets
FOREX_EURUSD_1H_ASK = _load_dataset("FOREX_EURUSD_1H_ASK", "Time")

# Load Stocks datasets
STOCKS_GOOGL = _load_dataset("STOCKS_GOOGL", "Date")

# Load Crypto datasets
Coinbase_BTCUSD_1h = _load_dataset("Coinbase_BTCUSD_1h", "date")
Coinbase_BTCUSD_d = _load_dataset("Coinbase_BTCUSD_d", "date")
