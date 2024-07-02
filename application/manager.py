import asyncio
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# from metatrader.base import BaseClient
# from metatrader.client import MTClient
from application.analyzers.analyzer import Analyzer
from metatrader.client import Client
from metatrader.services import PingService


from application.models.app_model import AppConfig
from application.logger import AppLogger
from application.collectors import BinanceDataCollector, MetaTraderDataCollector
from application.utils.binance import freq_to_CronTrigger

logger = AppLogger(name=__name__)


class AppManager:
    def __init__(self, config: AppConfig):
        self.config = config
        self.transaction_file = Path("transactions.txt")

    def data_provider_problems_exist(self):
        if self.config.error_status != 0:
            return True
        if self.config.server_status != 0:
            return True
        return False

    def problems_exist(self):
        if self.config.error_status != 0:
            return True
        if self.config.server_status != 0:
            return True
        if self.config.account_status != 0:
            return True
        if self.config.trade_state_status != 0:
            return True
        return False

    def register_scheduler(self, freq: str):
        self.config.sched = AsyncIOScheduler()

        # logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
        logging.getLogger("apscheduler").setLevel(logging.WARNING)

        trigger = freq_to_CronTrigger(freq)

        self.config.sched.add_job(self.main_task, trigger=trigger, id="app:main_task")

        self.config.sched.start()  # Start scheduler (essentially, start the thread)

        logger.info(f"Scheduler started.")

        return

    async def main_task(self):
        """This task will be executed regularly according to the schedule"""
        res = await main_collector_task()
        if res:
            return res

        try:
            analyze_task = await self.app.loop.run_in_executor(
                None, self.app.analyzer.analyze
            )
        except Exception as e:
            logger.error(f"Error while analyzing data: {e}")
            return

        score_notification_model = self.app.config.score_notification_model
        if score_notification_model.score_notification:
            await send_score_notification()

        diagram_notification_model = self.app.config.diagram_notification_model
        notification_freq = diagram_notification_model.notification_freq
        freq = self.app.config.freq
        if notification_freq:
            if (
                pandas_get_interval(notification_freq)[0]
                == pandas_get_interval(freq)[0]
            ):
                await send_diagram()

        trade_model = self.app.config.trade_model
        if trade_model.trader_simulation:
            transaction = await trader_simulation()
            if transaction:
                await send_transaction_message(transaction)
        if trade_model.trader_binance:
            trade_task = self.app.loop.create_task(main_trader_task())

        return

    @staticmethod
    async def start(app_config: AppConfig):
        app = AppManager(app_config)

        symbol = app_config.config.symbol
        freq = app_config.config.freq

        logger.info(f"Initializing server. Trade pair: {symbol}. ")
        # getcontext().prec = 8

        #
        # Connect to the server and update/initialize the system state
        #
        app_config.client = Client()
        ping = PingService(app_config.client)

        logger.info(f"app_config.client.ping: {ping.do()}")

        collector = MetaTraderDataCollector(app_config, app_config.client)

        app_config.analyzer = Analyzer(app_config.config)

        app_config.loop = asyncio.get_event_loop()

        # Do one time server check and state update
        try:
            await collector.data_provider_health_check()
        except Exception as e:
            logger.exception(
                f"Problems during health check (connectivity, server etc.) {e}"
            )

        if await collector.data_provider_problems_exist():
            logger.error("Problems during health check (connectivity, server etc.)")
            return

        logger.info("Finished health check (connection, server status etc.)")

        # Cold start: load initial data, do complete analysis
        try:
            await collector.sync_data_collector_task()

            # First call may take some time because of big initial size and hence we make the second call to get the (possible) newest klines
            await collector.sync_data_collector_task()

            # Analyze all received data (and not only last few rows) so that we have full history
            app_config.analyzer.analyze(ignore_last_rows=True)
        except Exception as e:
            logger.exception(f"Problems during initial data collection. {e}")

        if await app.data_provider_problems_exist():
            logger.info(f"Problems during initial data collection.")
            return

        logger.info(f"Finished initial data collection.")

        # Initialize trade status (account, balances, orders etc.) in case we are going to really execute orders
        if app_config.config.get("trade_model", {}).get("trader_binance"):
            try:
                app_config.loop.run_until_complete(update_trade_status())
            except Exception as e:
                print(f"Problems trade status sync. {e}")

            if await app.data_provider_problems_exist():
                print(f"Problems trade status sync.")
                return

            print(f"Finished trade status sync (account, balances etc.)")
            print(
                f"Balance: {app_config.config['base_asset']} = {str(app_config.base_quantity)}"
            )
            print(
                f"Balance: {app_config.config['quote_asset']} = {str(app_config.quote_quantity)}"
            )

        #
        # Register scheduler
        #
        app.register_scheduler(freq)

        #
        # Start event loop
        #
        try:
            app_config.loop.run_forever()  # Blocking. Run until stop() is called
        except KeyboardInterrupt:
            logger.exception(f"KeyboardInterrupt.")
        finally:
            app_config.loop.close()
            logger.info(f"Event loop closed.")
            app_config.sched.shutdown()
            logger.info(f"Scheduler shutdown.")

        return 0


# # Example instantiation and usage:
# if __name__ == "__main__":
#     logger = AppLogger(name=__name__)
#     app_config = AppConfig()
#     collector = AppManager(app_config, logger)

#     # To run the main task
#     asyncio.run(collector.main_task())
