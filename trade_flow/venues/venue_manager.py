from typing import Optional
from nautilus_trader.model.identifiers import Venue, TraderId

class DataClient:
    pass

class ExecutionClient:
    pass

class VenueManager:
    def __init__(self) -> None:
        self.venue: Venue  = None
        self.trader_id: TraderId = None
        self.data_manager: Optional[DataClient] = None
        self.execution_manager: Optional[ExecutionClient] = None
    pass