from asyncio import AbstractEventLoop
from typing import Any, Dict, Optional
from application.models.config_model import ConfigModel
from application.analyzers.base import BaseAnalyzer
from apscheduler.schedulers.asyncio import AsyncIOScheduler


class AppConfig:
    """Globally visible variables."""

    def __init__(
        self,
        config: ConfigModel,
        loop: Optional[AbstractEventLoop] = None,
        sched: Optional[AsyncIOScheduler] = None,
        analyzer: Optional[BaseAnalyzer] = None,
        client: Optional[Any] = None,
        bm: Optional[Any] = None,
        conn_key: Optional[Any] = None,
        error_status: int = 0,
        server_status: int = 0,
        account_status: int = 0,
        trade_state_status: int = 0,
        df: Optional[Any] = None,
        transaction: Optional[Any] = None,
        status: Optional[Any] = None,
        order: Optional[Any] = None,
        order_time: Optional[Any] = None,
        base_quantity: str = "0.04108219",
        quote_quantity: str = "1000.0",
        system_status: Dict[str, Any] = None,
        symbol_info: Dict[str, Any] = None,
        account_info: Dict[str, Any] = None,
    ):
        # System
        self.loop = loop
        self.sched = sched

        self.analyzer = analyzer

        # Connector client
        self.client = client

        # WebSocket for push notifications
        self.bm = bm
        self.conn_key = conn_key

        # State of the server (updated after each interval)
        self.error_status = error_status  # Networks, connections, exceptions etc. what does not allow us to work at all
        self.server_status = (
            server_status  # If server allows us to trade (maintenance, down etc.)
        )
        self.account_status = (
            account_status  # If account allows us to trade (funds, suspended etc.)
        )
        self.trade_state_status = trade_state_status  # Something wrong with our trading logic (wrong use, inconsistent state etc. what we cannot recover)

        self.df = df  # Data from the latest analysis

        # Trade simulator
        self.transaction = transaction
        # Trade binance
        self.status = status  # BOUGHT, SOLD, BUYING, SELLING
        self.order = order  # Latest or current order
        self.order_time = order_time  # Order submission time

        # Available assets for trade
        # Can be set by the sync/recover function or updated by the trading algorithm
        self.base_quantity = (
            base_quantity  # BTC owned (on account, already bought, available for trade)
        )
        self.quote_quantity = (
            quote_quantity  # USDT owned (on account, available for trade)
        )

        # Trader. Status data retrieved from the server. Below are examples only.
        self.system_status = system_status or {
            "status": 0,
            "msg": "normal",
        }  # 0: normal, 1: system maintenance
        self.symbol_info = symbol_info or {}
        self.account_info = account_info or {}
        self.config = config


# class AppConfig(BaseModel):
#     """Globally visible variables."""

#     # System
#     loop: Optional[AbstractEventLoop] = None  # asyncio main loop
#     sched: Optional[AsyncIOScheduler] = None  # Scheduler

#     analyzer: Optional[BaseAnalyzer] = None  # Store and analyze data

#     # Connector client
#     client: Optional[Any] = None

#     # WebSocket for push notifications
#     bm: Optional[Any] = None
#     conn_key: Optional[Any] = None  # Socket

#     #
#     # State of the server (updated after each interval)
#     #
#     # State 0 or None or empty means ok. String and other non-empty objects mean error
#     error_status: int = (
#         0  # Networks, connections, exceptions etc. what does not allow us to work at all
#     )
#     server_status: int = 0  # If server allows us to trade (maintenance, down etc.)
#     account_status: int = 0  # If account allows us to trade (funds, suspended etc.)
#     trade_state_status: int = (
#         0  # Something wrong with our trading logic (wrong use, inconsistent state etc. what we cannot recover)
#     )

#     df: Optional[Any] = None  # Data from the latest analysis

#     # Trade simulator
#     transaction: Optional[Any] = None
#     # Trade binance
#     status: Optional[Any] = None  # BOUGHT, SOLD, BUYING, SELLING
#     order: Optional[Any] = None  # Latest or current order
#     order_time: Optional[Any] = None  # Order submission time

#     # Available assets for trade
#     # Can be set by the sync/recover function or updated by the trading algorithm
#     base_quantity: str = (
#         "0.04108219"  # BTC owned (on account, already bought, available for trade)
#     )
#     quote_quantity: str = "1000.0"  # USDT owned (on account, available for trade)

#     #
#     # Trader. Status data retrieved from the server. Below are examples only.
#     #
#     system_status: Dict[str, Any] = {
#         "status": 0,
#         "msg": "normal",
#     }  # 0: normal, 1: system maintenance
#     symbol_info: Dict[str, Any] = {}
#     account_info: Dict[str, Any] = {}
#     config: Optional[ConfigModel] = None
