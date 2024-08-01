from commons import TradingState
from venues import VenueManager


class BaseEnvironment:
    def __init__(self, venue_manager: VenueManager) -> None:
        """
        Initialize the base environment.

        Args:
        - venue_manager (VenueManager): Manager for handling venue-specific data and operations
        """
        self.trading_state: TradingState = TradingState.IDLE
        self.venue_manager = venue_manager
        self.engine = None  # Initialize or replace with actual trading engine

    def add_data(self):
        """
        Method to add data to the environment, if necessary.
        """
        pass
    
    def reset(self):
        """
        Reset the environment.
        """
        pass

    def step(self, action):
        """
        Take a step in the environment.

        Args:
        - action: Action to take
        """
        pass

    def render(self, mode="human"):
        """
        Render the environment.

        Args:
        - mode (str): Rendering mode
        """
        pass

    def close(self):
        """
        Close the environment.
        """
        pass

    def get_trading_state(self):
        """
        Get the current trading state.
        
        Returns:
        - TradingState: Current state of the trading environment
        """
        return self.trading_state
    
    def set_trading_state(self, state: TradingState = TradingState.IDLE):
        """
        Set the trading state.

        Args:
        - state (TradingState): New trading state

        Returns:
        - TradingState: Updated trading state
        """
        self.trading_state = state
        return self.trading_state

