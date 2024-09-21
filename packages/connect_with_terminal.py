import os
from nautilus_trader.config import LiveDataEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.config import RoutingConfig
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.examples.strategies.subscribe import SubscribeStrategy
from nautilus_trader.examples.strategies.subscribe import SubscribeStrategyConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.identifiers import InstrumentId

from trade_flow.adapters.metatrader5.config import MetaTrader5DataClientConfig
from trade_flow.adapters.metatrader5.config import MetaTrader5ExecClientConfig
from trade_flow.adapters.metatrader5.config import MetaTrader5InstrumentProviderConfig
from trade_flow.adapters.metatrader5.factories import MetaTrader5LiveDataClientFactory
from trade_flow.adapters.metatrader5.factories import MetaTrader5LiveExecClientFactory

from dotenv import load_dotenv

load_dotenv()


# *** THIS IS A TEST STRATEGY WITH NO ALPHA ADVANTAGE WHATSOEVER. ***
# *** IT IS NOT INTENDED TO BE USED TO TRADE LIVE WITH REAL MONEY. ***

# *** THIS INTEGRATION IS STILL UNDER CONSTRUCTION. ***
# *** CONSIDER IT TO BE IN AN UNSTABLE BETA PHASE AND EXERCISE CAUTION. ***

BROKER_SERVER = "Deriv-Demo"  # "MetaQuotes-Demo"

instrument_provider = MetaTrader5InstrumentProviderConfig(
    load_ids=frozenset(
        [
            f"Volatility-10-Index.{BROKER_SERVER}",
            f"Volatility-75-Index.{BROKER_SERVER}",
            f"Crash-500-Index.{BROKER_SERVER}",
            # f"EUR/USD.{BROKER_SERVER}",
            # f"AUD/CAD.{BROKER_SERVER}",
            # f"AUD/NZD.{BROKER_SERVER}",
            # f"XAU/USD.{BROKER_SERVER}",
            # f"SP500m.{BROKER_SERVER}",
            # f"UK100.{BROKER_SERVER}",
        ],
    ),
)

# Configure the trading node

config_node = TradingNodeConfig(
    trader_id="TESTER-001",
    logging=LoggingConfig(log_level="INFO"),
    data_clients={
        "MT5": MetaTrader5DataClientConfig(
            mt5_host="127.0.0.1",
            mt5_port=18812,
            mt5_client_id=1,
            handle_revised_bars=False,
            use_regular_trading_hours=True,
            instrument_provider=instrument_provider,
        ),
    },
    exec_clients={
        "MT5": MetaTrader5ExecClientConfig(
            mt5_host="127.0.0.1",
            mt5_port=18812,
            mt5_client_id=1,
            account_id=os.getenv(
                "MT5_ACCOUNT_NUMBER"
            ),  # This must match with the MT5 Terminal node is connecting to
            instrument_provider=instrument_provider,
            routing=RoutingConfig(
                default=True,
            ),
        ),
    },
    data_engine=LiveDataEngineConfig(
        time_bars_timestamp_on_close=False,  # Will use opening time as `ts_event` (same like MT5)
        validate_data_sequence=True,  # Will make sure DataEngine discards any Bars received out of sequence
    ),
    timeout_connection=90.0,
    timeout_reconciliation=5.0,
    timeout_portfolio=5.0,
    timeout_disconnection=5.0,
    timeout_post_stop=2.0,
)


# Instantiate the node with a configuration
node = TradingNode(config=config_node)

# Configure your strategy
strategy_config = SubscribeStrategyConfig(
    instrument_id=InstrumentId.from_str(f"Step-Index.{BROKER_SERVER}"),  # "EUR/USD.{BROKER_SERVER}"
    trade_ticks=False,
    quote_ticks=True,
    bars=True,
)
# Instantiate your strategy
strategy = SubscribeStrategy(config=strategy_config)

# Add your strategies and modules
node.trader.add_strategy(strategy)

# Register your client factories with the node (can take user-defined factories)
node.add_data_client_factory("MT5", MetaTrader5LiveDataClientFactory)
node.add_exec_client_factory("MT5", MetaTrader5LiveExecClientFactory)
node.build()


# Stop and dispose of the node with SIGINT/CTRL+C
if __name__ == "__main__":
    try:
        node.run()
    finally:
        node.dispose()
