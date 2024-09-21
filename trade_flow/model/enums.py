from enum import Enum, unique


@unique
class Environment(Enum):
    """
    Represents the environment context for a TradFlow system.
    """

    TRAIN = "train"
    BACKTEST = "backtest"
    SANDBOX = "sandbox"
    LIVE = "live"


class TradingState(Enum):
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"


class RunningStatus(Enum):
    PENDING = 1
    RUNNING = 2
    STOPPED = 3
    FAILED = 4
    UNKNOWN = 5
