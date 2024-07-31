from enum import Enum
import gymnasium as gym

# from nautilus_trader.core.enums import TradingState  # confirm this import

# define training, testing and live environments



class BaseEnvironment:
    def __init__(
        self,
        env_type: TradingEnvironment,
        trading_state: TradingState = TradingState.IDLE,
    ) -> None:
        """
        Initialize the base environment.

        Args:
        - env_type (str): Type of environment (live, backtest, sandbox, gym)
        - trading_state (TradingState): Initial trading state
        """
        self.env_type = env_type
        self.trading_state = trading_state
        self.gym_env = None

    def reset(self):
        """
        Reset the environment.
        """
        if self.env_type == "gym":
            self.gym_env.reset()

    def step(self, action):
        """
        Take a step in the environment.

        Args:
        - action: Action to take
        """
        if self.env_type == "gym":
            return self.gym_env.step(action)

    def render(self, mode="human"):
        """
        Render the environment.

        Args:
        - mode (str): Rendering mode
        """
        if self.env_type == "gym":
            self.gym_env.render(mode)

    def close(self):
        """
        Close the environment.
        """
        if self.env_type == "gym":
            self.gym_env.close()

    def get_trading_environment(self):
        """
        Get the Trader environment.

        Returns:
        - TradingEnvironment: Trader environment
        """
        if self.env_type == "live":
            return TradingEnvironment.LIVE
        elif self.env_type == "backtest":
            return TradingEnvironment.BACKTEST
        elif self.env_type == "sandbox":
            return TradingEnvironment.SANDBOX
        else:
            return None
