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
