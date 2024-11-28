import asyncio
import logging
import random
import re
from typing import List, Optional
import pandas as pd
from telethon import events
from packages.tf_trade.tf_trade.agents import Agent
from packages.tf_trade.tf_trade.types import Signal, TradeType
from packages.tf_trade.tf_trade.venues import MT5
from packages.tf_trade.tf_trade.interfaces import TelegramInterface
from packages.mt5any import MetaTrader5 as mt5
from trade_flow.common.logging import Logger

random.seed(248)


class TFTrade:
    """
    TFTrade Class for managing trading signals and executing trades using MetaTrader 5.

    Attributes:
        venue (MT5): Instance of MT5 to interact with the MetaTrader 5 platform.
        logger (Logger): Instance of Logger for logging activities and errors.
        notifications_handler (TelegramInterface): Instance of TelegramInterface for handling Telegram messages.
        db (str): Path to the database for storing trade logs.
        default_chats (List[str]): List of default Telegram channels to listen for signals.
    """

    def __init__(
        self,
        agent: Agent,
        venue: MT5,
        notifications_handler: TelegramInterface,
        db: str = "tf_trade_mt5_trades.db",
        logger: Optional[Logger] = None,
    ):
        """
        Initializes the TFTrade instance with the given parameters.

        Args:
            agent (Agent): An instance of an agent for generating trading signals.
            venue (MT5): An instance of MT5 for executing trades.
            notifications_handler (TelegramInterface): An instance of TelegramInterface for handling messages.
            db (str, optional): Path to the SQLite database for storing trade logs. Defaults to "tf_trade_mt5_trades.db".
            logger (Optional[Logger], optional): A Logger instance for logging. If not provided, a default logger is created.
        """

        # Default Telegram chat channels to listen to
        self.default_chats = ["intelligent_trading_signals"]

        # Set up logging
        self.logger = logger or Logger(
            name="tf_trade", log_level=logging.DEBUG, filename="TFTrade.log"
        )

        self.venue = venue
        self.notifications_handler = notifications_handler
        self.agent = agent
        self.db = db

        # Change signals_queue to hold only Signal objects
        self.signals_queue: asyncio.Queue[Signal] = asyncio.Queue()

    def _validate_signal(self, signal: Signal) -> bool:
        """
        Validate the signal to ensure it meets the required criteria.

        Args:
            signal (Signal): The signal to validate.

        Returns:
            bool: True if the signal is valid, False otherwise.
        """
        if signal.price <= 0:
            self.logger.warning("Invalid signal: Price must be greater than 0.")
            return False
        if signal.score < -1 or signal.score > 1:
            self.logger.warning("Invalid signal: Score must be between -1 and 1.")
            return False
        # Add any additional validation criteria as needed

        return True

    def _parse_telegram_signals(self, data: str) -> List[Signal]:
        """
        Parse signals (trading data) from a Telegram message to extract price, score, trend direction, and zone classification.

        Args:
            data (str): Raw trading data as a string received from Telegram.

        Returns:
            List[Signal]: A list of Signal objects parsed from the provided data.
        """

        if "₿" not in data:
            return []

        pattern = re.compile(
            r"₿ (?P<price>[\d,]+) Score: (?P<score>[-+]\d+\.\d{2})\s*(?P<trend>↑)?\s*(?P<zone>[\w\s]+)?"
        )

        signals = []
        for match in pattern.finditer(data):
            # Create a Signal object using the parsed data
            trade_type = (
                match.group("zone").upper().split("ZONE")[0].strip()
                if match.group("zone")
                else "None"
            )
            signal = Signal(
                symbol="BTCUSD",
                price=float(match.group("price").replace(",", "")) if match.group("price") else 0.0,
                score=float(match.group("score")) if match.group("score") else 0.0,
                trend=match.group("trend") or "None",
                zone=match.group("zone") or "None",
                trade_type=TradeType.BUY if "BUY" in trade_type else TradeType.SELL,
                position_size=0.01,
            )
            signals.append(signal)

        return signals

    async def handle_new_message(self, event: events.NewMessage) -> None:
        """
        Handle new messages received from Telegram channels and extract trading signals.

        Args:
            event (events.NewMessage): The event object representing the new Telegram message.
        """

        # Extract the message text
        message = event.message
        text = f"{message.message}"

        # Extract channel information
        try:
            entity = await self.notifications_handler.client.get_entity(message.peer_id.channel_id)
        except AttributeError:
            entity = await self.notifications_handler.client.get_entity(message.peer_id)

        self.logger.debug(f"Received event from {entity.username} with message:\n" + text)

        if "ZONE" in text:
            # Parse the message text for trading signals
            signals = self._parse_telegram_signals(text)
            self.logger.debug(f"Processed signals: {signals}")

            # Process each signal and forward it to MT5 venue for execution
            if signals:
                for signal in signals:
                    self.logger.debug(f"Adding signal to queue: {signal}")
                    await self.signals_queue.put(signal)

    async def send_data(self):
        """
        Continuously send trading data for specified symbols to the agent.

        Timeframe: 1 minute.

        This method fetches trading data for each selected symbol at 1-minute intervals,
        adds the data to the agent for further processing, and sends it to TFTrade for execution.
        The method operates in an infinite loop to ensure ongoing data transmission.

        Notes:
            - The method generates tasks for each symbol concurrently to improve efficiency.
            - A 5-second delay is added between iterations to prevent excessive requests.
        """

        async def fetch_and_send_data(symbol: str):
            """Fetch data for a specific symbol and send it to the agent."""
            try:
                data = await self.venue.get_bar_data(
                    symbol=symbol, timeframe=mt5.TIMEFRAME_M1, count=3500
                )
                await self.agent.add_data(symbol, data)
                self.logger.info(f"Data for {symbol} sent to the agent successfully.")
            except Exception as e:
                self.logger.error(f"Error fetching data for {symbol}: {e}")

        while True:
            tasks = []

            # Loop over selected instruments and create tasks to fetch data concurrently
            for symbol in self.agent.selected_instruments:
                self.logger.debug(f"Preparing to fetch data for symbol: {symbol}")
                tasks.append(fetch_and_send_data(symbol))

            # Run the tasks concurrently
            if tasks:
                await asyncio.gather(*tasks)

            await asyncio.sleep(5)  # Add delay between iterations

    async def close_all_positions(self):
        """
        Close all open trading positions.

        This function retrieves all currently open positions and attempts to close each one.
        It logs the results of each operation and continues until all positions are closed.
        """
        try:
            # Get current open positions
            self.current_open_positions = await self.venue.get_open_positions()
            self.logger.info("Retrieved open positions.")

            if self.current_open_positions.empty:
                self.logger.info("No open positions to close.")
                return

            # Iterate over all open positions and close them
            for index, position_info in self.current_open_positions.iterrows():
                symbol = position_info["symbol"]
                position = position_info["position_decoded"]
                identifier = position_info["ticket"]

                self.logger.info(
                    f"Closing position for symbol: {symbol} | Position: {position} | ID: {identifier}"
                )
                await self.venue.execute(
                    signal=None,  # No specific signal, closing based on current position
                    close_trade=True,
                    position_id=identifier,
                )

            self.logger.info("All open positions have been closed.")

        except Exception as e:
            self.logger.error(f"Error occurred while closing positions: {e}")

    async def run_venue(self):
        """
        Run the trading venue. This function processes signals from the queue and manages open positions accordingly.
        """

        try:
            while True:
                self.logger.debug("Waiting for signal in queue...")
                signal = await self.signals_queue.get()  # Get signal from the queue
                self.logger.debug(f"Received Signal from queue: {signal}")

                # Validate the signal
                if not self._validate_signal(signal):
                    self.logger.error(f"Invalid signal detected: {signal}. Skipping...")
                    continue  # Skip to the next iteration if the signal is invalid

                # Get current open positions for the signal's symbol
                self.current_open_positions = await self.venue.get_open_positions()
                symbol_positions = self.current_open_positions[
                    self.current_open_positions["symbol"] == signal.symbol
                ]
                self.logger.info(f"Open positions for {signal.symbol}: {len(symbol_positions)}")

                # Determine action based on the signal type
                if signal.trade_type in [TradeType.BUY, TradeType.SELL]:
                    # If we have open positions, decide whether to close them
                    if not symbol_positions.empty:
                        await self._handle_existing_positions(signal, symbol_positions)

                    # Open a new position based on the signal
                    await self.venue.execute(signal)
                    self.logger.info(f"Opened new {signal.trade_type} position for {signal.symbol}")

                self.logger.info(
                    "------------------------------------------------------------------"
                )

        except KeyboardInterrupt:
            self.logger.info("Logging out...")
            await self.close_all_positions()

    async def _handle_existing_positions(self, signal, symbol_positions: pd.DataFrame):
        """
        Handle existing open positions for a given symbol based on the new signal.

        Args:
            signal (Signal): The incoming trading signal.
            symbol_positions (pd.DataFrame): A DataFrame containing open positions for the given symbol.
        """

        for index, position_info in symbol_positions.iterrows():
            position = position_info["position_decoded"]
            identifier = position_info["ticket"]

            # Close positions if they are in the opposite direction of the new signal
            if (position == "BUY" and signal.trade_type == TradeType.SELL) or (
                position == "SELL" and signal.trade_type == TradeType.BUY
            ):
                self.logger.info(
                    f"Closing position {position} for {signal.symbol} (ID: {identifier})"
                )
                await self.venue.execute(signal, close_trade=True, position_id=identifier)

            # Optionally: Close or manage positions based on take-profit, stop-loss, or other strategies

    async def run(self):
        """
        Start the TFTrade.

        This method initializes and starts the bot's functionality, including:
        - Starting the Telegram client to listen for trading signals.
        - Adding a message handler to process incoming messages from specified Telegram channels.
        - Running the agent to generate trading signals in parallel with the Telegram listener.

        It sets up the necessary asynchronous tasks to ensure both the Telegram listener and the trading agent run concurrently.
        """
        self.logger.info("Starting TFTrade...")

        # Add message handler to the telegrams notifications listener
        channel_entities = [
            f"https://t.me/{chat}" for chat in self.default_chats if "@" not in chat
        ]
        self.notifications_handler.add_message_handler(channel_entities, self.handle_new_message)

        # Start tasks for the agent and the Telegram listener
        await asyncio.gather(
            self.notifications_handler.run(),  # Start the Telegram listener
            self.agent.run(self.signals_queue),  # Start the agent
            self.send_data(),
            self.run_venue(),  # Start the trading venue
        )
