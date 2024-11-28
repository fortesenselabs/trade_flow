from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import pandas as pd
import os
import joblib
from datetime import datetime, timedelta

from trade_flow.environments.metatrader.terminal import Timeframe, SymbolInfo, retrieve_data
from trade_flow.environments.metatrader.engine.orders import OrderType, Order
from trade_flow.environments.metatrader.engine.exceptions import SymbolNotFound, OrderNotFound


class Simulator:
    """
    A financial trading simulator to manage and simulate orders, symbols data,
    and account balance using historical price data.

    Attributes:
    ----------
    unit: str
        Currency unit of the account (default: USD)
    balance: float
        Initial balance of the account
    leverage: float
        Leverage applied to the account
    stop_out_level: float
        The minimum margin level before stopping out orders
    hedge: bool
        Whether hedging is allowed (default: True)
    symbols_filename: Optional[str]
        Filename to load/save symbol information and data

    Methods:
    -------
    download_data(symbols, time_range, timeframe)
        Downloads symbol data for given time range and timeframe.
    save_symbols(filename)
        Saves symbols information and data to a file.
    load_symbols(filename)
        Loads symbols information and data from a file.
    tick(delta_time)
        Simulates a time tick to update orders and account status.
    create_order(order_type, symbol, volume, fee, raise_exception)
        Creates a new order, hedged or unhedged based on the hedge attribute.
    close_order(order)
        Closes the specified order.
    get_state()
        Returns the current state of the simulator.
    """

    def __init__(
        self,
        unit: str = "USD",
        balance: float = 10000.0,
        leverage: float = 100.0,
        stop_out_level: float = 0.2,
        hedge: bool = True,
        symbols_filename: Optional[str] = None,
    ) -> None:
        self.unit = unit
        self.balance = balance
        self.equity = balance
        self.leverage = leverage
        self.stop_out_level = stop_out_level
        self.hedge = hedge
        self.symbols_filename = symbols_filename
        self.margin = 0.0

        self.symbols_info: Dict[str, SymbolInfo] = {}
        self.symbols_data: Dict[str, pd.DataFrame] = {}
        self.orders: List[Order] = []
        self.closed_orders: List[Order] = []
        self.current_time: datetime = NotImplemented

        if symbols_filename:
            if not self.load_symbols(symbols_filename):
                raise FileNotFoundError(f"file '{symbols_filename}' not found")

    @property
    def free_margin(self) -> float:
        return self.equity - self.margin

    @property
    def margin_level(self) -> float:
        margin = round(self.margin, 6)
        if margin == 0.0:
            return float("inf")
        return self.equity / margin

    def download_data(
        self, symbols: List[str], time_range: Tuple[datetime, datetime], timeframe: Timeframe
    ) -> None:
        """
        Downloads and stores data for the provided symbols within a time range and timeframe.

        Parameters:
        ----------
        symbols : List[str]
            A list of symbol names to download data for.
        time_range : Tuple[datetime, datetime]
            A tuple containing the start and end datetime for the data range.
        timeframe : Timeframe
            The timeframe to retrieve data for.
        """
        from_dt, to_dt = time_range
        for symbol in symbols:
            si, df = retrieve_data(symbol, from_dt, to_dt, timeframe)
            self.symbols_info[symbol] = si
            self.symbols_data[symbol] = df

    def save_symbols(self, filename: str) -> None:
        """
        Saves the current symbol information and data to a file using joblib.
        """
        with open(filename, "wb") as file:
            joblib.dump((self.symbols_info, self.symbols_data), file)

    def load_symbols(self, filename: str) -> bool:
        """
        Loads symbol information and data from a file using joblib.

        Returns:
        -------
        bool
            True if the file exists and data is successfully loaded, False otherwise.
        """
        if not os.path.exists(filename):
            return False
        with open(filename, "rb") as file:
            self.symbols_info, self.symbols_data = joblib.load(file)
        return True

    def tick(self, delta_time: timedelta = timedelta()) -> None:
        """
        Simulates the passage of time and updates all open orders' status.

        Parameters:
        ----------
        delta_time : timedelta
            The time step to move forward by.
        """
        self._check_current_time()

        self.current_time += delta_time
        self.equity = self.balance

        for order in self.orders:
            order.exit_time = self.current_time
            order.exit_price = self.price_at(order.symbol, order.exit_time)["Close"]
            self._update_order_profit(order)
            self.equity += order.profit

        while self.margin_level < self.stop_out_level and len(self.orders) > 0:
            most_unprofitable_order = min(self.orders, key=lambda order: order.profit)
            self.close_order(most_unprofitable_order)

        if self.balance < 0.0:
            self.balance = 0.0
            self.equity = self.balance

    def nearest_time(self, symbol: str, time: datetime) -> datetime:
        """
        Finds the nearest available time for a symbol's data.

        Parameters:
        ----------
        symbol : str
            The symbol to check.
        time : datetime
            The time to match.

        Returns:
        -------
        datetime
            The nearest available time in the symbol's data.
        """
        df = self.symbols_data[symbol]
        if time in df.index:
            return time
        try:
            (i,) = df.index.get_indexer([time], method="ffill")
        except KeyError:
            (i,) = df.index.get_indexer([time], method="bfill")
        return df.index[i]

    def price_at(self, symbol: str, time: datetime) -> pd.Series:
        """
        Retrieves the price data for a symbol at the nearest available time.

        Parameters:
        ----------
        symbol : str
            The symbol to retrieve the price for.
        time : datetime
            The time at which to get the price.

        Returns:
        -------
        pd.Series
            The price data for the symbol at the nearest time.
        """
        df = self.symbols_data.get(symbol)
        if df is None:
            raise ValueError(f"Symbol '{symbol}' not found in symbols data.")
        nearest_time = self.nearest_time(symbol, time)
        return df.loc[nearest_time]

    def symbol_orders(self, symbol: str) -> List[Order]:
        """
        Retrieves all orders associated with a specific symbol.

        Parameters:
        ----------
        symbol : str
            The symbol to filter orders by.

        Returns:
        -------
        List[Order]
            A list of orders associated with the specified symbol.
        """
        return [order for order in self.orders if order.symbol == symbol]

    def create_order(
        self,
        order_type: OrderType,
        symbol: str,
        volume: float,
        fee: float = 0.0005,
        raise_exception: bool = True,
    ) -> Optional[Order]:
        """
        Create a new order for a given symbol with specified parameters.

        Parameters:
        ----------
        order_type : OrderType
            The type of the order (buy/sell).
        symbol : str
            The symbol for the order.
        volume : float
            The volume for the order.
        fee : float, optional
            The fee for the order (default is 0.0005).
        raise_exception : bool, optional
            Whether to raise an exception on failure (default is True).

        Returns:
        -------
        Optional[Order]
            The created order or None if an exception is not raised.
        """
        self._check_current_time()
        self._check_volume(symbol, volume)

        if fee < 0.0:
            raise ValueError(f"Negative fee '{fee}' is not allowed.")

        return (
            self._create_hedged_order(order_type, symbol, volume, fee, raise_exception)
            if self.hedge
            else self._create_unhedged_order(order_type, symbol, volume, fee, raise_exception)
        )

    def _create_hedged_order(
        self, order_type: OrderType, symbol: str, volume: float, fee: float, raise_exception: bool
    ) -> Optional[Order]:
        """
        Create a hedged order.

        Parameters:
        ----------
        order_type : OrderType
            The type of the order (buy/sell).
        symbol : str
            The symbol for the order.
        volume : float
            The volume for the order.
        fee : float
            The fee for the order.
        raise_exception : bool
            Whether to raise an exception on failure.

        Returns:
        -------
        Optional[Order]
            The created order or None if an exception is not raised.
        """
        order_id = len(self.closed_orders) + len(self.orders) + 1
        entry_time = self.current_time
        entry_price = self.price_at(symbol, entry_time)["Close"]

        order = Order(
            order_id,
            order_type,
            symbol,
            volume,
            fee,
            entry_time,
            entry_price,
            entry_time,  # Exit time same as entry for hedged orders
            entry_price,  # Exit price same as entry for hedged orders
        )
        self._update_order_profit(order)
        self._update_order_margin(order)

        if order.margin > self.free_margin + order.profit:
            if raise_exception:
                raise ValueError(
                    f"Insufficient free margin (order margin={order.margin}, "
                    f"order profit={order.profit}, free margin={self.free_margin})"
                )
            return None

        self.equity += order.profit
        self.margin += order.margin
        self.orders.append(order)
        return order

    def _create_unhedged_order(
        self, order_type: OrderType, symbol: str, volume: float, fee: float, raise_exception: bool
    ) -> Optional[Order]:
        """
        Create an unhedged order or manage existing orders for the symbol.

        Parameters:
        ----------
        order_type : OrderType
            The type of the order (buy/sell).
        symbol : str
            The symbol for the order.
        volume : float
            The volume for the order.
        fee : float
            The fee for the order.
        raise_exception : bool
            Whether to raise an exception on failure.

        Returns:
        -------
        Optional[Order]
            The created or modified order or None if an exception is not raised.
        """
        if not any(order.symbol == symbol for order in self.orders):
            return self._create_hedged_order(order_type, symbol, volume, fee, raise_exception)

        old_order = self.symbol_orders(symbol)[0]

        if old_order.type == order_type:
            new_order = self._create_hedged_order(order_type, symbol, volume, fee, raise_exception)
            if new_order is None:
                return None

            entry_price_weighted_average = np.average(
                [old_order.entry_price, new_order.entry_price],
                weights=[old_order.volume, new_order.volume],
            )

            old_order.volume += new_order.volume
            old_order.profit += new_order.profit
            old_order.margin += new_order.margin
            old_order.entry_price = entry_price_weighted_average
            old_order.fee = max(old_order.fee, new_order.fee)

            return old_order

        # Manage volume when the order types differ
        if volume >= old_order.volume:
            self.close_order(old_order)
            if volume > old_order.volume:
                return self._create_hedged_order(order_type, symbol, volume - old_order.volume, fee)
            return old_order

        # Handling partial volumes
        partial_profit = (volume / old_order.volume) * old_order.profit
        partial_margin = (volume / old_order.volume) * old_order.margin

        old_order.volume -= volume
        old_order.profit -= partial_profit
        old_order.margin -= partial_margin

        self.balance += partial_profit
        self.margin -= partial_margin

        return old_order

    def close_order(self, order: Order) -> float:
        """
        Close an existing order and update the balance and equity.

        Parameters:
        ----------
        order : Order
            The order to close.

        Returns:
        -------
        float
            The profit from closing the order.

        Raises:
        -------
        OrderNotFound
            If the order is not found in the order list.
        """
        self._check_current_time()
        if order not in self.orders:
            raise OrderNotFound("Order not found in the order list.")

        order.exit_time = self.current_time
        order.exit_price = self.price_at(order.symbol, order.exit_time)["Close"]
        self._update_order_profit(order)

        self.balance += order.profit
        self.margin -= order.margin

        order.exit_balance = self.balance
        order.exit_equity = self.equity
        order.closed = True

        self.orders.remove(order)
        self.closed_orders.append(order)

        return order.profit

    def get_state(self) -> Dict[str, Any]:
        """
        Retrieve the current state of the trading system.

        Returns:
        -------
        Dict[str, Any]
            A dictionary containing the current time, balance, equity, margin,
            free margin, margin level, and a DataFrame of orders.
        """
        orders = [
            {
                "Id": order.id,
                "Symbol": order.symbol,
                "Type": order.type.name,
                "Volume": order.volume,
                "Entry Time": order.entry_time,
                "Entry Price": order.entry_price,
                "Exit Time": order.exit_time,
                "Exit Price": order.exit_price,
                "Exit Balance": order.exit_balance,
                "Exit Equity": order.exit_equity,
                "Profit": order.profit,
                "Margin": order.margin,
                "Fee": order.fee,
                "Closed": order.closed,
            }
            for order in reversed(self.closed_orders + self.orders)
        ]

        return {
            "current_time": self.current_time,
            "balance": self.balance,
            "equity": self.equity,
            "margin": self.margin,
            "free_margin": self.free_margin,
            "margin_level": self.margin_level,
            "orders": pd.DataFrame(orders),
        }

    def _update_order_profit(self, order: Order) -> None:
        """
        Update the profit for a given order based on exit price and fees.

        Parameters:
        ----------
        order : Order
            The order to update profit for.
        """
        diff = order.exit_price - order.entry_price
        v = order.volume * self.symbols_info[order.symbol].trade_contract_size
        local_profit = v * (order.type.sign * diff - order.fee)
        order.profit = local_profit * self._get_unit_ratio(order.symbol, order.exit_time)

    def _update_order_margin(self, order: Order) -> None:
        """
        Update the margin for a given order based on entry price and leverage.

        Parameters:
        ----------
        order : Order
            The order to update margin for.
        """
        v = order.volume * self.symbols_info[order.symbol].trade_contract_size
        local_margin = (v * order.entry_price) / self.leverage
        local_margin *= self.symbols_info[order.symbol].margin_rate
        order.margin = local_margin * self._get_unit_ratio(order.symbol, order.entry_time)

    def _get_unit_ratio(self, symbol: str, time: datetime) -> float:
        """
        Get the unit ratio for converting between currencies.

        Parameters:
        ----------
        symbol : str
            The symbol to get the ratio for.
        time : datetime
            The time for price lookup.

        Returns:
        -------
        float
            The conversion ratio.
        """
        symbol_info = self.symbols_info[symbol]

        if self.unit == symbol_info.currency_profit:
            return 1.0

        if self.unit == symbol_info.currency_margin:
            return 1 / self.price_at(symbol, time)["Close"]

        unit_symbol_info = self._get_unit_symbol_info(symbol_info.currency_profit)
        if unit_symbol_info is None:
            raise SymbolNotFound(f"Unit symbol for '{symbol_info.currency_profit}' not found.")

        unit_price = self.price_at(unit_symbol_info.name, time)["Close"]
        if unit_symbol_info.currency_margin == self.unit:
            unit_price = 1.0 / unit_price

        return unit_price

    def _get_unit_symbol_info(self, currency: str) -> Optional[SymbolInfo]:
        """
        Get the symbol info for a currency.

        Parameters:
        ----------
        currency : str
            The currency to find the symbol info for.

        Returns:
        -------
        Optional[SymbolInfo]
            The symbol info or None if not found.
        """
        for info in self.symbols_info.values():
            if currency in info.currencies and self.unit in info.currencies:
                return info
        return None

    def _check_current_time(self) -> None:
        """
        Check if the current time is set.

        Raises:
        -------
        ValueError
            If 'current_time' is not set.
        """
        if self.current_time is None:
            raise ValueError("'current_time' must have a valid value.")

    def _check_volume(self, symbol: str, volume: float) -> None:
        """
        Validate the volume for a given symbol.

        Parameters:
        ----------
        symbol : str
            The symbol to validate volume against.
        volume : float
            The volume to validate.

        Raises:
        -------
        ValueError
            If volume is outside of allowed range or not a multiple of volume step.
        """
        symbol_info = self.symbols_info[symbol]

        if not (symbol_info.volume_min <= volume <= symbol_info.volume_max):
            raise ValueError(
                f"'volume' must be in range [{symbol_info.volume_min}, {symbol_info.volume_max}]"
            )

        if not round(volume / symbol_info.volume_step, 6).is_integer():
            raise ValueError(f"'volume' must be a multiple of {symbol_info.volume_step}.")
