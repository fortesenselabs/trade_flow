from typing import Optional
from commons import AssetClass
from nautilus_trader.model.identifiers import Venue, TraderId
from trade_flow.venues import BaseVenue

def cli_help():
    return "Metatrader Venue"

class DataClient:
    pass

class ExecutionClient:
    pass

class MetaTrader(BaseVenue):
    def __init__(self, venue_id: str ="MT-01") -> None:
        self.asset_classes: AssetClass = [AssetClass.FOREX, AssetClass.INDEX]
        self.venue: Venue  = Venue(venue_id)
    
        self.trader_id: TraderId = None
        self.data_client: Optional[DataClient] = None
        self.execution_client: Optional[ExecutionClient] = None
    
    def set_trader_id(self, id: str):
        self.trader_id = TraderId(id)
        return self.trader_id