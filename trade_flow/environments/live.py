from nautilus_trader.live.node import TradingNode
from nautilus_trader.config import TradingNodeConfig
from trade_flow.commons import TradingState
from trade_flow.venues import VenueManager
from trade_flow.environments.environment import BaseEnvironment

def cli_help():
    return "Live Environment"


class LiveEnvironment(BaseEnvironment):
    def __init__(self, venue_manager: VenueManager) -> None:
        super().__init__(venue_manager)
        self.engine = TradingNode()
