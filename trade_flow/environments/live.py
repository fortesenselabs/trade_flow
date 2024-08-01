from commons import TradingState
from environments import BaseEnvironment
from nautilus_trader.live.node import TradingNode
from nautilus_trader.config import TradingNodeConfig
from venues import VenueManager

def cli_help():
    return "Live Environment"


class LiveEnvironment(BaseEnvironment):
    def __init__(self, venue_manager: VenueManager) -> None:
        super().__init__(venue_manager)
        self.engine = TradingNode()
