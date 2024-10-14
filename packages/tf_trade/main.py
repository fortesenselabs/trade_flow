import asyncio
import logging
import os
from packages.tf_trade.tf_trade.agents import BasicMLAgent
from packages.tf_trade.tf_trade.venues import MT5
from packages.tf_trade.tf_trade.interfaces import TelegramInterface
from packages.tf_trade.tf_trade import TFTrade
from trade_flow.common.logging import Logger
from dotenv import load_dotenv

load_dotenv()


def main():
    # Set up logging
    logger = Logger(name="tf_trade", log_level=logging.DEBUG, filename="TFTrade.log")

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
    trader = MT5(
        account_number=mt5_account_number,
        password=mt5_password,
        server=mt5_server,
        logger=logger,
    )

    # Initialize ML Agent instance
    agent = BasicMLAgent(
        initial_balance=trader.initial_balance,
        selected_instruments=[
            "ETCUSD",
            "IBM",
            "Volatility 150 (1s) Index",
            "Volatility 200 (1s) Index",
            "Volatility 250 (1s) Index",
        ],
        whitelist_instruments=[
            "ETCUSD",
            "Volatility 150 (1s) Index",
            "Volatility 200 (1s) Index",
            "Volatility 250 (1s) Index",
        ],
        logger=logger,
    )

    # Load model for the agent (modify path as needed)
    agent.load_models(f"{os.getcwd()}/models/")

    # Setup and Start TFTrade
    tf_trade = TFTrade(agent, trader, notifications_handler, logger=logger)
    asyncio.run(tf_trade.run())


if __name__ == "__main__":
    main()
