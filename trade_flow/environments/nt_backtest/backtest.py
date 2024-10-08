import pathlib
import shutil
import pandas as pd
import yfinance as yf
from pathlib import Path
from typing import Optional, Tuple

from nautilus_trader.backtest.node import BacktestNode
from nautilus_trader.config import (
    CacheConfig,
    BacktestDataConfig,
    BacktestEngineConfig,
    BacktestRunConfig,
    BacktestVenueConfig,
    ImportableActorConfig,
    ImportableStrategyConfig,
    RiskEngineConfig,
    StreamingConfig,
)
from nautilus_trader.model.data import Bar, BarType, BarSpecification
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.test_kit.providers import CSVTickDataLoader, TestInstrumentProvider
from nautilus_trader.persistence.wranglers import QuoteTickDataWrangler, BarDataWrangler
from nautilus_trader.persistence.catalog import ParquetDataCatalog

# from trade_flow.agents.sb3_agent import SB3Agent


# CATALOG = DataCatalog(str(pathlib.Path(__file__).parent.joinpath("catalog")))
CATALOG_PATH = Path.cwd() / "catalog"


def fetch_data(
    instrument_name: str,
    datetime_format: str = "mixed",
    interval: str = "1d",
    start: str = "2020-01-01",
    end: str = "2021-01-01,",
    venue: str = "NASDAQ",
):
    data: Optional[pd.DataFrame] = yf.download(
        instrument_name, interval=interval, start=start, end=end
    )
    data.index = pd.to_datetime(data.index, format=datetime_format)
    data.drop(columns=["Adj Close"], axis=1, inplace=True)
    data.index.set_names("timestamp", inplace=True)

    # Process bars using a wrangler
    INSTRUMENT = TestInstrumentProvider.equity(symbol=instrument_name.upper(), venue=venue.upper())
    wrangler = BarDataWrangler(
        bar_type=BarType.from_str(f"{instrument_name.upper()}.{venue}-1-DAY-LAST-EXTERNAL"),
        instrument=INSTRUMENT,
    )

    bars = wrangler.process(data)

    return INSTRUMENT, bars


def main(
    instrument_id: str,
    catalog: ParquetDataCatalog,
    notional_trade_size_usd: int = 10_000,
    start_time: str = None,
    end_time: str = None,
    log_level: str = "ERROR",
    bypass_logging: bool = False,
    persistence: bool = False,
    **strategy_kwargs,
):
    # Create agent model actor
    agent = ImportableActorConfig(
        actor_path="agent:DRLAgent",
        config_path="agent:DRLAgentConfig",
        config=dict(
            symbol=instrument_id,
        ),
    )

    # Create strategy
    strategy = ImportableStrategyConfig(
        strategy_path="strategy:DRLAgentStrategy",
        config_path="strategy:DRLAgentStrategyConfig",
        config=dict(
            symbol=instrument_id,
            notional_trade_size_usd=notional_trade_size_usd,
            **strategy_kwargs,
        ),
    )

    # Create backtest engine
    engine = BacktestEngineConfig(
        trader_id="BACKTESTER-001",
        cache=CacheConfig(tick_capacity=100_000),
        # bypass_logging=bypass_logging,
        # log_level=log_level,
        streaming=StreamingConfig(catalog_path=str(catalog.path)) if persistence else None,
        risk_engine=RiskEngineConfig(max_order_submit_rate="1000/00:00:01"),  # type: ignore
        strategies=[strategy],
        actors=[agent],
    )
    venues = [
        BacktestVenueConfig(
            name="BINANCE",
            oms_type="NETTING",
            account_type="CASH",
            base_currency="USD",
            starting_balances=["1_000_000 USD"],
        )
    ]

    data = [
        BacktestDataConfig(
            data_cls=Bar.fully_qualified_name(),
            catalog_path=str(catalog.path),
            catalog_fs_protocol=catalog.fs_protocol,
            catalog_fs_storage_options=catalog.fs_storage_options,
            instrument_id=InstrumentId.from_str(instrument_id),
            start_time=start_time,
            end_time=end_time,
        )
        # for instrument_id in instrument_ids
    ]

    run_config = BacktestRunConfig(engine=engine, venues=venues, data=data)

    print("venues => ", run_config.venues)
    node = BacktestNode(configs=[run_config])
    return node.run()


if __name__ == "__main__":
    smh_instrument, smh_bars = fetch_data(
        "SMH",
        interval="1d",
        datetime_format="%Y-%m-%d %H:%M:%S.%f",
        start="2020-01-01",
        end="2021-01-01",
    )
    print(smh_instrument, smh_bars)

    soxx_instrument, soxx_bars = fetch_data(
        "SOXX",
        interval="1d",
        datetime_format="%Y-%m-%d %H:%M:%S.%f",
        start="2020-01-01",
        end="2021-01-01",
    )
    print(soxx_instrument, soxx_bars)

    # Clear if it already exists, then create fresh
    if CATALOG_PATH.exists():
        shutil.rmtree(CATALOG_PATH)
    CATALOG_PATH.mkdir(parents=True)

    # Create a catalog instance
    nautilus_talks_catalog = ParquetDataCatalog(CATALOG_PATH)

    # Write instrument to the catalog
    nautilus_talks_catalog.write_data([smh_instrument, soxx_instrument])

    # Write bars to catalog
    nautilus_talks_catalog.write_data(smh_bars)
    nautilus_talks_catalog.write_data(soxx_bars)

    nautilus_talks_catalog_path = str(pathlib.Path.cwd().joinpath("catalog"))
    print(nautilus_talks_catalog_path)

    nautilus_talks_catalog = ParquetDataCatalog(nautilus_talks_catalog_path)

    print(nautilus_talks_catalog.instruments())

    # typer.run(main)
    # lr_catalog = LR_MODEL_DATA_CATALOG

    assert (
        len(nautilus_talks_catalog.instruments()) > 0
    ), "Couldn't load instruments, have you run `poetry run inv extract-catalog`?"

    results = main(
        catalog=nautilus_talks_catalog,
        instrument_id="BTCUSD.BINANCE",
        # instrument_ids=("SMH.NASDAQ", "SOXX.NASDAQ"),
        # instrument_ids=("EURUSD.SIM"),
        log_level="INFO",
        persistence=False,
        end_time="2020-06-01",
    )

    print("\n\n")
    print(results)
    if len(results) > 0:
        print(results[0].instance_id)
