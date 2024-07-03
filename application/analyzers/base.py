import queue
from typing import Dict, List
from pathlib import Path
from application.database import load_models, load_last_transaction
from application.models import ConfigModel


class BaseAnalyzer:
    """
    Generic base class for analyzers that handle in-memory database representing the state of the environment.
    """

    def __init__(self, config: ConfigModel):
        """
        Initialize the analyzer with the given configuration.
        """
        self.config = config

        #
        # Data state
        #

        # Klines are stored as a dict of lists. Key is a symbol and the list is a list of latest kline records
        # One kline record is a list of values (not dict) as returned by API: open time, open, high, low, close, volume etc.
        self.klines = {}

        self.queue = queue.Queue()

        #
        # Load models
        #
        symbol = config.symbol
        data_path = Path(config.data_folder) / symbol

        model_path = Path(config.models_folder)
        if not model_path.is_absolute():
            model_path = data_path / model_path
        model_path = model_path.resolve()

        labels = config.labels
        algorithms = config.algorithms
        self.models = self.load_models(model_path, labels, algorithms)

        # Load latest transaction and (simulated) trade state
        self.transaction = None

    def get_last_transaction(self, transaction_file: Path):
        self.transaction = load_last_transaction(transaction_file)
        return self.transaction

    def load_models(self, model_path, labels: list, algorithms: list):
        """
        Load models based on the configuration.
        """
        return load_models(model_path, labels, algorithms)

    def get_klines_count(self, symbol: str) -> int:
        """
        Get the number of klines for the given symbol.
        """
        raise NotImplementedError()

    def get_last_kline(self, symbol: str) -> List:
        """
        Get the last kline for the given symbol.
        """
        raise NotImplementedError()

    def get_last_kline_ts(self, symbol: str) -> int:
        """
        Get the timestamp of the last kline for the given symbol.
        """
        raise NotImplementedError()

    def get_missing_klines_count(self, symbol: str) -> int:
        """
        Get the number of missing klines for the given symbol.
        """
        raise NotImplementedError()

    def store_klines(self, data: Dict[str, List]):
        """
        Store the latest klines for the specified symbols.
        """
        raise NotImplementedError()

    def analyze(self, ignore_last_rows=False):
        """
        Analyze the data and generate features, predictions, and signals.
        """
        raise NotImplementedError()

    def collect_klines(self, freq: str):
        """
        Collect klines at the specified frequency.
        """
        raise NotImplementedError()
