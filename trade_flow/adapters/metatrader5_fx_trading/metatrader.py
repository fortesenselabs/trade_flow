from typing import Optional
from trade_flow.core import AssetClass, AgentId
from trade_flow.environments.generic import Venue


class MetaTrader5(Venue):
    def __init__(self, venue_id: str = "MT5-01", asset_class: AssetClass = AssetClass.CFD) -> None:
        super().__init__(venue_id, asset_class)

    def set_trader_id(self, id: str):
        self.trader_id = AgentId(id)
        return self.trader_id
