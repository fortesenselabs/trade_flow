# TODO: Complete this module, there is suppose to be an abstract version of the Portfolio

from abc import ABC
from trade_flow.accounting.accounts.base import Account
from trade_flow.model.identifiers import InstrumentId
from trade_flow.model.identifiers import Venue
from trade_flow.model.objects import Money



class PortfolioFacade(ABC):
    """
    Provides a read-only facade for a `Portfolio`.
    """

    def account(self, venue: Venue) -> Account:
        """Abstract method (implement in subclass)."""
        raise NotImplementedError("method `account` must be implemented in the subclass")  

    def balances_locked(self, venue: Venue) -> dict:
        """Abstract method (implement in subclass)."""
        raise NotImplementedError("method `balances_locked` must be implemented in the subclass")  

    def margins_init(self, venue: Venue) -> dict:
        """Abstract method (implement in subclass)."""
        raise NotImplementedError("method `margins_init` must be implemented in the subclass")  

    def margins_maint(self, venue: Venue) -> dict:
        """Abstract method (implement in subclass)."""
        raise NotImplementedError("method `margins_maint` must be implemented in the subclass")  

    def unrealized_pnls(self, venue: Venue) -> dict:
        """Abstract method (implement in subclass)."""
        raise NotImplementedError("method `unrealized_pnls` must be implemented in the subclass")  

    def net_exposures(self, venue: Venue) -> dict:
        """Abstract method (implement in subclass)."""
        raise NotImplementedError("method `net_exposures` must be implemented in the subclass")  

    def unrealized_pnl(self, instrument_id: InstrumentId) -> Money:
        """Abstract method (implement in subclass)."""
        raise NotImplementedError("method `unrealized_pnl` must be implemented in the subclass")  

    def net_exposure(self, instrument_id: InstrumentId) -> Money:
        """Abstract method (implement in subclass)."""
        raise NotImplementedError("method `net_exposure` must be implemented in the subclass")  

    def net_position(self, instrument_id: InstrumentId) -> object:
        """Abstract method (implement in subclass)."""
        raise NotImplementedError("method `net_position` must be implemented in the subclass")  

    def is_net_long(self, instrument_id: InstrumentId) -> bool:
        """Abstract method (implement in subclass)."""
        raise NotImplementedError("method `is_net_long` must be implemented in the subclass")  

    def is_net_short(self, instrument_id: InstrumentId) -> bool:
        """Abstract method (implement in subclass)."""
        raise NotImplementedError("method `is_net_short` must be implemented in the subclass")  

    def is_flat(self, instrument_id: InstrumentId) -> bool:
        """Abstract method (implement in subclass)."""
        raise NotImplementedError("method `is_flat` must be implemented in the subclass")  

    def is_completely_flat(self) -> bool:
        """Abstract method (implement in subclass)."""
        raise NotImplementedError("method `is_completely_flat` must be implemented in the subclass")  
