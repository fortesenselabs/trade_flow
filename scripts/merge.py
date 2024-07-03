import click
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from application.config import Settings
from application.logger import AppLogger
from application.models import AppConfig

logger = AppLogger(name=__name__)

"""
This script is intended for creating one output file from multiple input data files. 
It is needed when we want to use additional data source in order to predict the main parameter.
For example, in order to predict BTC price, we might want to add ETH prices. 
This script solves the following problems:
- Input files might have the same column names (e.g., open, high, low, close) and therefore it adds prefixes to the columns of the output file
- Input data may have gaps and therefore the script generates a regular time raster for the output file. The granularity of the time raster is determined by the parameter
"""


depth_file_names = [  # Leave empty to skip
    # r"DATA2\BITCOIN\GENERATED\depth-BTCUSDT-batch1.csv",
    # r"DATA2\BITCOIN\GENERATED\depth-BTCUSDT-batch2.csv",
    # r"DATA2\BITCOIN\GENERATED\depth-BTCUSDT-batch3.csv",
    # r"DATA2\BITCOIN\GENERATED\depth-BTCUSDT-batch4.csv",
    # r"DATA2\BITCOIN\GENERATED\depth-BTCUSDT-batch5.csv",
]


#
# Readers from inputs files (DEPRECATED)
#


def load_futur_files(futur_file_path):
    """Return a data frame with future features."""

    df = pd.read_csv(futur_file_path, parse_dates=["timestamp"], date_format="ISO8601")
    start = df["timestamp"].iloc[0]
    end = df["timestamp"].iloc[-1]

    df = df.set_index("timestamp")

    logger.info(
        f"Loaded futur file with {len(df)} records in total. Range: ({start}, {end})"
    )

    return df, start, end


def load_kline_files(kline_file_path):
    """Return a data frame with kline features."""

    df = pd.read_csv(kline_file_path, parse_dates=["timestamp"], date_format="ISO8601")
    start = df["timestamp"].iloc[0]
    end = df["timestamp"].iloc[-1]

    df = df.set_index("timestamp")

    logger.info(
        f"Loaded kline file with {len(df)} records in total. Range: ({start}, {end})"
    )

    return df, start, end


def load_depth_files():
    """Return a list of data frames with depth features."""

    dfs = []
    start = None
    end = None
    for depth_file_name in depth_file_names:
        df = pd.read_csv(
            depth_file_name, parse_dates=["timestamp"], date_format="ISO8601"
        )
        # Start
        if start is None:
            start = df["timestamp"].iloc[0]
        elif df["timestamp"].iloc[0] < start:
            start = df["timestamp"].iloc[0]
        # End
        if end is None:
            end = df["timestamp"].iloc[-1]
        elif df["timestamp"].iloc[-1] > end:
            end = df["timestamp"].iloc[-1]

        df = df.set_index("timestamp")

        dfs.append(df)

    length = np.sum([len(df) for df in dfs])
    logger.info(
        f"Loaded {len(depth_file_names)} depth files with {length} records in total. Range: ({start}, {end})"
    )

    return dfs, start, end


#
# Merger
#


@click.command()
@click.option(
    "--config_file", "-c", type=click.Path(), default="", help="Configuration file name"
)
def main(config_file):
    settings: Settings = Settings(config_file)
    logger.info(settings.model_dump())

    app_config: AppConfig = settings.get_app_config()

    time_column = app_config.config.time_column

    data_sources = app_config.config.data_sources
    if not data_sources:
        logger.error(f"ERROR: Data sources are not defined. Nothing to merge.")
        # data_sources = [{"folder": symbol, "file": "klines", "column_prefix": ""}]

    now = datetime.now()

    # Read data from input files
    data_path = Path(app_config.config.data_folder)
    for ds in data_sources:
        # What is want is for each source, load file into df, determine its properties (columns, start, end etc.), and then merge all these dfs

        quote = ds.folder
        if not quote:
            logger.error(f"ERROR. Folder is not specified.")
            continue

        # If file name is not specified then use symbol name as file name
        file = ds.file if ds.file else quote
        if not file:
            file = quote

        file_path = (data_path / quote / file).with_suffix(".csv")
        if not file_path.is_file():
            logger.info(f"Data file does not exist: {file_path}")
            return

        logger.info(f"Reading data file: {file_path}")
        df = pd.read_csv(file_path, parse_dates=[time_column], date_format="ISO8601")
        logger.info(f"Loaded file with {len(df)} records.")

        ds["df"] = df

    # Merge in one df with prefixes and common regular time index
    df_out = merge_data_sources(data_sources)

    #
    # Store file with features
    #
    out_path = data_path / app_config.config.symbol / app_config.config.merge_file_name

    logger.info(f"Storing output file...")
    df_out = df_out.reset_index()
    if out_path.suffix == ".parquet":
        df_out.to_parquet(out_path, index=False)
    elif out_path.suffix == ".csv":
        df_out.to_csv(out_path, index=False)  # float_format="%.6f"
    else:
        logger.error(
            f"ERROR: Unknown extension of the 'merge_file_name' file '{out_path.suffix}'. Only 'csv' and 'parquet' are supported"
        )
        return

    range_start = df_out.index[0]
    range_end = df_out.index[-1]
    logger.info(
        f"Stored output file {out_path} with {len(df_out)} records. Range: ({range_start}, {range_end})"
    )

    elapsed = datetime.now() - now
    logger.info(f"Finished merging data in {str(elapsed).split('.')[0]}")


def merge_data_sources(data_sources: list):

    time_column = app_config.config.time_column
    freq = app_config.config.freq

    for ds in data_sources:
        df = ds.get("df")

        if time_column in df.columns:
            df = df.set_index(time_column)
        elif df.index.name == time_column:
            pass
        else:
            logger.error(f"ERROR: Timestamp column is absent.")
            return

        # Add prefix if not already there
        if ds["column_prefix"]:
            # df = df.add_prefix(ds['column_prefix']+"_")
            df.columns = [
                (
                    ds["column_prefix"] + "_" + col
                    if not col.startswith(ds["column_prefix"] + "_")
                    else col
                )
                for col in df.columns
            ]

        ds["start"] = df.first_valid_index()  # df.index[0]
        ds["end"] = df.last_valid_index()  # df.index[-1]

        ds["df"] = df

    #
    # Create common (main) index and empty data frame
    #
    range_start = min([ds["start"] for ds in data_sources])
    range_end = min([ds["end"] for ds in data_sources])

    # Generate a discrete time raster according to the (pandas) frequency parameter
    index = pd.date_range(range_start, range_end, freq=freq)

    df_out = pd.DataFrame(index=index)
    df_out.index.name = time_column

    for ds in data_sources:
        # Note that timestamps must have the same semantics, for example, start of kline (and not end of kline)
        # If different data sets have different semantics for timestamps, then data must be shifted accordingly
        df_out = df_out.join(ds["df"])

    return df_out


if __name__ == "__main__":
    main()
