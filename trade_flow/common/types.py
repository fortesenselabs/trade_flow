from enum import Enum


class EnvironmentMode(Enum):
    LIVE = "live"
    SANDBOX = "sandbox"
    BACKTEST = "backtest"
    TRAIN = "train"


class TradingState(Enum):
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"


class RunningStatus(Enum):
    PENDING = 1
    RUNNING = 2
    STOPPED = 3
    FAILED = 4
    UNKNOWN = 5
