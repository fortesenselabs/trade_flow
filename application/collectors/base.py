import asyncio
import logging
from abc import ABC, abstractmethod
from application.logger import AppLogger
from application.models.app_model import AppConfig

logger = AppLogger(name=__name__)


class BaseDataCollector(ABC):
    def __init__(self, app_config: AppConfig):
        self.app_config = app_config

        if self.app_config.config is None:
            raise ValueError("Config model not Set")

    @abstractmethod
    async def get_data_provider_status(self):
        """
        Check the data provider status. Should be implemented in a subclass.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_klines(self, symbol, interval, limit, end_time):
        """
        Request kline data. Should be implemented in a subclass.
        """
        raise NotImplementedError()

    @abstractmethod
    async def store_klines(self, klines):
        """
        Store kline data. Should be implemented in a subclass.
        """
        raise NotImplementedError()

    async def main_collector_task(self):
        """
        It is the highest level task which is added to the event loop and executed normally every 1 minute and then it calls other tasks.
        """
        symbol = self.app_config.config.symbol
        freq = self.app_config.config.freq
        start_ts, end_ts = self.get_interval(freq)
        now_ts = self.get_now_timestamp()

        logger.info(
            f"===> Start collector task. Symbol {symbol}, Timestamp {now_ts}. Interval [{start_ts},{end_ts}]."
        )

        if await self.data_provider_problems_exist():
            await self.data_provider_health_check()
            if await self.data_provider_problems_exist():
                logger.error(
                    "Problems with the data provider server found. No signaling, no trade. Will try next time."
                )
                return 1

        res = await self.sync_data_collector_task()
        if res > 0:
            logger.error(
                "Problem getting data from the server. No signaling, no trade. Will try next time."
            )
            return 1

        logger.info("<=== End collector task.")
        return 0

    async def data_provider_problems_exist(self):
        """
        Check if there are problems with the data provider.
        """
        status = await self.get_data_provider_status()
        return status != 0

    async def sync_data_collector_task(self):
        """
        Collect latest data.
        """
        symbols = self.app_config.config.get(
            "data_sources", [self.app_config.config.symbol]
        )  # TODO: fix this
        # Accessing config from the app configuration
        data_sources = self.app_config.config.data_sources

        # If data_sources is empty, use the symbol as the default
        if not data_sources:
            data_sources = [self.app_config.config.symbol]
        freq = self.app_config.config.freq

        missing_klines_counts = [self.get_missing_klines_count(sym) for sym in symbols]
        tasks = [
            asyncio.create_task(self.request_klines(s, freq, c))
            for c, s in zip(missing_klines_counts, symbols)
        ]

        results = {}
        timeout = 10  # Seconds to wait for the result

        for fut in asyncio.as_completed(tasks, timeout=timeout):
            try:
                res = await fut
            except TimeoutError:
                logger.warning(f"Timeout {timeout} seconds when requesting kline data.")
                return 1
            except Exception as e:
                logger.warning("Exception when requesting kline data.")
                return 1

            if res and res.keys():
                try:
                    added_count = await self.store_klines(res)
                except Exception as e:
                    logger.error(
                        f"Error storing kline result in the database. Exception: {e}"
                    )
                    return 1
                results.update(res)
            else:
                logger.error("Received empty or wrong result from klines request.")
                return 1

        return 0

    async def request_klines(self, symbol, freq, limit):
        """
        Request klines data from the service for one symbol.
        """
        klines_per_request = 400  # Limitation of API
        now_ts = self.get_now_timestamp()
        start_ts, end_ts = self.get_interval(freq)

        try:
            if limit <= klines_per_request:
                klines = await self.get_klines(symbol, freq, limit, now_ts)
            else:
                request_start_ts = now_ts - self.get_interval_length_ms(freq) * (
                    limit + 1
                )
                klines = await self.get_klines(symbol, freq, limit, request_start_ts)
        except Exception as e:
            logger.error(f"Exception while requesting klines: {e}")
            return {}

        klines_full = [kl for kl in klines if kl[0] < start_ts]
        last_full_kline_ts = klines_full[-1][0]

        if last_full_kline_ts != start_ts - self.get_interval_length_ms(freq):
            logger.error(
                f"UNEXPECTED RESULT: Last full kline timestamp {last_full_kline_ts} is not equal to previous full interval start {start_ts - self.get_interval_length_ms(freq)}. Maybe some results are missing and there are gaps."
            )

        return {symbol: klines_full}

    async def data_provider_health_check(self):
        """
        Request information about the data provider server state.
        """
        status = await self.get_data_provider_status()
        if status != 0:
            self.app_config.server_status = 1
            return 1
        self.app_config.server_status = 0
        return 0

    @abstractmethod
    def get_interval(self, freq):
        """
        Get the start and end timestamp for the given frequency. Should be implemented in a subclass.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_now_timestamp(self):
        """
        Get the current timestamp. Should be implemented in a subclass.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_interval_length_ms(self, freq):
        """
        Get the interval length in milliseconds for the given frequency. Should be implemented in a subclass.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_missing_klines_count(self, symbol):
        """
        Get the number of missing klines for the given symbol. Should be implemented in a subclass.
        """
        raise NotImplementedError()

    def pandas_get_interval(self, freq):
        raise NotImplementedError()

    def pandas_interval_length_ms(self, freq):
        raise NotImplementedError()

    # def data_provider_problems_exist(self):
    #     pass

    # async def data_provider_health_check(self):
    #     pass

    # def get_missing_klines_count(self, symbol):
    #     pass

    # def get_klines(self, symbol, interval, limit, endTime):
    #     pass

    # def get_historical_klines(self, symbol, interval, start_str, end_str):
    #     pass

    # def store_klines(self, res):
    #     pass
