import asyncio
import logging
import random
import re
from typing import List, Optional
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
        trader (MT5): Instance of MT5 to interact with the MetaTrader 5 platform.
        logger (Logger): Instance of Logger for logging activities and errors.
        notifications_handler (TelegramInterface): Instance of TelegramInterface for handling Telegram messages.
        db (str): Path to the database for storing trade logs.
        default_chats (List[str]): List of default Telegram channels to listen for signals.
    """

    def __init__(
        self,
        agent: Agent,
        trader: MT5,
        notifications_handler: TelegramInterface,
        db: str = "tf_trade_mt5_trades.db",
        logger: Optional[Logger] = None,
    ):
        """
        Initializes the TFTrade instance with the given parameters.

        Args:
            agent (Agent): An instance of an agent for generating trading signals.
            trader (MT5): An instance of MT5 for executing trades.
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

        self.trader = trader
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
            # Validate the signal before adding it to the list
            if self._validate_signal(signal):
                signals.append(signal)
            else:
                self.logger.warning(f"Invalid signal detected: {signal}")

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

            # Process each signal and forward it to MT5 trader for execution
            if signals:
                for signal in signals:
                    if self._validate_signal(signal):
                        self.logger.debug(f"Adding signal to queue: {signal}")
                        await self.signals_queue.put(signal)

    async def run_agent(self):
        """
        Continuously run the agent to generate trading signals for multiple instruments
        and send them to the TFTrade for execution.

        This method generates and processes signals for each symbol selected by the agent symbol.
        """
        self.logger.debug("Starting Agent...")

        while True:
            tasks = []

            # Loop over selected instruments and create tasks to fetch data and generate signals concurrently
            for symbol in self.agent.selected_instruments:
                self.logger.debug(symbol)
                tasks.append(self.process_agent_symbol(symbol))

            # Run the tasks concurrently
            await asyncio.gather(*tasks)

            await asyncio.sleep(5)  # Add delay between iterations

    async def process_agent_symbol(self, symbol: str):
        """
        Process agent's trading signals for a specific symbol.

        Timeframe: 1 min

        Args:
            symbol (str): The trading symbol to process.
        """
        # Fetch data for the symbol
        self.logger.info(f"Fetching data for {symbol}")
        data = await self.trader.get_bar_data(symbol=symbol, timeframe=mt5.TIMEFRAME_M1, count=3500)

        # Generate signals from the agent
        self.logger.info(f"Generating signals for {symbol}")
        signals = await self.agent.generate_signals(symbol, data)

        # Process each signal and forward it to MT5 trader for execution
        if signals:
            for signal in signals:
                if self._validate_signal(signal):
                    self.logger.debug(f"Adding signal to queue: {signal}")
                    await self.signals_queue.put(signal)

    async def run_trader(self):
        """
        Run the trader.
        """
        try:
            while True:
                self.logger.debug("Waiting for signal in queue...")
                signal = await self.signals_queue.get()  # Get signal from the queue
                self.logger.debug(f"Received Signal from queue: {signal}")

                # Get current open positions
                self.current_open_positions = await self.trader.get_open_positions()
                self.current_open_positions.to_csv("current_open_positions.csv")

                # Close trade if applicable
                try:
                    # Filter the DataFrame for the specific symbol
                    position_info = self.current_open_positions.loc[
                        self.current_open_positions["symbol"] == signal.symbol
                    ].iloc[
                        0
                    ]  # Get the first matching row

                    position = position_info["position_decoded"]  # Use column name directly
                    identifier = position_info["ticket"]  # Use column name directly
                except IndexError:
                    position = None
                    identifier = None
                    self.logger.warning(f"No open position found for symbol: {signal.symbol}")

                # Close trades based on position state and signal received
                if position is not None and signal.trade_type in [TradeType.BUY, TradeType.SELL]:
                    self.logger.info(f"POSITION: {position} \t ID: {identifier}")
                    await self.trader.execute(signal, close_trade=True, position_id=identifier)
                else:
                    self.logger.info("No open positions to close.")

                # Open new trades based on the signal
                if position is None and signal.trade_type in [TradeType.BUY, TradeType.SELL]:
                    await self.trader.execute(signal)

                self.logger.info(
                    "------------------------------------------------------------------"
                )
        except KeyboardInterrupt:
            self.logger.info("Logging out...")
            # await self.trader.execute(signal, close_trade=True, position_id=identifier)

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
            self.run_agent(),  # Start the agent
            self.run_trader(),  # Start the trader
        )
