from decimal import Decimal
from typing import Any
from trade_flow.core.exceptions import InvalidTradingPair
from trade_flow.environments.metatrader.engine.instruments.quantity import Quantity
from trade_flow.environments.metatrader.terminal import Timeframe, SymbolInfo, retrieve_data

registry = {}

class TradingInstrument:
    """
    Represents a financial instrument for use in trading, including pairing capabilities
    to form trading symbols on a broker.

    Parameters
    ----------
    broker : `Broker`
        The broker listing the symbol for trading.
    base : `Instrument`
        The base instrument of the trading pair.
    quote : `Instrument`
        The quote instrument of the trading pair.
    symbol : str, optional
        The symbol for a single instrument (e.g., "AAPL", "BTC").
    precision : int, optional
        Precision for quoting amounts (e.g., 8 for BTC).
    name : str, optional
        Name of the instrument.

    Raises
    ------
    InvalidTradingPair
        Raised if base and quote instrument are identical.
    """

    def __init__(
        self,
        symbol: str,
        precision: int = 2,
        name: str = None,
        broker: "Broker" = None,
        base: "Symbol" = None,
        quote: "Symbol" = None,
    ) -> None:
        self.broker = broker
        self.base = base or self
        self.quote = quote
        self.symbol = symbol or (
            f"{self.base.symbol}/{self.quote.symbol}" if self.base and self.quote else None
        )
        self.precision = precision
        self.name = name

        if base and quote:
            if base == quote:
                raise InvalidTradingPair(base, quote)

        # Register only if a single instrument, not a trading pair.
        if symbol:
            registry[symbol] = self

    @property
    def price(self) -> Decimal:
        """Quoted price of the symbol. (`Decimal`, read-only)"""
        if self.broker:
            return self.broker.quote_price(self)
        raise ValueError("Price not available without broker association.")

    @property
    def inverse_price(self) -> Decimal:
        """The inverse price of the symbol. (`Decimal`, read-only)"""
        quantization = Decimal(10) ** -self.precision
        return Decimal(1 / self.price).quantize(quantization)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, TradingInstrument):
            return False
        if self.base and self.quote:  # For trading pairs
            return self.base == other.base and self.quote == other.quote
        # For single instruments
        return (
            self.symbol == other.symbol
            and self.precision == other.precision
            and self.name == other.name
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __rmul__(self, other: float) -> "Quantity":
        """Enables reverse multiplication for creating a quantity."""
        return Quantity(instrument=self, size=other)

    def __truediv__(self, other: "TradingInstrument") -> "TradingInstrument":
        """Creates a trading pair if two instruments are divided."""
        if isinstance(other, TradingInstrument):
            return TradingInstrument(self.broker, self, other)
        raise ValueError(f"Invalid trading pair: {other} is not a valid instrument.")

    def __hash__(self) -> int:
        return hash((self.symbol, self.base, self.quote))

    def __str__(self) -> str:
        if self.base and self.quote:
            return f"{self.broker.name}:{self.base.symbol}/{self.quote.symbol}"
        return self.symbol

    def __repr__(self) -> str:
        return str(self)


# FX
USD = TradingInstrument("USD", 4, "U.S. Dollar")
EUR = TradingInstrument("EUR", 4, "Euro")
GBP = TradingInstrument("GBP", 4, "British Pound")
JPY = TradingInstrument("JPY", 4, "Japanese Yen")
AUD = TradingInstrument("AUD", 4, "Australian Dollar")
AUD = TradingInstrument("CAD", 4, "Canadian Dollar")

# Commodities
XAU = TradingInstrument("XAU", 2, "Gold")
XAG = TradingInstrument("XAG", 2, "Silver")

# Stocks
AAPL = TradingInstrument("AAPL", 2, "Apple")
MSFT = TradingInstrument("MSFT", 2, "Microsoft")
