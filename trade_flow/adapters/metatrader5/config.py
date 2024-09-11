from __future__ import annotations
from typing import Literal
from nautilus_trader.config import InstrumentProviderConfig
from nautilus_trader.config import LiveDataClientConfig
from nautilus_trader.config import LiveExecClientConfig
from nautilus_trader.config import NautilusConfig

from trade_flow.adapters.metatrader5.mt5api.common import (
    MarketDataTypeEnum as MT5MarketDataTypeEnum,
)
from trade_flow.adapters.metatrader5.common import MT5Symbol


class DockerizedMT5TerminalConfig(NautilusConfig, frozen=True):
    """
    Configuration for `DockerizedMT5Terminal` setup when working with containerized
    installations.

    Parameters
    ----------
    account_number : str, optional
        The Metatrader 5 account number.
        If ``None`` then will source the `MT5_ACCOUNT_NUMBER` environment variable.
    password : str, optional
        The Metatrader 5 account password.
        If ``None`` then will source the `MT5_PASSWORD` environment variable.
    server : str, optional
        The Metatrader 5 server name as it is specified in the terminal.
        If ``None`` then will source the `MT5_SERVER` environment variable.
    read_only_api: bool, optional, default True
        If True, no order execution is allowed. Set read_only_api=False to allow executing live orders.
    timeout: int, optional
        The timeout for trying to launch MT5 docker container when start=True

    """

    account_number: str | None = None
    password: str | None = None
    server: str | None = None
    trading_mode: Literal["paper", "live"] = "paper"
    read_only_api: bool = True
    timeout: int = 300

    def __repr__(self):
        masked_account_number = self._mask_sensitive_info(self.account_number)
        masked_password = self._mask_sensitive_info(self.password)
        return (
            f"DockerizedMT5TerminalConfig(account_number={masked_account_number}, "
            f"password={masked_password}, server={self.server}, "
            f"read_only_api={self.read_only_api}, timeout={self.timeout})"
        )

    @staticmethod
    def _mask_sensitive_info(value: str | None) -> str:
        if value is None:
            return "None"
        return value[0] + "*" * (len(value) - 2) + value[-1] if len(value) > 2 else "*" * len(value)


class MetaTrader5InstrumentProviderConfig(InstrumentProviderConfig, frozen=True):
    """
    Configuration for instances of `MetaTrader5InstrumentProvider`.

    Specify either `load_ids`, `load_symbols`, or both to dictate which instruments the system loads upon start.
    It should be noted that the `MetaTrader5InstrumentProviderConfig` isn't limited to the instruments
    initially loaded. Instruments can be dynamically requested and loaded at runtime as needed.

    Parameters
    ----------
    load_all : bool, default False
        Note: Loading all instruments isn't supported by the MetaTrader5InstrumentProvider.
        As such, this parameter is not applicable.
    load_ids : FrozenSet[InstrumentId], optional
        A frozenset of `InstrumentId` instances that should be loaded during startup. These represent the specific
        instruments that the provider should initially load.
    load_symbols: FrozenSet[MT5Symbol], optional
        A frozenset of `MT5Symbol` objects that are loaded during the initial startup. These specific symbols
        correspond to the instruments that the provider preloads. It's important to note that while the `load_ids`
        option can be used for loading individual instruments, using `load_symbols` allows for a more versatile
        loading of several related instruments like Futures and Options that share the same underlying asset.
    cache_validity_days: int (default: None)
        Default None, will request fresh pull upon starting of TradingNode [only once].
        Setting value will pull the instruments at specified interval, useful when TradingNode runs for many days.
        Example: value set to 1, InstrumentProvider will make fresh pull every day even if TradingNode is not restarted.
    pickle_path: str (default: None)
        If provided valid path, will store the ContractDetails as pickle, and use during cache_validity period.

    """

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MetaTrader5InstrumentProviderConfig):
            return False
        return self.load_ids == other.load_ids and self.load_symbols == other.load_symbols

    def __hash__(self) -> int:
        return hash(
            (
                self.load_ids,
                self.load_symbols,
            ),
        )

    strict_symbology: bool = False
    load_symbols: frozenset[MT5Symbol] | None = None

    cache_validity_days: int | None = None
    pickle_path: str | None = None


class MetaTrader5DataClientConfig(LiveDataClientConfig, frozen=True):
    """
    Configuration for ``MetaTrader5DataClient`` instances.

    Parameters
    ----------
    mt5_host : str, default "127.0.0.1"
        The hostname or ip address for the MetaTrader Terminal (MT5).
    mt5_port : int, default None
        The port for the gateway server. ("web"/"rpyc" defaults: 8000/18812)
    mt5_client_id: int, default 1
        The client_id to be passed into connect call.
    use_regular_trading_hours : bool
        If True, will request data for Regular Trading Hours only.
        Only applies to bar data - will have no effect on trade or tick data feeds.
    market_data_type : MT5MarketDataTypeEnum, default REALTIME
        Set which MT5MarketDataTypeEnum to be used by MetaTrader5Client.
        Configure `MT5MarketDataTypeEnum.DELAYED_FROZEN` to use with account without data subscription.
    ignore_quote_tick_size_updates : bool
        If set to True, the QuoteTick subscription will exclude ticks where only the size has changed but not the price.
        This can help reduce the volume of tick data. When set to False (the default), QuoteTick updates will include
        all updates, including those where only the size has changed.
    dockerized_gateway : DockerizedMT5TerminalConfig, Optional
        The client's terminal container configuration.

    """

    instrument_provider: MetaTrader5InstrumentProviderConfig = MetaTrader5InstrumentProviderConfig()

    mt5_host: str = "127.0.0.1"
    mt5_port: int | None = None
    mt5_client_id: int = 1
    use_regular_trading_hours: bool = True
    market_data_type: MT5MarketDataTypeEnum = MT5MarketDataTypeEnum.REALTIME
    ignore_quote_tick_size_updates: bool = False
    dockerized_gateway: DockerizedMT5TerminalConfig | None = None


class MetaTrader5ExecClientConfig(LiveExecClientConfig, frozen=True):
    """
    Configuration for ``MetaTrader5ExecClient`` instances.

    Parameters
    ----------
    mt5_host : str, default "127.0.0.1"
        The hostname or ip address for the MetaTrader Terminal (MT5).
    mt5_port : int, default None
        The port for the gateway server. ("web"/"rpyc" defaults: 8000/18812)
    mt5_client_id: int, default 1
        The client_id to be passed into connect call.
    account_id : str
        Represents the account_id for MetaTrader 5 instance to which the Terminal is logged in.
        It's crucial that the account_id aligns with the account for which the Terminal is logged in.
        If the account_id is `None`, the system will fallback to use the `MT5_ACCOUNT_NUMBER` from environment variable.
    dockerized_gateway : DockerizedMT5TerminalConfig, Optional
        The client's terminal container configuration.

    """

    instrument_provider: MetaTrader5InstrumentProviderConfig = MetaTrader5InstrumentProviderConfig()

    mt5_host: str = "127.0.0.1"
    mt5_port: int | None = None
    mt5_client_id: int = 1
    account_id: str | None = None
    dockerized_gateway: DockerizedMT5TerminalConfig | None = None
