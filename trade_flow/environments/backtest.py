# backtest
# - train
# - test
from trade_flow.environments.environment import BaseEnvironment
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.engine import BacktestEngineConfig
from trade_flow.flow import DataManager


class BacktestEnvironment(BacktestEngine):
    def __init__(self, mode: str, config_path: str) -> None:
        super().__init__()
        self.mode = mode
        self.config_path = config_path
        self.engine = None
