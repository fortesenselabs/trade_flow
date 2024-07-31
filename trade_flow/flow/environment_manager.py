from trade_flow.commons import EnvironmentMode
from trade_flow.environments import LiveEnvironment, SandboxEnvironment, BacktestEnvironment, TrainingEnvironment
from trade_flow.flow import DataManager


class EnvironmentManager:
    def __init__(self, mode: EnvironmentMode, data_manager: DataManager) -> None:
        self.mode = mode
        self.data_manager = data_manager

    def _init_environment(self) -> None:
        if self.mode == EnvironmentMode.LIVE:
            self.engine = LiveEnvironment(self.data_manager)
        elif self.mode == EnvironmentMode.SANDBOX:
            self.engine = SandboxEnvironment(self.data_manager)
        elif self.mode == EnvironmentMode.BACKTEST:
            self.engine = BacktestEnvironment(self.data_manager)
        elif self.mode == EnvironmentMode.TRAIN:
            self.engine = TrainingEnvironment(self.data_manager)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")
        
        # config = EnvironmentConfig.from_file(self.config_path)
        # self.engine.initialize(config)