from datetime import datetime, timedelta
import click
import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from sklearn.metrics import (
    precision_recall_curve,
    PrecisionRecallDisplay,
    RocCurveDisplay,
)
from sklearn.model_selection import ParameterGrid
from tradeflow.evaluators import generate_feature_set
from tradeflow.evaluators.preprocessors import simulated_trade_performance
from application.config.settings import Settings
from application.logger import AppLogger
from application.models.app_model import AppConfig
from application.database import save_model_pair
from application.utils import find_index


logger = AppLogger(name=__name__)

"""
The script is intended for finding best trade parameters for a certain trade algorithm
by executing trade simulation (backtesting) for all specified parameters.
It performs exhaustive search in the space of all specified parameters by computing 
trade performance and then choosing the parameters with the highest profit (or maybe
using other selection criteria like stability of the results or minimum allowed losses etc.)

Notes:
- The optimization is based on certain trade algorithm. This means that a trade algorithm
is a parameter for this script. Different trade algorithms have different trade logics and 
also have different parameters. Currently, the script works with a very simple threshold-based
trade algorithm: if some score is higher than the threshold (parameter) then buy, if it is lower
than another threshold then sell. There is also a version with two thresholds for two scores.
- The script consumes the results of signal script but it then varies parameters of one entry
responsible for generation of trade signals. It then measures performance.
"""


class P:
    in_nrows = 100_000_000


@click.command()
@click.option(
    "--config_file", "-c", type=click.Path(), default="", help="Configuration file name"
)
def main(config_file):
    settings: Settings = Settings(config_file)
    logger.info(settings.model_dump())

    app_config: AppConfig = settings.get_app_config()

    time_column = app_config.config.time_column

    now = datetime.now()

    symbol = app_config.config.symbol
    data_path = Path(app_config.config.data_folder) / symbol
    if not data_path.is_dir():
        logger.error(f"Data folder does not exist: {data_path}")
        return

    out_path = Path(app_config.config.data_folder) / symbol
    out_path.mkdir(parents=True, exist_ok=True)  # Ensure that folder exists

    #
    # Load data with (rolling) label point-wise predictions and signals generated
    #
    file_path = data_path / app_config.config.signal_file_name
    if not file_path.exists():
        logger.error(f"ERROR: Input file does not exist: {file_path}")
        return

    logger.info(f"Loading signals from input file: {file_path}")
    if file_path.suffix == ".parquet":
        df = pd.read_parquet(file_path)
    elif file_path.suffix == ".csv":
        df = pd.read_csv(
            file_path,
            parse_dates=[time_column],
            date_format="ISO8601",
            nrows=P.in_nrows,
        )
    else:
        logger.error(
            f"ERROR: Unknown extension of the 'signal_file_name' file '{file_path.suffix}'. Only 'csv' and 'parquet' are supported"
        )
        return

    logger.info(f"Signals loaded. Length: {len(df)}. Width: {len(df.columns)}")

    #
    # Limit the source data
    #
    train_signal_config = app_config.config.train_signal_model

    data_start = train_signal_config.data_start
    if isinstance(data_start, str):
        data_start = find_index(df, data_start)
    data_end = train_signal_config.data_end
    if isinstance(data_end, str):
        data_end = find_index(df, data_end)

    df = df.iloc[data_start:data_end]
    df = df.reset_index(drop=True)

    logger.info(
        f"Input data size {len(df)} records. Range: [{df.iloc[0][time_column]}, {df.iloc[-1][time_column]}]"
    )

    months_in_simulation = (
        df[time_column].iloc[-1] - df[time_column].iloc[0]
    ) / timedelta(days=365 / 12)

    #
    # Load signal train parameters
    #
    parameter_grid = train_signal_config.grid
    direction = train_signal_config.direction
    if direction not in ["long", "short", "both", ""]:
        raise ValueError(
            f"Unknown value of {direction} in signal train model. Only 'long', 'short' and 'both' are possible."
        )
    topn_to_store = train_signal_config.topn_to_store

    # Evaluate strings to produce lists with ranges of parameters
    if isinstance(parameter_grid.get("buy_signal_threshold"), str):
        parameter_grid["buy_signal_threshold"] = eval(
            parameter_grid.get("buy_signal_threshold")
        )
    if isinstance(parameter_grid.get("buy_signal_threshold_2"), str):
        parameter_grid["buy_signal_threshold_2"] = eval(
            parameter_grid.get("buy_signal_threshold_2")
        )
    if isinstance(parameter_grid.get("sell_signal_threshold"), str):
        parameter_grid["sell_signal_threshold"] = eval(
            parameter_grid.get("sell_signal_threshold")
        )
    if isinstance(parameter_grid.get("sell_signal_threshold_2"), str):
        parameter_grid["sell_signal_threshold_2"] = eval(
            parameter_grid.get("sell_signal_threshold_2")
        )

    # If necessary, disable sell parameters in grid search - they will be set from the buy parameters
    if train_signal_config.buy_sell_equal:
        parameter_grid["sell_signal_threshold"] = [None]
        parameter_grid["sell_signal_threshold_2"] = [None]

    #
    # Find the generators, the parameters of which will be varied
    #
    combine_generator_name = "combine"
    combine_signal_generator = next(
        (
            ss
            for ss in app_config.config.signal_sets
            if ss.generator == combine_generator_name
        ),
        None,
    )
    if not combine_signal_generator:
        raise ValueError(
            f"Signal generator '{generator_name}' not found among all 'signal_sets'"
        )

    generator_name = train_signal_config.signal_generator
    signal_generator = next(
        (ss for ss in app_config.config.signal_sets if ss.generator == generator_name),
        None,
    )
    if not signal_generator:
        raise ValueError(
            f"Signal generator '{generator_name}' not found among all 'signal_sets'"
        )

    performances = list()
    for parameters in tqdm(ParameterGrid([parameter_grid]), desc="MODELS"):

        #
        # If equal parameters, then derive the sell parameter from the buy parameter
        #
        if train_signal_config.buy_sell_equal:
            parameters["sell_signal_threshold"] = -parameters["buy_signal_threshold"]
            # signal_model["sell_slope_threshold"] = -signal_model["buy_slope_threshold"]
            if parameters.get("buy_signal_threshold_2") is not None:
                parameters["sell_signal_threshold_2"] = -parameters[
                    "buy_signal_threshold_2"
                ]

        #
        # Set new parameters of the signal generator
        #
        signal_generator.config.parameters.update(parameters)

        #
        # Execute the signal generator with new parameters by producing new signal columns
        #
        # perform combine before threshold
        df, _ = generate_feature_set(
            df, combine_signal_generator.model_dump(), last_rows=0
        )

        df, new_features = generate_feature_set(
            df, signal_generator.model_dump(), last_rows=0
        )

        #
        # Simulate trade and compute performance using close price and two boolean signals
        # Add a pair of two dicts: performance dict and model parameters dict
        #

        # These boolean columns are used for performance measurement. Alternatively, they are in trade_signal_model
        buy_signal_column = signal_generator.config.names[0]
        sell_signal_column = signal_generator.config.names[1]

        # Perform backtesting
        performance, long_performance, short_performance = simulated_trade_performance(
            df, buy_signal_column, sell_signal_column, "close"
        )

        # Remove some items. Remove lists of transactions which are not needed
        long_performance.pop("transactions", None)
        short_performance.pop("transactions", None)

        if direction == "long":
            performance = long_performance
        elif direction == "short":
            performance = short_performance

        # Add some metrics. Add per month metrics
        performance["profit_percent_per_month"] = (
            performance["profit_percent"] / months_in_simulation
        )
        performance["transaction_no_per_month"] = (
            performance["transaction_no"] / months_in_simulation
        )
        performance["profit_percent_per_transaction"] = (
            performance["profit_percent"] / performance["transaction_no"]
            if performance["transaction_no"]
            else 0.0
        )
        performance["profit_per_month"] = performance["profit"] / months_in_simulation

        # long_performance["profit_percent_per_month"] = long_performance["profit_percent"] / months_in_simulation
        # short_performance["profit_percent_per_month"] = short_performance["profit_percent"] / months_in_simulation

        performances.append(
            dict(
                model=parameters,
                performance={
                    k: performance[k]
                    for k in [
                        "profit_percent_per_month",
                        "profitable",
                        "profit_percent_per_transaction",
                        "transaction_no_per_month",
                    ]
                },
                # long_performance={k: long_performance[k] for k in ['profit_percent_per_month', 'profitable']},
                # short_performance={k: short_performance[k] for k in ['profit_percent_per_month', 'profitable']}
            )
        )

    #
    # Flatten
    #

    # Sort
    performances = sorted(
        performances,
        key=lambda x: x["performance"]["profit_percent_per_month"],
        reverse=True,
    )
    performances = performances[:topn_to_store]

    # Column names (from one record)
    keys = list(performances[0]["model"].keys()) + list(
        performances[0]["performance"].keys()
    )
    # list(performances[0]['long_performance'].keys()) + \
    # list(performances[0]['short_performance'].keys())

    lines = []
    for p in performances:
        record = list(p["model"].values()) + list(p["performance"].values())
        # list(p['long_performance'].values()) + \
        # list(p['short_performance'].values())
        record = [f"{v:.3f}" if isinstance(v, float) else str(v) for v in record]
        record_str = ",".join(record)
        lines.append(record_str)

    #
    # Store simulation parameters and performance
    #
    out_path = (
        (out_path / app_config.config.signal_models_file_name)
        .with_suffix(".txt")
        .resolve()
    )

    if out_path.is_file():
        add_header = False
    else:
        add_header = True
    with open(out_path, "a+") as f:
        if add_header:
            f.write(",".join(keys) + "\n")
        # f.writelines(lines)
        f.write("\n".join(lines) + "\n\n")

    logger.info(f"Simulation results stored in: {out_path}. Lines: {len(lines)}.")

    elapsed = datetime.now() - now
    logger.info(f"Finished simulation in {str(elapsed).split('.')[0]}")


if __name__ == "__main__":
    main()
