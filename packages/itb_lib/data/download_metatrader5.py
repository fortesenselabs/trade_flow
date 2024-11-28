import logging
import time
import pandas as pd
import asyncio
from datetime import datetime
from typing import Optional
from trade_flow.common.logging import Logger
from packages.mt5any import (
    DockerizedMT5TerminalConfig,
    DockerizedMT5Terminal,
)
from packages.mt5any import MetaTrader5 as mt5


class MetaTraderException(Exception):
    """Base exception class for MetaTrader errors."""

    pass


class MetaTraderInitializationError(MetaTraderException):
    """Raised when there is an error initializing MT5 Trader."""

    pass


class MetaTrader:
    """
    A class to fetch data from MetaTrader 5 using Dockerized MT5 Terminals.

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
        Initialize the MetaTrader class with account credentials and configurations.

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
            raise MetaTraderInitializationError("Failed to start Dockerized MT5 Terminal")

    def _initialize_mt5(self) -> None:
        """Initialize the MetaTrader 5 client."""
        try:
            if not self.mt5.initialize():
                raise RuntimeError("MetaTrader 5 initialization failed")

            # if not self.mt5.login(self.mt5_account_number, self.mt5_password, self.mt5_server):
            #     raise RuntimeError("MetaTrader 5 login failed")
        except Exception as e:
            self.logger.error(f"Error initializing MetaTrader 5: {e}")
            raise MetaTraderInitializationError("Failed to initialize MetaTrader 5")

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


async def fetch_historical_data(
    account_number: str,
    password: str,
    server: str,
    symbol: str,
    timeframe: int,
    count: int,
    utc_from: Optional[datetime] = None,
    datetime_format: str = "%Y-%m-%d",
) -> pd.DataFrame:
    """
    Fetch historical data from MetaTrader 5.

    Args:
        account_number (str): MetaTrader 5 account number.
        password (str): MetaTrader 5 account password.
        server (str): MetaTrader 5 server.
        symbol (str): The trading symbol to fetch data for (e.g., 'EURUSD').
        timeframe (int): The timeframe for the data (e.g., mt5.TIMEFRAME_D1).
        count (int): The number of historical bars to retrieve.
        utc_from (Optional[datetime]): The starting point for fetching data (default is current UTC time).
        datetime_format (str): The format in which to return the 'time' column (default is "%Y-%m-%d").

    Returns:
        pd.DataFrame: A DataFrame containing the historical data.
    """
    # Create an instance of MetaTrader
    mt5_instance = None

    try:
        mt5_instance = MetaTrader(account_number, password, server)
        historical_data = await mt5_instance.get_bar_data(
            symbol, timeframe, count, utc_from, datetime_format
        )
        return historical_data

    except MetaTraderInitializationError as e:
        print(f"Initialization error: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of error

    except Exception as e:
        print(f"An error occurred while fetching historical data: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of error

    finally:
        if mt5_instance:
            # Cleanup if necessary (e.g., closing connections)
            pass


# Example of how to call the function (inside an async event loop)
# historical_data = await fetch_historical_data("your_account_number", "your_password", "your_server", "EURUSD", mt5.TIMEFRAME_D1, 100)
