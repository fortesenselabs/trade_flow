from enum import Enum


class EnvironmentMode(Enum):
    LIVE = "LIVE"
    SANDBOX = "SANDBOX"
    BACKTEST = "BACKTEST"
    TRAIN = "TRAIN"

class TradingState(Enum):
    IDLE = "IDLE"
