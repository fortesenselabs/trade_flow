import asyncio
import os
from functools import lru_cache

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import MessageBus
from nautilus_trader.core.correctness import PyCondition
from nautilus_trader.live.factories import LiveDataClientFactory
from nautilus_trader.live.factories import LiveExecClientFactory
from nautilus_trader.model.identifiers import AccountId

from metatrader5.client import MetaTrader5Client
from metatrader5.common import MT5_VENUE
from metatrader5.config import DockerizedMT5TerminalConfig, MetaTrader5DataClientConfig, MetaTrader5ExecClientConfig, MetaTrader5InstrumentProviderConfig
from metatrader5.data import MetaTrader5DataClient
from metatrader5.execution import MetaTrader5ExecutionClient
from metatrader5.terminal import DockerizedMT5Terminal
from metatrader5.providers import MetaTrader5InstrumentProvider

TERMINAL = None
MT5_CLIENTS: dict[tuple, MetaTrader5Client] = {}


def get_cached_mt5_client(
    loop: asyncio.AbstractEventLoop,
    msgbus: MessageBus,
    cache: Cache,
    clock: LiveClock,
    host: str = "127.0.0.1",
    port: int | None = None,
    client_id: int = 1,
    dockerized_gateway: DockerizedMT5TerminalConfig | None = None,
) -> MetaTrader5Client:
    """
    Retrieve or create a cached MetaTrader5Client using the provided key.

    Should a keyed client already exist within the cache, the function will return this instance. It's important
    to note that the key comprises a combination of the host, port, and client_id.

    Parameters
    ----------
    loop: asyncio.AbstractEventLoop,
        loop
    msgbus: MessageBus,
        msgbus
    cache: Cache,
        cache
    clock: LiveClock,
        clock
    host: str
        The MT5 host to connect to. This is optional if using DockerizedMT5TerminalConfig, but is required otherwise.
    port: int
        The MT5 port to connect to. This is optional if using DockerizedMT5TerminalConfig, but is required otherwise.
    client_id: int
        The unique session identifier for the Terminal.A single host can support multiple connections;
        however, each must use a different client_id.
    dockerized_gateway: DockerizedMT5TerminalConfig, optional
        The configuration for the dockerized gateway.If this is provided, Nautilus will oversee the docker
        environment, facilitating the operation of the MT5 Terminal within.

    Returns
    -------
    MetaTrader5Client

    """
    global TERMINAL
    if dockerized_gateway:
        PyCondition.equal(host, "127.0.0.1", "host", "127.0.0.1")
        PyCondition.none(port, "Ensure `port` is set to None when using DockerizedMT5TerminalConfig.")
        if TERMINAL is None:
            TERMINAL = DockerizedMT5Terminal(dockerized_gateway)
            TERMINAL.safe_start(wait=dockerized_gateway.timeout)
            port = TERMINAL.port
        else:
            port = TERMINAL.port
    else:
        PyCondition.not_none(
            host,
            "Please provide the `host` IP address for the MT5 Terminal.",
        )
        PyCondition.not_none(port, "Please provide the `port` for the MT5 Terminal.")

    client_key: tuple = (host, port, client_id)

    if client_key not in MT5_CLIENTS:
        client = MetaTrader5Client(
            loop=loop,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            host=host,
            port=port,
            client_id=client_id,
        )
        client.start()
        MT5_CLIENTS[client_key] = client
    return MT5_CLIENTS[client_key]


@lru_cache(1)
def get_cached_metatrader5_instrument_provider(
    client: MetaTrader5Client,
    config: MetaTrader5InstrumentProviderConfig,
) -> MetaTrader5InstrumentProvider:
    """
    Cache and return a MetaTrader5InstrumentProvider.

    If a cached provider already exists, then that cached provider will be returned.

    Parameters
    ----------
    client : MetaTrader5Client
        The client for the instrument provider.
    config: MetaTrader5InstrumentProviderConfig
        The instrument provider config

    Returns
    -------
    MetaTrader5InstrumentProvider

    """
    return MetaTrader5InstrumentProvider(client=client, config=config)


class MetaTrader5LiveDataClientFactory(LiveDataClientFactory):
    """
    Provides a `MetaTrader5` live data client factory.
    """

    @staticmethod
    def create(  # type: ignore
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: MetaTrader5DataClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> MetaTrader5DataClient:
        """
        Create a new MetaTrader5 data client.

        Parameters
        ----------
        loop : asyncio.AbstractEventLoop
            The event loop for the client.
        name : str
            The custom client ID.
        config : dict
            The configuration dictionary.
        msgbus : MessageBus
            The message bus for the client.
        cache : Cache
            The cache for the client.
        clock : LiveClock
            The clock for the client.

        Returns
        -------
        MetaTrader5DataClient

        """
        client = get_cached_mt5_client(
            loop=loop,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            host=config.mt5_host,
            port=config.mt5_port,
            client_id=config.mt5_client_id,
            dockerized_gateway=config.dockerized_gateway,
        )

        # Get instrument provider singleton
        provider = get_cached_metatrader5_instrument_provider(
            client=client,
            config=config.instrument_provider,
        )

        # Create client
        data_client = MetaTrader5DataClient(
            loop=loop,
            client=client,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            instrument_provider=provider,
            mt5_client_id=config.mt5_client_id,
            config=config,
            name=name,
        )
        return data_client


class MetaTrader5LiveExecClientFactory(LiveExecClientFactory):
    """
    Provides a `MetaTrader5` live execution client factory.
    """

    @staticmethod
    def create(  # type: ignore
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: MetaTrader5ExecClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> MetaTrader5ExecutionClient:
        """
        Create a new MetaTrader5 execution client.

        Parameters
        ----------
        loop : asyncio.AbstractEventLoop
            The event loop for the client.
        name : str
            The custom client ID.
        config : dict[str, object]
            The configuration for the client.
        msgbus : MessageBus
            The message bus for the client.
        cache : Cache
            The cache for the client.
        clock : LiveClock
            The clock for the client.

        Returns
        -------
        MetaTrader5SpotExecutionClient

        """
        client = get_cached_mt5_client(
            loop=loop,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            host=config.mt5_host,
            port=config.mt5_port,
            client_id=config.mt5_client_id,
            dockerized_gateway=config.dockerized_gateway,
        )

        # Get instrument provider singleton
        provider = get_cached_metatrader5_instrument_provider(
            client=client,
            config=config.instrument_provider,
        )

        # Set account ID
        mt5_account = config.account_id or os.environ.get("MT5_ACCOUNT_NUMBER")
        assert (
            mt5_account
        ), f"Must pass `{config.__class__.__name__}.account_id` or set `MT5_ACCOUNT_NUMBER` env var."

        account_id = AccountId(f"{name or MT5_VENUE.value}-{mt5_account}")

        # Create client
        exec_client = MetaTrader5ExecutionClient(
            loop=loop,
            client=client,
            account_id=account_id,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            instrument_provider=provider,
            config=config,
            name=name,
        )
        return exec_client
