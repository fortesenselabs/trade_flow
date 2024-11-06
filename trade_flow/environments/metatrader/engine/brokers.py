from datetime import datetime
import os
from typing import Callable, Dict, List, Optional, Tuple
from decimal import Decimal
import joblib
import pandas as pd

from trade_flow.core import Component, TimedIdentifiable
from trade_flow.environments.generic.portfolio import Portfolio
from trade_flow.environments.metatrader.engine.instruments import Symbol
from trade_flow.environments.metatrader.terminal import retrieve_data, Timeframe, SymbolInfo
from trade_flow.feed import Stream


class BrokerOptions:
    """
    Options for configuring a broker in the trading environment.

    Parameters
    ----------
    unit: str, default "USD"
        Currency unit of the account.
    balance: float, default 10000.0
        Initial account balance.
    leverage: float, default 100.0
        Leverage ratio for account.
    stop_out_level: float, default 0.2
        Minimum margin level before triggering stop-out.
    hedge: bool, default True
        Enable or disable hedging on account.
    commission: float, default 0.003
        Commission percentage applied to orders.
    min_trade_size: float, default 1e-3
        Minimum allowed trade size.
    max_trade_size: float, default 1e2
        Maximum allowed trade size.
    min_trade_price: float, default 1e-1
        Minimum allowed trade price.
    max_trade_price: float, default 1e6
        Maximum allowed trade price.
    is_live: bool, default False
        Set to True for live trading.
    symbols_filename: Optional[str]
        Filename to load/save symbol information.
    """

    def __init__(
        self,
        unit: str = "USD",
        balance: float = 10000.0,
        leverage: float = 100.0,
        stop_out_level: float = 0.2,
        hedge: bool = True,
        commission: float = 0.003,
        min_trade_size: float = 1e-3,
        max_trade_size: float = 1e2,
        min_trade_price: float = 1e-1,
        max_trade_price: float = 1e6,
        is_live: bool = False,
        symbols_filename: Optional[str] = None,
    ):
        self.unit = unit
        self.balance = balance
        self.equity = balance
        self.leverage = leverage
        self.stop_out_level = stop_out_level
        self.hedge = hedge
        self.margin = 0.0
        self.commission = commission
        self.min_trade_size = min_trade_size
        self.max_trade_size = max_trade_size
        self.min_trade_price = min_trade_price
        self.max_trade_price = max_trade_price
        self.is_live = is_live
        self.symbols_filename = symbols_filename

        self.symbols_info: Dict[str, SymbolInfo] = {}
        self.symbols_data: Dict[str, pd.DataFrame] = {}

        if symbols_filename:
            if not self.load_symbols(symbols_filename):
                raise FileNotFoundError(f"File '{symbols_filename}' not found")

    @property
    def free_margin(self) -> float:
        return self.equity - self.margin

    @property
    def margin_level(self) -> float:
        return float("inf") if self.margin == 0 else self.equity / self.margin

    def download_data(
        self, symbols: List[str], time_range: Tuple[datetime, datetime], timeframe: Timeframe
    ) -> None:
        """
        Download and store data for specified symbols over a time range and timeframe.

        Parameters
        ----------
        symbols : List[str]
            List of symbol names to download data for.
        time_range : Tuple[datetime, datetime]
            Start and end datetime for the data range.
        timeframe : Timeframe
            Timeframe for the data.
        """
        for symbol in symbols:
            si, df = retrieve_data(symbol, *time_range, timeframe)
            self.symbols_info[symbol] = si
            self.symbols_data[symbol] = df

    def save_symbols(self, filename: str) -> None:
        """Save symbol information and data to a file."""
        with open(filename, "wb") as file:
            joblib.dump((self.symbols_info, self.symbols_data), file)

    def load_symbols(self, filename: str) -> bool:
        """Load symbol information and data from a file.

        Returns
        -------
        bool
            True if file exists and data is loaded, False otherwise.
        """
        if not os.path.exists(filename):
            return False
        with open(filename, "rb") as file:
            self.symbols_info, self.symbols_data = joblib.load(file)
        return True


class Broker(Component, TimedIdentifiable):
    """
    Abstract broker within the MetaTrader trading environment.

    Parameters
    ----------
    name : str
        Broker's name.
    service : Callable
        Service for executing orders.
    options : BrokerOptions, optional
        Broker configuration settings.
    """

    registered_name = "brokers"

    def __init__(self, name: str, service: Callable, options: BrokerOptions = None):
        super().__init__()
        self.name = name
        self._service = service
        self.options = options or BrokerOptions()
        self._price_streams = {}

    def __call__(self, *streams) -> "Broker":
        """
        Set up price streams for price generation.

        Parameters
        ----------
        *streams : Stream
            Price streams to be associated with the broker.

        Returns
        -------
        Broker
            Broker instance with assigned price streams.
        """
        for s in streams:
            symbol_name = "".join([c if c.isalnum() else "/" for c in s.name])
            self._price_streams[symbol_name] = s.rename(f"{self.name}:/{s.name}")
        return self

    def streams(self) -> List["Stream[float]"]:
        """Return list of broker's price streams."""
        return list(self._price_streams.values())

    def quote_price(self, symbol: Symbol) -> Decimal:
        """
        Get the quote price for a symbol.

        Parameters
        ----------
        symbol : Symbol
            Symbol for which to get the quote price.

        Returns
        -------
        Decimal
            Quote price of the specified symbol.
        """
        price = Decimal(self._price_streams[str(symbol)].value)
        if price == 0:
            raise ValueError(f"Price for symbol {symbol} is 0. Check input data for valid prices.")

        price = price.quantize(Decimal(10) ** -symbol.precision)
        if price == 0:
            raise ValueError(
                f"Quantized price at symbol precision ({symbol.precision}) is 0 {symbol}. "
                "Consider using a higher-precision instrument."
            )

        return price

    def is_symbol_tradable(self, symbol: Symbol) -> bool:
        """
        Check if a symbol is tradable.

        Parameters
        ----------
        symbol : Symbol
            Symbol to check.

        Returns
        -------
        bool
            True if symbol is tradable, else False.
        """
        return str(symbol) in self._price_streams.keys()

    def execute_order(self, order: "Order", portfolio: Portfolio) -> None:
        """
        Execute an order on the broker.

        Parameters
        ----------
        order : Order
            Order to execute.
        portfolio : Portfolio
            Portfolio for order execution.
        """
        trade = self._service(
            order=order,
            account=portfolio.account(self.id, order.symbol),
            current_price=self.quote_price(order.symbol),
            options=self.options,
            clock=self.clock,
        )

        if trade:
            order.fill(trade)
