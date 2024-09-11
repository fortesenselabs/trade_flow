#!/usr/bin/env python3

from decimal import Decimal
import os

from nautilus_trader.adapters.sandbox.config import SandboxExecutionClientConfig
from nautilus_trader.adapters.sandbox.factory import SandboxLiveExecClientFactory
from nautilus_trader.config import LiveDataEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.examples.strategies.ema_cross import EMACross
from nautilus_trader.examples.strategies.ema_cross import EMACrossConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.data import BarType
from nautilus_trader.persistence.catalog import ParquetDataCatalog

from trade_flow.adapters.metatrader5.config import DockerizedMT5TerminalConfig
from trade_flow.adapters.metatrader5.config import MetaTrader5DataClientConfig
from trade_flow.adapters.metatrader5.config import MetaTrader5InstrumentProviderConfig
from trade_flow.adapters.metatrader5.factories import MetaTrader5LiveDataClientFactory
from dotenv import load_dotenv

load_dotenv()


# Load instruments from a Parquet catalog
CATALOG_PATH = f"{os.getcwd()}"
catalog = ParquetDataCatalog(CATALOG_PATH)
SANDBOX_INSTRUMENTS = catalog.instruments(instrument_ids=["EUR/USD.MetaQuotes-Demo"])  # Step Index

# Set up the MetaTrader 5 configuration, this is applicable only when using Docker.
dockerized_gateway = DockerizedMT5TerminalConfig(
    account_number=os.environ["MT5_ACCOUNT_NUMBER"],
    password=os.environ["MT5_PASSWORD"],
    server=os.environ["MT5_SERVER"],
    read_only_api=True,
)

instrument_provider = MetaTrader5InstrumentProviderConfig(
    load_ids=frozenset(str(instrument.id) for instrument in SANDBOX_INSTRUMENTS),
)

# Set up the execution clients (required per venue)
SANDBOX_VENUES = {str(instrument.venue) for instrument in SANDBOX_INSTRUMENTS}
exec_clients = {}
for venue in SANDBOX_VENUES:
    exec_clients[venue] = SandboxExecutionClientConfig(
        venue=venue,
        base_currency="USD",
        starting_balances=["10_000 USD"],
        instrument_provider=instrument_provider,
    )


# Configure the trading node
config_node = TradingNodeConfig(
    trader_id="SANDBOX-001",
    logging=LoggingConfig(log_level="INFO"),
    data_clients={
        "MT5": MetaTrader5DataClientConfig(
            mt5_host="127.0.0.1",
            mt5_port=None,
            mt5_client_id=1,
            use_regular_trading_hours=True,
            instrument_provider=instrument_provider,
            dockerized_gateway=dockerized_gateway,
        ),
    },
    exec_clients=exec_clients,  # type: ignore
    data_engine=LiveDataEngineConfig(
        time_bars_timestamp_on_close=False,
        validate_data_sequence=True,
    ),
    timeout_connection=90.0,
    timeout_reconciliation=5.0,
    timeout_portfolio=5.0,
    timeout_disconnection=5.0,
    timeout_post_stop=2.0,
)

# Instantiate the node with a configuration
node = TradingNode(config=config_node)

# Can manually set instruments for sandbox exec client
for instrument in SANDBOX_INSTRUMENTS:
    node.cache.add_instrument(instrument)

# Instantiate strategies
strategies = {}
for instrument in SANDBOX_INSTRUMENTS:
    # Configure your strategy
    strategy_config = EMACrossConfig(
        instrument_id=instrument.id,
        bar_type=BarType.from_str(f"{instrument.id}-30-SECOND-MID-EXTERNAL"),
        trade_size=Decimal(1_000),
        subscribe_quote_ticks=True,
    )
    # Instantiate your strategy
    strategy = EMACross(config=strategy_config)
    # Add your strategies and modules
    node.trader.add_strategy(strategy)

    strategies[str(instrument.id)] = strategy


# Register client factories with the node
for data_client in config_node.data_clients:
    node.add_data_client_factory(data_client, MetaTrader5LiveDataClientFactory)
for exec_client in config_node.exec_clients:
    node.add_exec_client_factory(exec_client, SandboxLiveExecClientFactory)

node.build()


# Stop and dispose of the node with SIGINT/CTRL+C
if __name__ == "__main__":
    try:
        node.run()
    finally:
        node.dispose()
