import os

from nautilus_trader.config import LiveDataEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.config import RoutingConfig
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.examples.strategies.subscribe import SubscribeStrategy
from nautilus_trader.examples.strategies.subscribe import SubscribeStrategyConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.book import OrderBook
from nautilus_trader.model.data import QuoteTick, Bar, BarType, BarSpecification
from nautilus_trader.model.enums import AggregationSource, BarAggregation, PriceType

from metatrader5.common import MT5_VENUE
from metatrader5.common import MT5Symbol
from metatrader5.config import DockerizedMT5TerminalConfig
from metatrader5.config import MetaTrader5DataClientConfig
from metatrader5.config import MetaTrader5ExecClientConfig
from metatrader5.config import MetaTrader5InstrumentProviderConfig
from metatrader5.factories import MetaTrader5LiveDataClientFactory
from metatrader5.factories import MetaTrader5LiveExecClientFactory

from dotenv import load_dotenv

load_dotenv()

# *** THIS IS A TEST STRATEGY WITH NO ALPHA ADVANTAGE WHATSOEVER. ***
# *** IT IS NOT INTENDED TO BE USED TO TRADE LIVE WITH REAL MONEY. ***

# *** THIS INTEGRATION IS STILL UNDER CONSTRUCTION. ***
# *** CONSIDER IT TO BE IN AN UNSTABLE BETA PHASE AND EXERCISE CAUTION. ***

BROKER_SERVER = "Deriv-Demo" # "MetaQuotes-Demo"
mt5_symbols = [
    # MT5Symbol(
    #     symbol="EUR/USD.MetaQuotes-Demo",
    # ),
    # MT5Symbol(symbol="USDCHF", broker=BROKER_SERVER),
    # MT5Symbol(symbol="GBPUSD", broker=BROKER_SERVER),
    # MT5Symbol(symbol="USDJPY", broker=BROKER_SERVER),
    # MT5Symbol(symbol="USDCNH", broker=BROKER_SERVER),
    # MT5Symbol(symbol="USDCAD", broker=BROKER_SERVER),
    # MT5Symbol(symbol="XAGUSD", broker=BROKER_SERVER),
    MT5Symbol(symbol="Step Index", broker=BROKER_SERVER),
    # MT5Symbol(symbol="Step-Index-200", broker=BROKER_SERVER),
    MT5Symbol(symbol="Boom 1000 Index", broker=BROKER_SERVER),
]

dockerized_gateway = DockerizedMT5TerminalConfig(
    account_number=os.environ["MT5_ACCOUNT_NUMBER"],
    password=os.environ["MT5_PASSWORD"],
    server=os.environ["MT5_SERVER"],
    read_only_api=True,
)

instrument_provider = MetaTrader5InstrumentProviderConfig(
    load_ids=frozenset(
        [
            # f"Volatility-10-Index.{BROKER_SERVER}",
            # f"Volatility-75-Index.{BROKER_SERVER}",
            f"Crash 500 Index.{BROKER_SERVER}",
            # f"EUR/USD.{BROKER_SERVER}",
            # f"AUD/CAD.{BROKER_SERVER}",
            # f"AUD/NZD.{BROKER_SERVER}",
            # f"XAU/USD.{BROKER_SERVER}",
            # f"SP500m.{BROKER_SERVER}",
            # f"UK100.{BROKER_SERVER}",
        ],
    ),
    load_symbols=frozenset(mt5_symbols),
)

# Configure the trading node

config_node = TradingNodeConfig(
    trader_id="TESTER-001",
    logging=LoggingConfig(log_level="INFO"),
    data_clients={
        "MT5": MetaTrader5DataClientConfig(
            mt5_client_id=1,
            handle_revised_bars=False,
            use_regular_trading_hours=True,
            # market_data_type=IBMarketDataTypeEnum.DELAYED_FROZEN,  # If unset default is REALTIME
            instrument_provider=instrument_provider,
            dockerized_gateway=dockerized_gateway,
        ),
    },
    exec_clients={
        "MT5": MetaTrader5ExecClientConfig(
            mt5_client_id=1,
            account_id=os.environ["MT5_ACCOUNT_NUMBER"],  # This must match with the MT5 Terminal node is connecting to
            dockerized_gateway=dockerized_gateway,
            instrument_provider=instrument_provider,
            routing=RoutingConfig(
                default=True,
            ),
        ),
    },
    data_engine=LiveDataEngineConfig(
        time_bars_timestamp_on_close=False,  # Will use opening time as `ts_event` (same like IB)
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
    instrument_id=InstrumentId.from_str(f"Step Index.{BROKER_SERVER}"), # "EUR/USD.{BROKER_SERVER}"
    quote_ticks=True,
    bars=True,
)

# Instantiate your strategy
class PSubscribeStrategy(SubscribeStrategy):
    def __init__(self, config: SubscribeStrategyConfig) -> None:
        super().__init__(config) 

    def on_start(self) -> None:
        """
        Actions to be performed on strategy start.
        """
        self.instrument = self.cache.instrument(self.instrument_id)
        if self.instrument is None:
            self.log.error(f"Could not find instrument for {self.instrument_id}")
            self.stop()
            return

        if self.config.book_type:
            self.book = OrderBook(
                instrument_id=self.instrument.id,
                book_type=self.config.book_type,
            )
            if self.config.snapshots:
                self.subscribe_order_book_at_interval(
                    instrument_id=self.instrument_id,
                    book_type=self.config.book_type,
                )
            else:
                self.subscribe_order_book_deltas(
                    instrument_id=self.instrument_id,
                    book_type=self.config.book_type,
                )

        if self.config.trade_ticks:
            self.subscribe_trade_ticks(instrument_id=self.instrument_id)
        if self.config.quote_ticks:
            self.subscribe_quote_ticks(instrument_id=self.instrument_id)
        if self.config.bars:
            bar_type: BarType = BarType(
                instrument_id=self.instrument_id,
                bar_spec=BarSpecification(
                    step=1,
                    aggregation=BarAggregation.MINUTE,
                    price_type=PriceType.LAST,
                ),
                aggregation_source=AggregationSource.EXTERNAL,
            )
            self.subscribe_bars(bar_type)

    def on_bar(self, bar: Bar) -> None:
        print("bar => ", bar)
    
strategy = PSubscribeStrategy(config=strategy_config)

# Add your strategies and modules
node.trader.add_strategy(strategy)

# Register your client factories with the node (can take user-defined factories)
node.add_data_client_factory("MT5", MetaTrader5LiveDataClientFactory)
# node.add_exec_client_factory("MT5", MetaTrader5LiveExecClientFactory)
node.build()
node.portfolio.set_specific_venue(MT5_VENUE)

# Stop and dispose of the node with SIGINT/CTRL+C
if __name__ == "__main__":
    try:
        node.run()
    finally:
        node.dispose()
