from typing import Optional
from trade_flow.commons import AssetClass
from nautilus_trader.model.identifiers import Venue, TraderId

class VenueManager:
    def __init__(self, venue_id: str ="Venue-01", asset_class: AssetClass = AssetClass.FOREX) -> None:
        self.asset_class = asset_class
        self.venue: Venue  = Venue(venue_id)
        self.trader_id: TraderId = None
    
    def set_trader_id(self, id: str):
        self.trader_id = TraderId(id)
        return self.trader_id