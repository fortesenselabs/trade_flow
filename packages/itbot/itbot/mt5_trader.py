import asyncio
import logging
import random
import time
import pandas as pd
from datetime import datetime
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
            risk_percentage=0.1,
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

            # self.logger.debug(
            #     self.mt5.login(self.mt5_account_number, self.mt5_password, self.mt5_server)
            # )
            # if not self.mt5.login(self.mt5_account_number, self.mt5_password, self.mt5_server):
            #     raise RuntimeError("MetaTrader 5 login failed")
        except Exception as e:
            self.logger.error(f"Error initializing MetaTrader 5: {e}")
            raise MT5TraderInitializationError("Failed to initialize MetaTrader 5")

    def _prepare_trade_request(self, symbol: str, trade_type: str, **kwargs) -> Dict:
        """Prepare a trade request based on the given symbol and trade type."""

        def round_2_tick_size(price: float, trade_tick_size):
            return round(price / trade_tick_size) * trade_tick_size

        symbol_info = self.mt5.symbol_info(symbol)
        point = symbol_info.point
        trade_stops_level = symbol_info.trade_stops_level
        trade_tick_size = symbol_info.trade_tick_size
        price = (
            self.mt5.symbol_info_tick(symbol).bid
            if trade_type == "BUY"
            else self.mt5.symbol_info_tick(symbol).ask
        )

        position_size = self.risk_management.calculate_position_size(**kwargs)

        # Validate the position size before executing the trade
        position_size = self.validate_position_size(symbol, position_size)

        request = {
            "action": self.mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": position_size,
            "type": self.mt5.ORDER_TYPE_BUY if trade_type == "BUY" else self.mt5.ORDER_TYPE_SELL,
            "price": price,
            # "sl": price - 1000 * point,
            # "tp": price + (100 * 2) * point,  # RRR => 2:1
            "deviation": 20,
            "magic": random.randint(234000, 237000),
            "comment": "ITBot",
            # "type_time": self.mt5.ORDER_TIME_GTC,
            # "type_filling": self.mt5.ORDER_FILLING_RETURN,
        }
        self.logger.debug(request)
        return request

    def validate_position_size(self, symbol: str, volume: float) -> bool:
        """
        Validate the position size for the specified symbol.

        Args:
            symbol (str): The trading symbol.
            volume (float): The proposed position size.

        Returns:
            bool: True if the position size is valid, raises ValueError otherwise.
        """
        symbol_info = self.mt5.symbol_info(symbol)

        if not symbol_info:
            raise ValueError(f"Symbol {symbol} information is not available.")

        self.logger.debug(symbol_info)

        # Check minimum and maximum volume
        min_volume = symbol_info.volume_min
        max_volume = symbol_info.volume_max

        if volume < min_volume:
            self.logger.warning(
                f"Volume {volume} is below the minimum volume of {min_volume} for {symbol}."
            )
            volume = min_volume
        if volume > max_volume:
            self.logger.warning(
                f"Volume {volume} exceeds the maximum volume of {max_volume} for {symbol}."
            )
            volume = max_volume

        self.logger.info(
            f"Volume {volume} is valid for {symbol} (min: {min_volume}, max: {max_volume})."
        )
        return volume

    def trail_sl(self, symbol, order_ticket, timeframe, stop_loss_dict):
        while True:

            bars = self.mt5.copy_rates_from_pos(symbol, timeframe, 0, 4)
            bars_df = pd.DataFrame(bars)
            bar1_high = bars_df["high"].iloc[0]
            bar2_high = bars_df["high"].iloc[1]
            bar3_high = bars_df["high"].iloc[2]
            bar1_low = bars_df["low"].iloc[0]
            bar2_low = bars_df["low"].iloc[1]
            bar3_low = bars_df["low"].iloc[2]

            if self.mt5.positions_get(ticket=order_ticket):
                position_type = self.mt5.positions_get(ticket=order_ticket)[0].type
                if position_type == self.mt5.ORDER_TYPE_SELL:
                    stop_loss_value = max(bar1_high, bar2_high, bar3_high)  # Sell order S/L
                else:
                    stop_loss_value = min(bar1_low, bar2_low, bar3_low)  # Buy order S/L

                tick_size = self.mt5.symbol_info(symbol).trade_tick_size
                normalised_sl = round(stop_loss_value / tick_size) * tick_size

                if normalised_sl != stop_loss_dict[symbol]:
                    current_sl = self.mt5.positions_get(ticket=order_ticket)[0].sl
                    if normalised_sl != current_sl:
                        request = {
                            "action": self.mt5.TRADE_ACTION_SLTP,
                            "position": order_ticket,
                            "symbol": symbol,
                            "magic": 24001,
                            "sl": normalised_sl,
                        }
                        result = self.mt5.order_send(request)
                        if result.retcode == self.mt5.TRADE_RETCODE_DONE:
                            print(
                                f"[{datetime.now()}] Trailing Stop Loss for Order {order_ticket} updated. New S/L: {normalised_sl}"
                            )
                            print()
                            stop_loss_dict[symbol] = normalised_sl
                        elif result.retcode == 10025:  # Ignore error code 10025
                            pass
                        else:
                            print(
                                f"[{datetime.now()}] Failed to update Trailing Stop Loss for Order {order_ticket}: {result.comment}"
                            )
                            print(f"Error code: {result.retcode}")
                            print()

            time.sleep(1)  # Wait for 1 second before checking again

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
            # result = self.mt5.order_send(request)

            if result.retcode != self.mt5.TRADE_RETCODE_DONE:
                raise ValueError(f"Order send failed with retcode={result.retcode}")

            self.logger.info(f"MT5 order sent successfully: Order ID = {result.order}")
        except Exception as e:
            self.logger.error(f"Error executing MT5 order: {e}")
