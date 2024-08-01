from typing import Optional
from environments import BaseEnvironment
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.engine import BacktestEngineConfig
from nautilus_trader.backtest.results import BacktestResult
from venues import VenueManager

def cli_help():
    return "Backtest Environment"

class BacktestEnvironment(BaseEnvironment):
    def __init__(self, venue_manager: VenueManager, config: Optional[BacktestEngineConfig] = None) -> None:
        super().__init__(self, venue_manager)
        self.engine = BacktestEngine(config=config) if config is not None else None # Initialize with actual BacktestEngine configuration or setup
        self.results = None

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
            # Runs one or many configs synchronously
            self.results: list[BacktestResult] = self.engine.run()
            return self.results
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
        
    