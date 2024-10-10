import asyncio
import logging
import random
from typing import Dict, Optional, List, Tuple
from packages.itbot.itbot import Signal
from packages.itbot.itbot.MetaTrader5 import MetaTrader5
from packages.itbot.itbot.terminal import (
    DockerizedMT5TerminalConfig,
    DockerizedMT5Terminal,
)
from packages.itbot.itbot.risk_manager import RiskManager
from trade_flow.common.logging import Logger


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
        db (Database): Database instance for trade logs and risk management data.
        initial_balance (float): The initial account balance.
        risk_management (RiskManagement): Risk management instance.
    """

    def __init__(
        self,
        account_number: str,
        password: str,
        server: str,
        logger: Optional[Logger] = None,
        db_name: str = "it_bot_mt5_trades.db",
        target_returns: Optional[List[float]] = None,
        period_per_return: int = 3,
        total_periods: int = 30,
        contract_size: float = 1.0,
    ) -> None:
        """
        Initialize the MT5Trader class with account credentials and configurations.

        Args:
            account_number (str): MetaTrader 5 account number.
            password (str): MetaTrader 5 account password.
            server (str): MetaTrader 5 server.
            logger (Optional[Logger]): Logger instance for logging.
            db_name (str): Name of the database for storing trade logs.
            target_returns (Optional[List[float]]): Target returns for risk management.
            period_per_return (int): Number of periods for each target return.
            total_periods (int): Total trading periods for risk management.
            contract_size (float): Contract size for calculating position sizes.
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
        self.mt5 = MetaTrader5()
        self._initialize_mt5()

        # Get account information
        self.account_info = self.mt5.account_info()._asdict()
        self.initial_balance = self.account_info["balance"]

        # Risk Manager Setup
        self.risk_management = RiskManager(
            initial_balance=self.initial_balance,
            contract_size=contract_size,
            logger=self.logger,
        )

        # Log account info
        self.logger.debug(f"Account Info: {self.account_info}")
        self.logger.info(f"Initial Account Balance: {self.initial_balance}")

    def _initialize_terminal(self) -> None:
        """Initialize and safely start the Dockerized MT5 Terminal."""
        try:
            self.mt5_terminal.safe_start()
            self.logger.info(f"MetaTrader 5 Terminal started for account {self.mt5_account_number}")
        except Exception as e:
            self.logger.error(f"Error initializing Dockerized MT5 Terminal: {e}")
            raise MT5TraderInitializationError("Failed to start Dockerized MT5 Terminal")

    def _initialize_mt5(self) -> None:
        """Initialize the MetaTrader 5 client."""
        try:
            if not self.mt5.initialize():
                raise RuntimeError("MetaTrader 5 initialization failed")
            if not self.mt5.login(self.mt5_account_number, self.mt5_password, self.mt5_server):
                raise RuntimeError("MetaTrader 5 login failed")
        except Exception as e:
            self.logger.error(f"Error initializing MetaTrader 5: {e}")
            raise MT5TraderInitializationError("Failed to initialize MetaTrader 5")

    async def execute_trade(
        self, signal: Signal, strategy_name: str = "fixed_percentage", **kwargs
    ) -> None:
        """
        Execute a trade order based on the provided signal data and selected risk management strategy.

        Args:
            signal (Signal): The trading signal object containing trade details.
            strategy_name (str): The strategy to apply for risk management. options are ['fixed_percentage', 'kelly_criterion', 'martingale', 'mean_reversion', 'equity_curve', 'volatility_based']. Defaults to fixed_percentage

        Raises:
            ValueError: If symbol information is unavailable or order send fails.

        Example:
            >>> await trader.execute_trade(signal)
        """
        self.logger.info(f"Executing trade with Signal: {signal}")

        self.risk_management.select_strategy(strategy_name)

        try:
            if not signal.trade_type or not signal.symbol:
                raise ValueError(f"Invalid signal data: {signal}")

            # Get symbol information and ensure visibility
            symbol_info = self.mt5.symbol_info(signal.symbol)
            if not symbol_info:
                raise ValueError(f"{signal.symbol} not found, cannot perform trade operation")
            if not symbol_info.visible:
                self.logger.warning(f"{signal.symbol} is not visible, attempting to enable...")
                if not self.mt5.symbol_select(signal.symbol, True):
                    raise ValueError(f"Failed to enable symbol: {signal.symbol}")

            # Prepare trade request
            request = self._prepare_trade_request(signal.symbol, signal.trade_type, **kwargs)
            self.logger.info(
                f"Executing trade with strategy '{strategy_name}' and position size: {request['volume']}"
            )
            result = await asyncio.get_running_loop().run_in_executor(
                None, self.mt5.order_send, request
            )

            if result.retcode != self.mt5.TRADE_RETCODE_DONE:
                raise ValueError(f"Order send failed with retcode={result.retcode}")

            self.logger.info(f"MT5 order sent successfully: Order ID = {result.order}")
        except Exception as e:
            self.logger.error(f"Error executing MT5 order: {e}")

    def _prepare_trade_request(self, symbol: str, trade_type: str, **kwargs) -> Dict:
        """Prepare a trade request based on the given symbol and trade type."""
        point = self.mt5.symbol_info(symbol).point
        price = (
            self.mt5.symbol_info_tick(symbol).ask
            if trade_type == "BUY"
            else self.mt5.symbol_info_tick(symbol).bid
        )

        position_size = self.risk_management.calculate_position_size(**kwargs)
        request = {
            "action": self.mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": position_size,
            "type": self.mt5.ORDER_TYPE_BUY if trade_type == "BUY" else self.mt5.ORDER_TYPE_SELL,
            "price": price,
            "sl": price - 100 * point,
            "tp": price + 100 * point,
            "deviation": 20,
            "magic": random.randint(234000, 237000),
            "comment": "ITBot",
            "type_time": self.mt5.ORDER_TIME_GTC,
            "type_filling": self.mt5.ORDER_FILLING_RETURN,
        }
        return request
