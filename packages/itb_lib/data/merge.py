import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from packages.itb_lib.utils import load_config

"""
This script is intended for creating one output file from multiple input data files. 
It is needed when we want to use additional data source in order to predict the main parameter.
For example, in order to predict BTC price, we might want to add ETH prices. 
This script solves the following problems:
- Input files might have the same column names (e.g., open, high, low, close), and therefore it adds prefixes to the columns of the output file.
- Input data may have gaps and therefore the script generates a regular time raster for the output file. The granularity of the time raster is determined by the `freq` parameter.
"""


def load_futur_files(futur_file_path):
    """
    Load future data from CSV file.

    Args:
        futur_file_path (str): Path to the future data CSV file.

    Returns:
        tuple: DataFrame of future data, start timestamp, and end timestamp.
    """
    df = pd.read_csv(futur_file_path, parse_dates=["timestamp"], date_format="ISO8601")
    start = df["timestamp"].iloc[0]
    end = df["timestamp"].iloc[-1]
    df = df.set_index("timestamp")
    print(f"Loaded futur file with {len(df)} records in total. Range: ({start}, {end})")
    return df, start, end


def load_kline_files(kline_file_path):
    """
    Load kline data from CSV file.

    Args:
        kline_file_path (str): Path to the kline data CSV file.

    Returns:
        tuple: DataFrame of kline data, start timestamp, and end timestamp.
    """
    df = pd.read_csv(kline_file_path, parse_dates=["timestamp"], date_format="ISO8601")
    start = df["timestamp"].iloc[0]
    end = df["timestamp"].iloc[-1]
    df = df.set_index("timestamp")
    print(f"Loaded kline file with {len(df)} records in total. Range: ({start}, {end})")
    return df, start, end


def load_depth_files(depth_file_names):
    """
    Load multiple depth data files and return a list of DataFrames.

    Args:
        depth_file_names (list): List of file paths to depth data CSV files.

    Returns:
        tuple: List of DataFrames with depth data, start timestamp, and end timestamp.
    """
    dfs = []
    start = None
    end = None
    for depth_file_name in depth_file_names:
        df = pd.read_csv(depth_file_name, parse_dates=["timestamp"], date_format="ISO8601")
        # Determine the range of the data
        if start is None or df["timestamp"].iloc[0] < start:
            start = df["timestamp"].iloc[0]
        if end is None or df["timestamp"].iloc[-1] > end:
            end = df["timestamp"].iloc[-1]
        df = df.set_index("timestamp")
        dfs.append(df)

    total_records = np.sum([len(df) for df in dfs])
    print(
        f"Loaded {len(depth_file_names)} depth files with {total_records} records in total. Range: ({start}, {end})"
    )
    return dfs, start, end


def merge_data_sources(data_sources, time_column, freq):
    """
    Merge multiple data sources into a single DataFrame with a common time index.

    Args:
        data_sources (list): List of data sources with DataFrames.
        time_column (str): Name of the time column.
        freq (str): Frequency for the time index (e.g., '1T', '5T', '1H').

    Returns:
        pd.DataFrame: Merged DataFrame with all data sources.
    """
    for ds in data_sources:
        df = ds.get("df")
        if time_column in df.columns:
            df = df.set_index(time_column)
        elif df.index.name != time_column:
            print(f"ERROR: Timestamp column is missing.")
            return

        # Add prefix to column names if specified
        if ds["column_prefix"]:
            df.columns = [
                (
                    f"{ds['column_prefix']}_{col}"
                    if not col.startswith(f"{ds['column_prefix']}_")
                    else col
                )
                for col in df.columns
            ]
        ds["start"] = df.first_valid_index()
        ds["end"] = df.last_valid_index()
        ds["df"] = df

    # Determine the common time range
    range_start = min(ds["start"] for ds in data_sources)
    range_end = min(ds["end"] for ds in data_sources)

    # Generate time index
    index = pd.date_range(range_start, range_end, freq=freq)
    df_out = pd.DataFrame(index=index)
    df_out.index.name = time_column

    # Join all DataFrames
    for ds in data_sources:
        df_out = df_out.join(ds["df"], how="left")

    return df_out


def merge_data(config_file):
    """
    Main function to merge data from multiple sources and save to an output file.

    Args:
        config_file (str): Path to the configuration file.
    """
    config = load_config(config_file)

    time_column = config["time_column"]
    data_sources = config.get("data_sources", [])

    if not data_sources:
        print(f"ERROR: Data sources are not defined. Nothing to merge.")
        return

    now = datetime.now()

    data_path = Path(config["data_folder"])
    for ds in data_sources:
        quote = ds.get("folder")
        if not quote:
            print(f"ERROR: Folder is not specified.")
            continue

        file = ds.get("file", quote)
        file_path = (data_path / quote / file).with_suffix(".csv")
        if not file_path.is_file():
            print(f"Data file does not exist: {file_path}")
            return

        print(f"Reading data file: {file_path}")
        df = pd.read_csv(file_path, parse_dates=[time_column], date_format="ISO8601")
        print(f"Loaded file with {len(df)} records.")
        ds["df"] = df

    # Merge all data sources
    df_out = merge_data_sources(data_sources, time_column, config["freq"])

    # Store the merged file
    out_path = data_path / config["symbol"] / config.get("merge_file_name")
    print(f"Storing output file...")
    df_out = df_out.reset_index()

    if out_path.suffix == ".parquet":
        df_out.to_parquet(out_path, index=False)
    elif out_path.suffix == ".csv":
        df_out.to_csv(out_path, index=False)
    else:
        print(
            f"ERROR: Unsupported file extension '{out_path.suffix}'. Only 'csv' and 'parquet' are supported."
        )
        return

    print(f"Stored output file {out_path} with {len(df_out)} records.")
    print(f"Finished merging data in {str(datetime.now() - now).split('.')[0]}")
