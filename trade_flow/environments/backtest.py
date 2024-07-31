from environments import BaseEnvironment
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.engine import BacktestEngineConfig
from flow import ExchangeManager

def cli_help():
    return "Backtest Environment"

class BacktestEnvironment(BaseEnvironment):
    def __init__(self, mode: str, exchange_manager: ExchangeManager, config: BacktestEngineConfig) -> None:
        super().__init__(self, mode, exchange_manager)
        self.engine = BacktestEngine(config=config)  # Initialize with actual BacktestEngine configuration or setup

    def reset(self):
        """
        Reset the backtest environment.
        """
        if self.engine:
            return self.engine.reset()
        else:
            raise RuntimeError("Engine not initialized.")

    def step(self, action):
        """
        Take a step in the backtest environment.

        Args:
        - action: Action to take
        """
        if self.engine:
            observation, reward, done, info = self.engine.step(action)
            return observation, reward, done, info
        else:
            raise RuntimeError("Engine not initialized.")

    def render(self, mode="human"):
        """
        Render the backtest environment.

        Args:
        - mode (str): Rendering mode
        """
        if self.engine:
            return self.engine.run()
        else:
            raise RuntimeError("Engine not initialized.")

    def close(self):
        """
        Close the backtest environment.
        """
        if self.engine:
            self.engine.dispose()
        else:
            raise RuntimeError("Engine not initialized.")