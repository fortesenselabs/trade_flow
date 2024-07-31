from commons import EnvironmentMode
from environments import LiveEnvironment, SandboxEnvironment, BacktestEnvironment, TrainingEnvironment
from venues import VenueManager


class EnvironmentManager:
    def __init__(self, mode: EnvironmentMode, venue_manager: VenueManager) -> None:
        self.mode = mode
        self.venue_manager = venue_manager

        self._init_environment()

    def _init_environment(self) -> None:
        if self.mode == EnvironmentMode.LIVE:
            self.selected_environment = LiveEnvironment(self.venue_manager)
        elif self.mode == EnvironmentMode.SANDBOX:
            self.selected_environment = SandboxEnvironment(self.venue_manager)
        elif self.mode == EnvironmentMode.BACKTEST:
            self.selected_environment = BacktestEnvironment(self.venue_manager)
        elif self.mode == EnvironmentMode.TRAIN:
            self.selected_environment = TrainingEnvironment(self.venue_manager)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")
        
        # config = EnvironmentConfig.from_file(self.config_path)
        # self.selected_environment.initialize(config)

    def get_portfolio(self):
        """
            returns things like:
            - wins, losses, max_loss, peak, etc
        """
        return
    
    def generate_positions_report(self):
        return
    
    def generate_order_fills_report(self):
        return
    
    def generate_account_report(self):
        return
    
    def place_order(self):
        return
    
    def close_order(self):
        return
    
    def dispose(self):
        return
    
    def reset(self):
        """
            Works for all environments except live(paper trading and real accounts) 
        """
        return