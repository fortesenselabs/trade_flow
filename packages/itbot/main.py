import asyncio
import logging
import os
import random
import re
from typing import Dict, List, Optional
from telethon import events
from packages.itbot.agents import Agent, BasicMLAgent
from packages.itbot.itbot import Signal, TradeType
from packages.itbot.itbot.mt5_trader import MT5Trader
from packages.itbot.itbot.interfaces import TelegramInterface
from packages.itbot.itbot.portfolio.risk_manager import RiskManager
from trade_flow.common.logging import Logger
from dotenv import load_dotenv

load_dotenv()

random.seed(248)


class ITBot:
    """
    ITBot Class for managing trading signals and executing trades using MetaTrader 5.

    Attributes:
        trader (MT5Trader): Instance of MT5Trader to interact with the MetaTrader 5 platform.
        logger (Logger): Instance of Logger for logging activities and errors.
        notifications_handler (TelegramInterface): Instance of TelegramInterface for handling Telegram messages.
        db (str): Path to the database for storing trade logs.
        risk_manager (RiskManager): Instance of RiskManager for managing trade risks.
        position_size (float): Size of the trading position to be executed.
        default_chats (List[str]): List of default Telegram channels to listen for signals.
    """

    def __init__(
        self,
        agent: Agent,
        trader: MT5Trader,
        notifications_handler: TelegramInterface,
        risk_manager: RiskManager,
        db: str = "it_bot_mt5_trades.db",
        logger: Optional[Logger] = None,
    ):
        """
        Initializes the ITBot instance with the given parameters.

        Args:
            agent (Agent): An instance of an agent for generating trading signals.
            trader (MT5Trader): An instance of MT5Trader for executing trades.
            notifications_handler (TelegramInterface): An instance of TelegramInterface for handling messages.
            risk_manager (RiskManager): An instance of RiskManager for trade risk management.
            db (str, optional): Path to the SQLite database for storing trade logs. Defaults to "it_bot_mt5_trades.db".
            logger (Optional[Logger], optional): A Logger instance for logging. If not provided, a default logger is created.
        """

        # Default Telegram chat channels to listen to
        self.default_chats = ["intelligent_trading_signals"]

        # Set up logging
        self.logger = logger or Logger(name="it_bot", log_level=logging.DEBUG, filename="ITBot.log")

        self.trader = trader
        self.notifications_handler = notifications_handler
        self.agent = agent
        self.risk_manager = risk_manager
        self.db = db
        # self.position_size = 0  # Define a default position size

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
            signal = Signal(
                symbol="BTCUSD",
                price=float(match.group("price").replace(",", "")) if match.group("price") else 0.0,
                score=float(match.group("score")) if match.group("score") else 0.0,
                trend=match.group("trend") or "None",
                zone=match.group("zone") or "None",
                trade_type=(
                    match.group("zone").upper().split("ZONE")[0].strip()
                    if match.group("zone")
                    else "None"
                ),
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

            self.logger.debug(f"Executing Telegram signals...")
            if signals:
                for signal in signals:
                    await self.signals_queue.put(signal)

    async def run_agent(self):
        """
        Continuously run the agent to generate trading signals and send them to the ITBot for execution.

        This method loads the agent's model and enters an infinite loop to generate and process signals.
        """
        self.logger.debug("Starting Agent")
        # Load model for the agent (modify path as needed)
        self.agent.load_model(f"{os.getcwd()}/models/001.model")

        while True:
            # Dummy data passed to agent for signal generation
            data = {"price": 50000, "score": 0.4}
            # await self.trader.get_bar_data()

            # Generate signals from the agent
            signals = await self.agent.generate_signals(data)

            # Process each signal and forward it to MT5 for execution
            for signal in signals:
                if self._validate_signal(signal):
                    await self.signals_queue.put(signal)
                await asyncio.sleep(5)

    async def run_trader(self, strategy_name: str = "fixed_percentage"):
        """
        Run the trader using the specified strategy for risk management.

        Args:
            strategy_name (str): The strategy to apply for risk management.
                                 Options: ['fixed_percentage', 'kelly_criterion', 'martingale',
                                 'mean_reversion', 'equity_curve', 'volatility_based'].
                                 Defaults to 'fixed_percentage'.
        """
        signal = await self.signals_queue.get()  # Get signal from the queue

        self.risk_manager.select_strategy(strategy_name)
        self.logger.info(
            f"Executing trade with strategy '{strategy_name}' and position size: {signal.position_size}"
        )

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
            identifier = position_info["identifier"]  # Use column name directly
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

        self.logger.info("------------------------------------------------------------------")

    async def run(self):
        """
        Start the ITBot.

        This method initializes and starts the bot's functionality, including:
        - Starting the Telegram client to listen for trading signals.
        - Adding a message handler to process incoming messages from specified Telegram channels.
        - Running the agent to generate trading signals in parallel with the Telegram listener.

        It sets up the necessary asynchronous tasks to ensure both the Telegram listener and the trading agent run concurrently.
        """
        self.logger.info("Starting ITBot...")

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


def main():
    # Set up logging
    logger = Logger(name="it_bot", log_level=logging.DEBUG, filename="ITBot.log")

    phone_number = os.getenv("PHONE_NUMBER")
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    mt5_account_number = os.getenv("MT5_ACCOUNT_NUMBER")
    mt5_password = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")

    # Initialize Telegram bot
    notifications_handler = TelegramInterface(
        phone_number=phone_number,
        api_id=api_id,
        api_hash=api_hash,
        logger=logger,
    )

    # Set up MetaTrader 5 terminal trader
    trader = MT5Trader(
        account_number=mt5_account_number,
        password=mt5_password,
        server=mt5_server,
        logger=logger,
    )

    # Initialize ML Agent instance
    agent = BasicMLAgent(logger=logger)

    # Risk Manager Setup
    target_returns: Optional[List[float]] = None
    period_per_return: int = 3
    total_periods: int = 30
    contract_size: float = 1.0
    risk_manager = RiskManager(
        initial_balance=trader.initial_balance,
        risk_percentage=0.1,
        contract_size=contract_size,
        logger=logger,
    )

    # Setup and Start ITBot
    it_bot = ITBot(agent, trader, notifications_handler, risk_manager, logger=logger)
    asyncio.run(it_bot.run())


if __name__ == "__main__":
    main()
