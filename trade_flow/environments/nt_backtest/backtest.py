import pathlib
from typing import Tuple

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
from nautilus_trader.model.data import Bar
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.persistence.catalog import ParquetDataCatalog  # as DataCatalog


# CATALOG = DataCatalog(str(pathlib.Path(__file__).parent.joinpath("catalog")))


def main(
    instrument_ids: Tuple[str, str],
    catalog: ParquetDataCatalog,
    notional_trade_size_usd: int = 10_000,
    start_time: str = None,
    end_time: str = None,
    log_level: str = "ERROR",
    bypass_logging: bool = False,
    persistence: bool = False,
    **strategy_kwargs,
):
    # Create model prediction actor
    prediction = ImportableActorConfig(
        actor_path="model:DRLAgentActor",
        config_path="model:DRLAgentConfig",
        config=dict(
            source_symbol=instrument_ids[0],
            target_symbol=instrument_ids[1],
        ),
    )

    # Create strategy
    strategy = ImportableStrategyConfig(
        strategy_path="strategy:PairTrader",
        config_path="strategy:PairTraderConfig",
        config=dict(
            source_symbol=instrument_ids[0],
            target_symbol=instrument_ids[1],
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
        actors=[prediction],
    )
    venues = [
        BacktestVenueConfig(
            name="NASDAQ",
            oms_type="NETTING",
            account_type="CASH",
            base_currency="USD",
            starting_balances=["1_000_000 USD"],
        )
    ]
    print("instrument_ids => ", instrument_ids)
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
        for instrument_id in instrument_ids
    ]

    run_config = BacktestRunConfig(engine=engine, venues=venues, data=data)

    print("venues => ", run_config.venues)
    node = BacktestNode(configs=[run_config])
    return node.run()


# # typer.run(main)
# # lr_catalog = LR_MODEL_DATA_CATALOG

# assert len(nautilus_talks_catalog.instruments())>0, "Couldn't load instruments, have you run `poetry run inv extract-catalog`?"

# [result] = main(
#         catalog=nautilus_talks_catalog,
#         instrument_ids=("SMH.NASDAQ", "SOXX.NASDAQ"),
#         # instrument_ids=("EURUSD.SIM"),
#         log_level="INFO",
#         persistence=False,
#         end_time="2020-06-01",
#     )

# print(result.instance_id)
