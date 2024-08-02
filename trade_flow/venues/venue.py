from typing import Optional
from trade_flow.commons import AssetClass
from nautilus_trader.model.identifiers import Venue, TraderId

class DataClient:
    pass

class ExecutionClient:
    pass

class BaseVenue:
    def __init__(self, venue_id: str ="Venue-01") -> None:
        self.asset_classes: AssetClass = [AssetClass.FOREX, AssetClass.INDEX]
        self.venue: Venue  = Venue(venue_id)
    
        self.trader_id: TraderId = None
        self.data_client: Optional[DataClient] = None
        self.execution_client: Optional[ExecutionClient] = None
    
    def set_trader_id(self, id: str):
        self.trader_id = TraderId(id)
        return self.trader_id
    
    def add_data(self):
        """
        Method to add data to the venue, if necessary.
        """
        pass

    def reset(self):
        """
        Reset the venue.
        """
        pass
    
    def close(self):
        """
        Close the venue.
        """
        pass
    