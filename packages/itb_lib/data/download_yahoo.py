import yfinance as yf
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict


def download_yahoo(data_sources: List[Dict], time_column: str, data_folder: str) -> pd.DataFrame:
    """
    Download stock quotes from Yahoo Finance and store them in CSV files.

    Args:
        data_sources (List[Dict]): A list of dictionaries with each dict containing 'folder' (symbol name)
                                   and optional 'file' (output file name).
        time_column (str): Name of the column representing time (e.g., 'Date').
        data_folder (str): Path to the folder where data files should be saved.

    Returns:
        pd.DataFrame: DataFrame containing the last downloaded data.
    """
    data_path = Path(data_folder)
    now = datetime.now()

    for ds in data_sources:
        quote = ds.get("folder")
        if not quote:
            print(f"ERROR. Folder is not specified.")
            continue

        file = ds.get("file", quote)
        if not file:
            file = quote

        print(f"Start downloading '{quote}' ...")
        file_path = data_path / quote
        file_path.mkdir(parents=True, exist_ok=True)

        file_name = (file_path / file).with_suffix(".csv")

        if file_name.is_file():
            df = pd.read_csv(file_name, parse_dates=[time_column])
            df[time_column] = df[time_column].dt.date
            last_date = df.iloc[-1][time_column]

            new_df = yf.download(quote, period="5d", auto_adjust=True)
            new_df = new_df.reset_index()
            new_df["Date"] = pd.to_datetime(new_df["Date"]).dt.date
            new_df.rename({"Date": time_column}, axis=1, inplace=True)
            new_df.columns = new_df.columns.str.lower()

            df = pd.concat([df, new_df]).drop_duplicates(subset=[time_column], keep="last")
        else:
            print(f"File not found. Full fetch...")
            df = yf.download(quote, period="max", auto_adjust=True)
            df = df.reset_index()
            df["Date"] = pd.to_datetime(df["Date"]).dt.date
            df.rename({"Date": time_column}, axis=1, inplace=True)
            df.columns = df.columns.str.lower()
            print(f"Full fetch finished.")

        df = df.sort_values(by=time_column)
        df.to_csv(file_name, index=False)
        print(f"Stored in '{file_name}'")

    elapsed = datetime.now() - now
    print(f"Finished downloading data in {str(elapsed).split('.')[0]}")

    return df


# Example Usage:
# data_sources = [{"folder": "AAPL", "file": "apple_stock"}]
# download_yahoo(data_sources, time_column="Date", data_folder="data/stocks")
