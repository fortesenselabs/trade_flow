import asyncio
import logging
import random
import time
import pandas as pd
from datetime import datetime
from typing import Dict, Optional
from packages.itbot.itbot import Signal
from packages.itbot.itbot.portfolio import RiskManager
from trade_flow.common.logging import Logger
from packages.mt5any import (
    DockerizedMT5TerminalConfig,
    DockerizedMT5Terminal,
)
from packages.mt5any import MetaTrader5 as mt5


SymbolInfo = object


class MT5TraderException(Exception):
    """Base exception class for MT5Trader errors."""

    pass


class MT5TraderInitializationError(MT5TraderException):
    """Raised when there is an error initializing MT5 Trader."""

    pass


class MT5Trader:
    """
    A class to interface with MetaTrader 5 for trading operations using Dockerized MT5 Terminals.

    Attributes:
        mt5_account_number (str): The MetaTrader 5 account number.
        mt5_password (str): The password for the MT5 account.
        mt5_server (str): The MT5 server name.
        logger (Logger): Logger instance for logging events.
        mt5_terminal (DockerizedMT5Terminal): Dockerized MT5 Terminal instance.
        mt5 (MetaTrader5): MetaTrader 5 client interface.
        initial_balance (float): The initial account balance.
    """

    def __init__(
        self,
        account_number: str,
        password: str,
        server: str,
        logger: Optional[Logger] = None,
    ) -> None:
        """
        Initialize the MT5Trader class with account credentials and configurations.

        Args:
            account_number (str): MetaTrader 5 account number.
            password (str): MetaTrader 5 account password.
            server (str): MetaTrader 5 server.
            logger (Optional[Logger]): Logger instance for logging.
        """
        self.mt5_account_number = account_number
        self.mt5_password = password
        self.mt5_server = server

        # Set up logging
        self.logger = logger or Logger(name="it_bot", log_level=logging.DEBUG, filename="ITBot.log")

        # Set up MetaTrader 5 terminal and configuration
        self.mt5_config = DockerizedMT5TerminalConfig(
            account_number=self.mt5_account_number,
            password=self.mt5_password,
            server=self.mt5_server,
            read_only_api=True,
        )

        # Initialize Dockerized MT5 Terminal
        self.mt5_terminal = DockerizedMT5Terminal(config=self.mt5_config)
        self._initialize_terminal()

        # Initialize MetaTrader 5
        self.mt5 = mt5()
        self._initialize_mt5()
        self.logger.debug(f"Terminal Info: {self.mt5.terminal_info()._asdict()}")

        # Get account information
        self.account_info = self.mt5.account_info()._asdict()
        self.logger.debug(f"Account Info: {self.account_info}")

        self.initial_balance = self.account_info["balance"]

        # Log account info
        self.logger.info(f"Account Balance: {self.initial_balance}")
        self.logger.info(f"Equity: {self.account_info['equity']}")
        self.logger.info(f"Currency: {self.account_info['currency']}")
        self.logger.info(f"Margin: {self.account_info['margin']}")
        self.logger.info(f"Server: {self.account_info['server']}")
        self.logger.info(f"Name: {self.account_info['name']}")

    def _initialize_terminal(self) -> None:
        """Initialize and safely start the Dockerized MT5 Terminal."""
        try:
            self.mt5_terminal.safe_start()
            time.sleep(5)

            self.logger.info(f"MetaTrader 5 Terminal started for account {self.mt5_account_number}")
        except Exception as e:
            self.logger.error(f"Error initializing Dockerized MT5 Terminal: {e}")
            raise MT5TraderInitializationError("Failed to start Dockerized MT5 Terminal")

    def _initialize_mt5(self) -> None:
        """Initialize the MetaTrader 5 client."""
        try:
            if not self.mt5.initialize():
                raise RuntimeError("MetaTrader 5 initialization failed")

            # if not self.mt5.login(self.mt5_account_number, self.mt5_password, self.mt5_server):
            #     raise RuntimeError("MetaTrader 5 login failed")
        except Exception as e:
            self.logger.error(f"Error initializing MetaTrader 5: {e}")
            raise MT5TraderInitializationError("Failed to initialize MetaTrader 5")

    def round_2_tick_size(self, price: float, trade_tick_size: float) -> float:
        """
        Rounds the given price to the nearest multiple of the trade tick size.

        Parameters:
        ----------
        price : float
            The price that needs to be rounded.
        trade_tick_size : float
            The tick size (minimum price movement) for the asset.

        Returns:
        -------
        float
            The price rounded to the nearest multiple of the trade tick size.
        """
        return round(price / trade_tick_size) * trade_tick_size

    async def _prepare_trade_request(
        self,
        symbol: str,
        trade_type: str,
        position_size: float,
        close_trade: bool = False,
        **kwargs,
    ) -> Dict:
        """
        Prepare a trade request based on the given symbol, trade type, and position size.

        Parameters:
        ----------
        symbol : str
            The trading symbol (e.g., 'EURUSD') for which the trade is being placed.
        trade_type : str
            The type of trade to be executed, either "BUY" or "SELL".
        position_size : float
            The volume of the position (lot size) to trade.
        close_trade : bool, optional
            Whether the trade is a close trade (default is False).
        **kwargs : dict
            Additional optional arguments, including:
            - position_id : int, required for closing trades.
            - magic : int, an optional custom identifier for the trade (default is 0).

        Returns:
        -------
        Dict
            A dictionary containing the trade request details to be sent to MetaTrader 5.

        Raises:
        -------
        ValueError
            If position_id is required for closing a trade and is not provided.
        """

        # Fetch symbol info and validate
        symbol_info = self.mt5.symbol_info(symbol)
        if not symbol_info:
            raise ValueError(f"Symbol info for {symbol} not available")

        # Validate the position size
        position_size = await self.validate_position_size(symbol_info, position_size)

        # Get necessary symbol info and pricing data
        filling_mode = symbol_info.filling_mode - 1
        tick_data = self.mt5.symbol_info_tick(symbol)
        ask_price = tick_data.ask
        bid_price = tick_data.bid
        point = symbol_info.point
        deviation = 20  # Slippage, customizable if needed
        trade_stops_level = symbol_info.trade_stops_level  # Reserved for future use
        trade_tick_size = symbol_info.trade_tick_size  # Reserved for future use

        # Initialize trade request
        if not close_trade:
            # Determine trade type and price
            if trade_type == "BUY":
                trade_type_code = mt5.ORDER_TYPE_BUY
                price = ask_price
            else:
                trade_type_code = mt5.ORDER_TYPE_SELL
                price = bid_price

            # Calculate stop loss (sl) and take profit (tp) | TODO: fix SL and TP
            sl = price * (1 - trade_tick_size)
            tp = price + (1 * trade_stops_level * point)

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": position_size,
                "type": trade_type_code,
                "price": price,
                # "sl": sl,
                # "tp": tp,
                "deviation": deviation,
                "magic": random.randint(234000, 237000),
                "comment": "ITBot",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": filling_mode,
            }
        else:
            # Closing an existing trade
            position_id = kwargs.get("position_id")
            if position_id is None:
                raise ValueError("Position ID is required for closing a trade")

            # Determine reverse trade type and price for closing
            if trade_type == "BUY":
                trade_type_code = mt5.ORDER_TYPE_SELL
                price = bid_price
            else:
                trade_type_code = mt5.ORDER_TYPE_BUY
                price = ask_price

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": position_size,
                "type": trade_type_code,
                "position": position_id,
                "price": price,
                "deviation": deviation,
                # "magic": kwargs.get("magic", 0),  # Default to 0 if not provided
                "comment": "ITBot",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": filling_mode,
            }

        # Log and return the prepared request
        self.logger.debug(f"Prepared trade request: {request}")
        return request

    async def get_bar_data(
        self,
        symbol: str,
        timeframe: int = mt5.TIMEFRAME_D1,
        count: int = 100,
        utc_from: Optional[datetime] = None,
        datetime_format: str = "%Y-%m-%d",
    ) -> pd.DataFrame:
        """
        Fetch historical bar data for a given symbol and timeframe from MetaTrader 5.

        Parameters:
        ----------
        symbol : str
            The trading symbol to fetch data for (e.g., 'EURUSD').
        count : int
            The number of historical bars (candles) to retrieve.
        timeframe : int, optional
            The timeframe for the data (default is MetaTrader 5 daily timeframe).
        utc_from : Optional[datetime], optional
            The starting point for fetching data (default is current UTC time).
        datetime_format : str, optional
            The format in which to return the 'time' column (default is "%Y-%m-%d").

        Returns:
        -------
        pd.DataFrame
            A DataFrame containing the historical data with columns such as 'open', 'high',
            'low', 'close', and 'tick_volume'. The index of the DataFrame will be the 'time' column,
            formatted as per the specified `datetime_format`.
        """
        # Get the current UTC datetime if not provided
        if utc_from is None:
            utc_from = datetime.now()

        # Fetch rates (historical data) from MetaTrader 5
        rates = self.mt5.copy_rates_from(symbol, timeframe, utc_from, count)

        # Convert the rates into a DataFrame
        rates_frame = pd.DataFrame(rates)

        # Check if the rates_frame is empty
        if rates_frame.empty:
            return pd.DataFrame(columns=["time", "open", "high", "low", "close", "tick_volume"])

        # Convert 'time' from Unix timestamp to a human-readable datetime format
        rates_frame["time"] = pd.to_datetime(rates_frame["time"], unit="s")

        # Format the column "time" according to the specified datetime format
        rates_frame["time"] = pd.to_datetime(rates_frame["time"], format=datetime_format)

        # Set 'time' as the index of the DataFrame
        rates_frame.set_index("time", inplace=True)

        # Return the relevant columns (the rates frame should already have them)
        return rates_frame

    async def validate_position_size(self, symbol_info: SymbolInfo, volume: float) -> float:
        """
        Validate and adjust the position size for the specified symbol.

        Parameters:
        ----------
        symbol_info : SymbolInfo
            The symbol information object that contains trading specifications like
            minimum and maximum volume.
        volume : float
            The proposed position size to validate.

        Returns:
        -------
        float
            The adjusted volume that falls within the symbol's allowed range. If the
            proposed volume is lower than the minimum or higher than the maximum, it
            will be adjusted accordingly.

        Raises:
        -------
        ValueError
            If the `symbol_info` is None or does not contain valid information about
            the trading symbol.
        """

        # Ensure symbol_info is available | isinstance(symbol_info, SymbolInfo)
        if not symbol_info:
            self.logger.warning("Symbol information is not available.")
            raise ValueError("Symbol information is not available.")

        # Extract the trading symbol
        symbol = symbol_info.name

        # Check and adjust the volume based on minimum and maximum allowed values
        min_volume = symbol_info.volume_min
        max_volume = symbol_info.volume_max

        if volume < min_volume:
            self.logger.warning(
                f"Volume {volume} is below the minimum allowed volume ({min_volume}) for {symbol}. "
                f"Adjusting to minimum volume."
            )
            volume = min_volume

        if volume > max_volume:
            self.logger.warning(
                f"Volume {volume} exceeds the maximum allowed volume ({max_volume}) for {symbol}. "
                f"Adjusting to maximum volume."
            )
            volume = max_volume

        self.logger.info(
            f"Validated volume for {symbol}: {volume} (Min: {min_volume}, Max: {max_volume})."
        )

        return volume

    async def open_trade(
        self, symbol: str, trade_type: str, position_size: float, **kwargs
    ) -> dict:
        """
        Open a new trade in MetaTrader 5.

        Parameters:
        ----------
        symbol : str
            The trading symbol (e.g., 'EURUSD') for the trade.
        trade_type : str
            The type of trade ('BUY' or 'SELL').
        position_size : float
            The position size (lot size) to open.
        **kwargs : dict
            Additional parameters to customize the trade request, such as:
            - close_trade : bool, whether to close an existing trade (default is False).
            - position_id : int, required if closing a trade.
            - magic : int, optional, a custom magic number for the order.

        Returns:
        -------
        dict
            A dictionary containing the result of the trade request if successful.

        Raises:
        -------
        ValueError
            If the order fails to be sent or if an unexpected error occurs.
        """
        try:
            # Prepare the trade request
            request = await self._prepare_trade_request(symbol, trade_type, position_size, **kwargs)

            # Execute the trade request asynchronously
            result = await asyncio.get_running_loop().run_in_executor(
                None, self.mt5.order_send, request
            )

            self.logger.debug(f"result: {result}")

            # Check if the trade was successfully executed
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"Order send failed with retcode={result.retcode}")

            # Log success and return the result as a dictionary
            self.logger.info(f"MT5 order sent successfully: Order ID = {result.order}")
            return result._asdict()

        except Exception as e:
            # Log and raise any errors that occur during trade execution
            self.logger.error(f"Error executing MT5 order: {e}")
            raise

    async def close_trade(
        self, symbol: str, position_id: int, trade_type: str, position_size: float, **kwargs
    ) -> dict:
        """
        Close an open trade in MetaTrader 5.

        Parameters:
        ----------
        symbol : str
            The trading symbol (e.g., 'EURUSD') of the trade to close.
        position_id : int
            The ID of the open position to be closed.
        trade_type : str
            The type of trade ('BUY' or 'SELL').
        position_size : float
            The position size (lot size) to close.
        **kwargs : dict
            Additional parameters to customize the trade request, such as:
            - magic : int, optional, a custom magic number for the order.

        Returns:
        -------
        dict
            A dictionary containing the result of the trade request if successful.

        Raises:
        -------
        ValueError
            If the order fails to be sent or if an unexpected error occurs.
        """

        try:
            # Prepare the trade request for closing the position
            request = await self._prepare_trade_request(
                symbol,
                trade_type,
                position_size,
                close_trade=True,
                position_id=position_id,
                **kwargs,
            )
            self.logger.debug(f"Trade Request: {request}")

            # Execute the trade request asynchronously
            result = await asyncio.get_running_loop().run_in_executor(
                None, self.mt5.order_send, request
            )

            # Check if the trade was successfully executed
            if result.retcode != self.mt5.TRADE_RETCODE_DONE:
                raise ValueError(f"Order send failed with retcode={result.retcode}")

            # Log success and return the result as a dictionary
            self.logger.info(f"MT5 Position closed successfully: Position ID = {position_id}")
            return result._asdict()

        except Exception as e:
            # Log and raise any errors that occur during trade execution
            self.logger.error(f"Error closing MT5 position: {e}")
            raise

    async def close_all_night(self) -> None:
        """
        Close all open trades for the current account based on their position status.

        Trades are identified by their position type:
        - For positions with zero (0), the trade is closed as a buy.
        - For non-zero positions, the trade is closed as a sell.

        The method also logs the account balance before each trade is closed.
        """
        # Retrieve current positions
        result = await self.get_open_positions()

        for index in range(len(result)):
            # Log current balance
            before_balance = self.mt5.account_info().balance

            # Get the current row of trade details
            row = result.iloc[index]

            # Check if the position is a buy (0) or sell (non-zero)
            # Close the trade as a buy/
            res = self.close_trade(
                symbol=row["symbol"],
                position_id=row["ticket"],
                trade_type=row["position_type_decoded"],
                position_size=row["volume"],
            )

            # Log the result of the trade closure and the account balance after the closure
            after_balance = self.mt5.account_info().balance
            self.logger.info(
                f"Trade closed: {row['symbol']} | Position ID: {row['ticket']} | Result: {res} | Balance before: {before_balance} | Balance after: {after_balance}"
            )

    async def trail_sl(
        self, symbol: str, order_ticket: int, timeframe: int, stop_loss_dict: dict
    ) -> None:
        """
        Continuously update the stop loss for a given order ticket based on the highest
        highs (for sell orders) or lowest lows (for buy orders) of the last three bars.

        TODO: Fix this method

        Args:
        -----
        symbol : str
            The trading symbol for the position.
        order_ticket : int
            The ticket number of the order to manage.
        timeframe : int
            The timeframe for fetching historical bars.
        stop_loss_dict : dict
            A dictionary that maps symbols to their current stop loss values.
        """
        while True:
            # Fetch the last four bars for the specified symbol and timeframe
            bars = self.mt5.copy_rates_from_pos(symbol, timeframe, 0, 4)
            bars_df = pd.DataFrame(bars)

            # Extract the high and low values of the last three bars
            bar_highs = bars_df["high"].iloc[:3].tolist()
            bar_lows = bars_df["low"].iloc[:3].tolist()

            # Get the current position details for the order ticket
            position_info = self.mt5.positions_get(ticket=order_ticket)
            if position_info:
                position_type = position_info[0].type
                stop_loss_value = (
                    max(bar_highs) if position_type == self.mt5.ORDER_TYPE_SELL else min(bar_lows)
                )

                # Normalize the stop loss value based on the tick size
                tick_size = self.mt5.symbol_info(symbol).trade_tick_size
                normalized_sl = round(stop_loss_value / tick_size) * tick_size

                # Update the stop loss if it has changed
                if normalized_sl != stop_loss_dict.get(symbol):
                    current_sl = position_info[0].sl
                    if normalized_sl != current_sl:
                        request = {
                            "action": self.mt5.TRADE_ACTION_SLTP,
                            "position": order_ticket,
                            "symbol": symbol,
                            "magic": 24001,
                            "sl": normalized_sl,
                        }
                        result = self.mt5.order_send(request)

                        # Check the result of the order send request
                        if result.retcode == self.mt5.TRADE_RETCODE_DONE:
                            self.logger.info(
                                f"[{datetime.now()}] Trailing Stop Loss for Order {order_ticket} updated. New S/L: {normalized_sl}\n"
                            )
                            stop_loss_dict[symbol] = normalized_sl
                        elif result.retcode != 10025:  # Ignore error code 10025
                            self.logger.info(
                                f"[{datetime.now()}] Failed to update Trailing Stop Loss for Order {order_ticket}: {result.comment}"
                            )
                            self.logger.info(f"Error code: {result.retcode}\n")

            # Wait for 1 second before checking again
            time.sleep(1)

    async def get_open_positions(self) -> pd.DataFrame:
        """
        Retrieve and return the current open positions in MetaTrader 5.

        Each position includes details such as ticket number, position type (0 for Buy),
        symbol, and volume.

        Returns:
        -------
        pd.DataFrame
            A DataFrame containing the open positions with columns ['ticket', 'position', 'symbol', 'volume', 'position_type_decoded'].
        """
        # Define the column names for the resulting DataFrame
        columns = [
            "time",
            "ticket",
            "position",
            "position_decoded",
            "symbol",
            "volume",
            "price_open",
            "sl",
            "tp",
            "magic",
        ]

        # Get the current open positions
        current_positions = self.mt5.positions_get()

        # If no positions are open, return an empty DataFrame
        if not current_positions:
            return pd.DataFrame(columns=columns)

        # Create a list of lists to accumulate each position's details
        data = [
            [
                position.time,
                position.ticket,
                position.type,
                (
                    "BUY"
                    if position is not None and position.type == 0
                    else "SELL" if position is not None else None
                ),  # Decode position type
                position.symbol,
                position.volume,
                position.price_open,
                position.sl,
                position.tp,
                position.magic,
            ]
            for position in current_positions
        ]

        # Convert the list of positions to a DataFrame
        summary = pd.DataFrame(data, columns=columns)

        return summary

    async def execute(
        self,
        signal: Signal,
        close_trade: bool = False,
        **kwargs: Optional[dict],
    ) -> None:
        """
        Execute a trade order based on the provided signal data and position size.

        Args:
            signal (Signal): The trading signal object containing trade details.
            close_trade (bool): Whether to close an existing trade (default is False).
            **kwargs: Additional arguments to be passed to trade functions.

        Raises:
            ValueError: If symbol information is unavailable or order send fails.

        Example:
            >>> await trader.execute(signal)
        """

        self.logger.info(f"Executing trade with Signal: {signal}")

        try:
            # Validate signal data
            if not signal.trade_type or not signal.symbol:
                raise ValueError(f"Invalid signal data: {signal}")

            # Get symbol information and ensure visibility
            symbol_info = self.mt5.symbol_info(signal.symbol)
            if not symbol_info:
                raise ValueError(
                    f"Symbol '{signal.symbol}' not found, cannot perform trade operation."
                )
            if not symbol_info.visible:
                self.logger.warning(
                    f"Symbol '{signal.symbol}' is not visible, attempting to enable..."
                )
                if not self.mt5.symbol_select(signal.symbol, True):
                    raise ValueError(f"Failed to enable symbol: {signal.symbol}")

            # Execute trade based on whether to open or close a trade
            if not close_trade:
                self.logger.info(
                    f"Opening trade for symbol: {signal.symbol} of type: {signal.trade_type} with size: {signal.position_size}"
                )
                await self.open_trade(
                    signal.symbol, signal.trade_type, signal.position_size, **kwargs
                )
            else:
                self.logger.info(
                    f"Closing trade for symbol: {signal.symbol} with position ID: {kwargs.get('position_id')}"
                )
                await self.close_trade(
                    symbol=signal.symbol,
                    position_id=kwargs.get("position_id"),
                    trade_type=signal.trade_type,
                    position_size=signal.position_size,
                )
        except Exception as e:
            self.logger.error(f"Error executing MT5 order: {e}")
            raise  # Re-raise the exception for higher-level handling if necessary
