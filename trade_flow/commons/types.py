from enum import Enum


class EnvironmentMode(Enum):
    LIVE = "live"
    SANDBOX = "sandbox"
    BACKTEST = "backtest"
    TRAIN = "train"

class AssetClass(Enum):
    FOREX = "forex"
    EQUITY = "equity"
    COMMODITY = "commodity"
    DEBT = "debt"
    INDEX = "index"
    CRYPTOCURRENCY = "cryptocurrency"
    ALTERNATIVE = "alternative"

class TradingState(Enum):
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"


class RunningStatus(Enum):
    PENDING = 1
    RUNNING = 2
    STOPPED = 3
    FAILED = 4
    UNKNOWN = 5
