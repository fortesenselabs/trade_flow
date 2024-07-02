import os
import re
import json
import inspect
from pathlib import Path
from dotenv import load_dotenv
from application.config import PACKAGE_ROOT
from application.logger import AppLogger
from application.models.app_model import AppConfig
from application.models.config_model import ConfigModel

# Load environment variables env vars AND from .env file
load_dotenv()

logger = AppLogger(name=__name__)

logger.info(f"PACKAGE_ROOT: {PACKAGE_ROOT}")

#
# Constant configuration parameters
#
DEFAULT_SETTINGS = {
    # Binance
    "api_key": "",
    "api_secret": "",
    # Telegram
    "telegram_bot_token": "",  # Source address of messages
    "telegram_chat_id": "",  # Destination address of messages
    #
    # Conventions for the file and column names
    #
    "merge_file_name": "data.csv",
    "feature_file_name": "features.csv",
    "matrix_file_name": "matrix.csv",
    "predict_file_name": "predictions.csv",  # predict, predict-rolling
    "signal_file_name": "signals.csv",
    "signal_models_file_name": "signal_models",
    "model_folder": "MODELS",
    "time_column": "timestamp",
    # File locations
    "data_folder": "C:/DATA_ITB",  # Location for all source and generated data/models
    # ==============================================
    # === DOWNLOADER, MERGER and (online) READER ===
    # Symbol determines sub-folder and used in other identifiers
    "symbol": "BTCUSDT",  # BTCUSDT ETHUSDT ^gspc
    # This parameter determines time raster (granularity) for the data
    # It is pandas frequency
    "freq": "1min",
    # This list is used for downloading and then merging data
    # "folder" is symbol name for downloading. prefix will be added column names during merge
    "data_sources": [],
    # ==========================
    # === FEATURE GENERATION ===
    # What columns to pass to which feature generator and how to prefix its derived features
    # Each executes one feature generation function applied to columns with the specified prefix
    "feature_sets": [],
    # ========================
    # === LABEL GENERATION ===
    "label_sets": [],
    # ===========================
    # === MODEL TRAIN/PREDICT ===
    #     predict off-line and on-line
    "label_horizon": 0,  # This number of tail rows will be excluded from model training
    "train_length": 0,  # train set maximum size. algorithms may decrease this length
    # List all features to be used for training/prediction by selecting them from the result of feature generation
    # The list of features can be found in the output of the feature generation (but not all must be used)
    # Currently the same feature set for all algorithms
    "train_features": [],
    # Labels to be used for training/prediction by all algorithms
    # List of available labels can be found in the output of the label generation (but not all must be used)
    "labels": [],
    # Algorithms and their configurations to be used for training/prediction
    "algorithms": [],
    # ===========================
    # ONLINE (PREDICTION) PARAMETERS
    # Minimum history length required to compute derived features
    "features_horizon": 10,
    # ===============
    # === SIGNALS ===
    "signal_sets": [],
    # =====================
    # === NOTIFICATIONS ===
    "score_notification_model": {},
    "diagram_notification_model": {},
    # ===============
    # === TRADING ===
    "trade_model": {
        "no_trades_only_data_processing": False,  # in market or out of market processing is excluded (all below parameters ignored)
        "test_order_before_submit": False,  # Send test submit to the server as part of validation
        "simulate_order_execution": False,  # Instead of real orders, simulate their execution (immediate buy/sell market orders and use high price of klines for limit orders)
        "percentage_used_for_trade": 99,  # in % to the available USDT quantity, that is, we will derive how much BTC to buy using this percentage
        "limit_price_adjustment": 0.005,  # Limit price of orders will be better than the latest close price (0 means no change, positive - better for us, negative - worse for us)
    },
    "train_signal_model": {},
    # =====================
    # === BINANCE TRADER ===
    "base_asset": "",  # BTC ETH
    "quote_asset": "",
    # ==================
    # === COLLECTORS ===
    "collector": {
        "folder": "DATA",
        "flush_period": 300,  # seconds
        "depth": {
            "folder": "DEPTH",
            "symbols": [
                "BTCUSDT",
                "ETHBTC",
                "ETHUSDT",
                "IOTAUSDT",
                "IOTABTC",
                "IOTAETH",
            ],
            "limit": 100,  # Legal values (depth): '5, 10, 20, 50, 100, 500, 1000, 5000' <100 weight=1
            "freq": "1min",  # Pandas frequency
        },
        "stream": {
            "folder": "STREAM",
            # Stream formats:
            # For kline channel: <symbol>@kline_<interval>, Event type: "e": "kline", Symbol: "s": "BNBBTC"
            # For depth channel: <symbol>@depth<levels>[@100ms], Event type: NO, Symbol: NO
            # btcusdt@ticker
            "channels": ["kline_1m", "depth20"],  # kline_1m, depth20, depth5
            "symbols": [
                "BTCUSDT",
                "ETHBTC",
                "ETHUSDT",
                "IOTAUSDT",
                "IOTABTC",
                "IOTAETH",
            ],
            # "BTCUSDT", "ETHBTC", "ETHUSDT", "IOTAUSDT", "IOTABTC", "IOTAETH"
        },
    },
}


class Settings:
    def __init__(self, config_file: str):
        self.config: ConfigModel = self.load_config(config_file)

    def _get_setting(self, key):
        value = os.environ.get(f"{key}")
        if not value:
            raise ValueError(f"Missing environment variable: {key}")
        return value

    def load_config(self, config_file) -> ConfigModel:
        if not config_file:
            raise ValueError("Empty config file variable")

        config_file_path = PACKAGE_ROOT / config_file
        with open(config_file_path, encoding="utf-8") as json_file:
            conf_str = json_file.read()

            # Remove everything starting with // and till the line end
            conf_str = re.sub(r"//.*$", "", conf_str, flags=re.M)

            conf_json = json.loads(conf_str)
            return ConfigModel(**conf_json)

    def model_dump(self):
        """Dumps all settings as a dictionary, excluding methods."""
        return {
            key: getattr(self.config, key)
            for key in dir(self.config)
            if not key.startswith("_")
            and not inspect.ismethod(getattr(self.config, key))
        }

    def get_app_config(self) -> AppConfig:
        return AppConfig(config=self.config)
