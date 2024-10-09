import logging
import os
import random
import re
from typing import Dict, List
from telethon import TelegramClient, events
from packages.itbot_signal_forwarder.mt5_trader import MT5Trader
from trade_flow.common.logging import Logger
from dotenv import load_dotenv

load_dotenv()

random.seed(248)


class ITBot:
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

        # Initialize Telegram client
        self.client = TelegramClient("it_bot_session", self.api_id, self.api_hash)

        # Set up MetaTrader 5 terminal trader
        self.trader = MT5Trader(
            account_number=self.mt5_account_number,
            password=self.mt5_password,
            server=self.mt5_server,
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

    def start_listener(self, chats: List[str] = None):
        """
        Start the Telegram listener to listen for new messages in specified chat channels.

        Args:
            chats (list): List of Telegram chat usernames to listen to.
        """
        if chats is None:
            chats = self.default_chats

        # Convert usernames into channel entities
        channel_entities = [f"https://t.me/{chat}" for chat in chats if "@" not in chat]

        @self.client.on(events.NewMessage(chats=channel_entities))
        async def new_message_listener(event):
            # Extract the message text
            message = event.message
            text = f"{message.message}"

            # Extract channel information
            try:
                entity = await self.client.get_entity(message.peer_id.channel_id)
            except AttributeError:
                entity = await self.client.get_entity(message.peer_id)

            self.logger.debug(f"Received event from {entity.username} with message:\n" + text)

            if "ZONE" in text:
                # Parse the message text for trading signals
                signals = self.parse_trading_data(text)
                self.logger.debug(f"Processed signals: {signals}")
                if len(signals) > 0:
                    for signal in signals:
                        await self.trader.execute(signal)

        # Start the client and listen for new messages
        with self.client:
            self.client.run_until_disconnected()

    def run(self):
        self.client.start(phone=self.phone_number)

        self.logger.info("Listening for Signals...")
        self.start_listener()


if __name__ == "__main__":
    it_bot = ITBot()
    it_bot.run()
