from trade_flow.environments.generic import TradingEnvironment
from trade_flow.environments.generic import Venue


class SandboxEnvironment(TradingEnvironment):
    def __init__(self, venue: Venue) -> None:
        pass
