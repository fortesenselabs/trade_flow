import logging
import os
import random
import re
from typing import Dict, List
from telethon import TelegramClient, events
from packages.itbot_signal_forwarder.risk_management import Database, RiskManagement
from trade_flow.common.logging import Logger
from packages.itbot_signal_forwarder.MetaTrader5 import MetaTrader5
from packages.itbot_signal_forwarder.terminal import (
    DockerizedMT5TerminalConfig,
    DockerizedMT5Terminal,
)
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

        # Set up Dockerized MetaTrader 5 terminal configuration
        self.mt5_config = DockerizedMT5TerminalConfig(
            account_number=self.mt5_account_number,
            password=self.mt5_password,
            server=self.mt5_server,
            read_only_api=True,
        )

        # Initialize MetaTrader 5 Terminal
        self.mt5_terminal = DockerizedMT5Terminal(config=self.mt5_config)
        self.mt5_terminal.safe_start()

        # Initialize MetaTrader 5
        self.mt5 = MetaTrader5()
        self.mt5.initialize()
        self.mt5.login(self.mt5_account_number, self.mt5_password, self.mt5_server)

        self.account_info = self.mt5.account_info()._asdict()

        self.db = Database(db_name="it_bot_trades.db")
        self.return_rates, self.total_periods = RiskManagement.generate_return_rates(
            target_returns=[3, 1, 2, 1, 1.5, 1, 1.2, 1, 1.2, 1],
            period_per_return=3,
            total_periods=30,
        )

        self.initial_balance = self.account_info["balance"]
        self.risk_management = RiskManagement(
            initial_balance=self.initial_balance,
            contract_size=1,  # BTCUSD is 1
            return_rates=self.return_rates,
        )

        self.logger.debug(f"Account Info: {self.account_info}")
        self.logger.info(f"Initial Account Balance: {self.initial_balance}")

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

    async def forward_signal_to_mt5(self, signal_data: Dict):
        """
        Send parsed signal data to MetaTrader 5 as a trade request.

        Args:
            signal_data (Dict[str, Any]): Dictionary containing parsed signal information.
        """
        try:
            if signal_data["type"] is None:
                raise ValueError(f"No trade zone specified")

            # prepare the buy request structure
            symbol = signal_data["symbol"]
            symbol_info = self.mt5.symbol_info(symbol)
            if symbol_info is None:
                raise ValueError(f"{symbol} not found, can not call order_check()")

            # if the symbol is unavailable in MarketWatch, add it
            if not symbol_info.visible:
                self.logger.warning(f"{symbol} is not visible, trying to switch on")
                if not self.mt5.symbol_select(symbol, True):
                    raise ValueError(f"symbol_select({symbol}) failed, exit")

            trade_type = (
                self.mt5.ORDER_TYPE_BUY
                if "BUY" in signal_data["type"]
                else self.mt5.ORDER_TYPE_SELL
            )
            lot = 0.01  # Managed by risk manager
            deviation = 20
            point = self.mt5.symbol_info(symbol).point
            price = (
                self.mt5.symbol_info_tick(symbol).ask
                if trade_type == self.mt5.ORDER_TYPE_BUY
                else self.mt5.symbol_info_tick(symbol).bid
            )

            request = {
                "action": self.mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot,
                "type": trade_type,
                "price": price,
                "sl": price - 100 * point,  # Managed by risk manager
                "tp": price + 100 * point,  # Managed by risk manager
                "deviation": deviation,
                "magic": random.randint(234000, 237000),
                "comment": "ITBot",
                "type_time": self.mt5.ORDER_TIME_GTC,
                "type_filling": self.mt5.ORDER_FILLING_RETURN,
            }

            result = self.mt5.order_send(request)
            if result.retcode != self.mt5.TRADE_RETCODE_DONE:
                raise ValueError("order_send failed, retcode={}".format(result.retcode))

            self.logger.info(f"MT5 order sent: {result.order}")
        except Exception as e:
            self.logger.error(f"Error sending MT5 order: {e}")

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
                if len(signals) > 0:
                    self.logger.debug(f"Processed signals: {signals}")
                    for signal in signals:
                        await self.forward_signal_to_mt5(signal)

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
