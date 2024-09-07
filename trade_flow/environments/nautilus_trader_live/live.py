from trade_flow.live.node import TradingNode
from trade_flow.config import TradingNodeConfig
from trade_flow.common import TradingState
from trade_flow.environments.generic import Venue, TradingEnvironment


class LiveEnvironment(TradingEnvironment):
    def __init__(self, venue: Venue) -> None:
        super().__init__(venue)
        self.engine = TradingNode()
