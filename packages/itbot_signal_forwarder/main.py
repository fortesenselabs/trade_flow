import logging
import os
import random
import re
from typing import Dict, List
from telethon import events
from packages.itbot_signal_forwarder.lib.mt5_trader import MT5Trader
from packages.itbot_signal_forwarder.lib.notifications import TelegramListener
from trade_flow.common.logging import Logger
from dotenv import load_dotenv

load_dotenv()

random.seed(248)


class ITBot:
    """
    ITBot Class for managing trading signals and executing trades using MetaTrader 5.

    Attributes:
        phone_number (str): Telegram account's phone number.
        api_id (str): Telegram API ID.
        api_hash (str): Telegram API Hash.
        mt5_account_number (str): MetaTrader 5 account number.
        mt5_password (str): MetaTrader 5 account password.
        mt5_server (str): MetaTrader 5 server address.
        trader (MT5Trader): MetaTrader 5 trader instance.
        logger (Logger): Logger instance.
        telegram_listener (TelegramListener): Instance of the Telegram listener.
    """

    def __init__(self):
        self.phone_number = os.getenv("PHONE_NUMBER")
        self.api_id = os.getenv("API_ID")
        self.api_hash = os.getenv("API_HASH")
        self.mt5_account_number = os.getenv("MT5_ACCOUNT_NUMBER")
        self.mt5_password = os.getenv("MT5_PASSWORD")
        self.mt5_server = os.getenv("MT5_SERVER")

        # Default Telegram chat channels to listen to
        self.default_chats = ["intelligent_trading_signals"]

        # Set up logging
        self.logger = Logger(name="it_bot", log_level=logging.DEBUG, filename="ITBot.log")

        # Set up MetaTrader 5 terminal trader
        self.trader = MT5Trader(
            account_number=self.mt5_account_number,
            password=self.mt5_password,
            server=self.mt5_server,
            logger=self.logger,
        )

        # Initialize Telegram listener
        self.telegram_listener = TelegramListener(
            phone_number=self.phone_number,
            api_id=self.api_id,
            api_hash=self.api_hash,
            logger=self.logger,
        )

    def parse_trading_data(self, data: str) -> List[Dict[str, str]]:
        """
        Parse trading data to extract price, score, trend direction, and zone classification.

        Args:
            data (str): Raw trading data as a string.

        Returns:
            List[Dict[str, str]]: Parsed trading data with fields such as price, score, trend, and zone.
        """
        if "₿" not in data:
            return []

        # Pattern to extract price, score, trend direction, and zone from each entry
        pattern = re.compile(
            r"₿ (?P<price>[\d,]+) Score: (?P<score>[-+]\d+\.\d{2})\s*(?P<trend>↑)?\s*(?P<zone>[\w\s]+)?"
        )

        parsed_data = []
        # Find all matches in the data string
        for match in pattern.finditer(data):
            entry = {
                "symbol": "BTCUSD",
                "price": match.group("price").replace(",", "")
                or "None",  # Remove commas from price
                "score": match.group("score") or "None",
                "trend": match.group("trend") or "None",  # Default to "None" if trend not found
                "zone": match.group("zone") or "None",  # Default to "None" if zone not found
                "type": (
                    match.group("zone").upper().split("ZONE")[0].strip()
                    if match.group("zone") is not None
                    else "None"
                ),
            }
            parsed_data.append(entry)

        return parsed_data

    async def handle_new_message(self, event: events.NewMessage) -> None:
        """
        Handle new messages received from Telegram channels.

        Args:
            event (events.NewMessage): The Telegram message event object.
        """
        # Extract the message text
        message = event.message
        text = f"{message.message}"

        # Extract channel information
        try:
            entity = await self.telegram_listener.client.get_entity(message.peer_id.channel_id)
        except AttributeError:
            entity = await self.telegram_listener.client.get_entity(message.peer_id)

        self.logger.debug(f"Received event from {entity.username} with message:\n" + text)

        if "ZONE" in text:
            # Parse the message text for trading signals
            signals = self.parse_trading_data(text)
            self.logger.debug(f"Processed signals: {signals}")
            if len(signals) > 0:
                for signal in signals:
                    await self.trader.execute_trade(signal)

    def run(self):
        """
        Start the ITBot by initializing the Telegram listener and running it.
        """
        # Start Telegram client
        self.telegram_listener.start_client()

        # Add message handler to the listener
        channel_entities = [
            f"https://t.me/{chat}" for chat in self.default_chats if "@" not in chat
        ]
        self.telegram_listener.add_message_handler(channel_entities, self.handle_new_message)

        # Run Telegram listener
        self.logger.info("Listening for Signals...")
        self.telegram_listener.run()


if __name__ == "__main__":
    it_bot = ITBot()
    it_bot.run()
