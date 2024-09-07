from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from trade_flow.core import AssetClass, AgentId


@dataclass
class Order:
    id: Optional[str] = None
    trader_id: AgentId


class DataProvider(ABC):
    @abstractmethod
    def add_data(self):
        pass

    @abstractmethod
    def get_instruments(self):
        pass

    @abstractmethod
    def get_account(self):
        pass

    @abstractmethod
    def request_tick(self):
        pass

    @abstractmethod
    def request_bar(self):
        pass

    @abstractmethod
    def request_historical_ticks(self):
        pass

    @abstractmethod
    def request_historical_bars(self):
        pass


class ExecutionProvider(ABC):
    @abstractmethod
    def execute_order(self, order):
        pass

    @abstractmethod
    def place_order(self, order):
        pass

    @abstractmethod
    def modify_order(self, order):
        pass

    @abstractmethod
    def get_orders(self, order: Order):
        pass

    @abstractmethod
    def get_portfolio(self):
        pass

    @abstractmethod
    def generate_positions_report(self):
        pass

    @abstractmethod
    def generate_order_fills_report(self):
        pass

    @abstractmethod
    def generate_account_report(self):
        pass

    @abstractmethod
    def place_order(self):
        pass

    @abstractmethod
    def close_order(self):
        pass


class Venue(DataProvider, ExecutionProvider):
    def __init__(
        self, venue_id: str = "Venue-01", asset_class: AssetClass = AssetClass.FOREX
    ) -> None:
        self.asset_class: AssetClass = asset_class
        self.venue_id: str = venue_id

        self.trader_id: TraderId = None

    def set_trader_id(self, id: str):
        self.trader_id = TraderId(id)
        return self.trader_id

    def add_data(self):
        """
        Implement data handling specific to Venue.
        """
        pass

    def place_order(self, order: Order):
        """
        Implement order execution specific to Venue.
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
