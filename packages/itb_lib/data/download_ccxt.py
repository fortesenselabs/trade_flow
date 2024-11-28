import os
import json
import pandas as pd
from datetime import datetime
import ccxt
from packages.itb_lib.utils import klines_to_df


def download_klines(
    exchange_name, api_key, api_secret, data_folder, time_column, freq, symbols, save=True
):
    """
    Retrieve historical klines from the specified exchange.

    Args:
    - exchange_name: The name of the exchange (e.g., 'binance').
    - api_key: The API key for the exchange.
    - api_secret: The API secret for the exchange.
    - data_folder: The folder path where data will be stored.
    - time_column: The name of the column representing time in the data.
    - freq: The frequency of the data (Pandas frequency).
    - symbols: A list of trading symbols to download.
    - save: Boolean indicating whether to save the data to CSV files (default is True).

    Returns:
    - df: DataFrame containing the downloaded klines data.
    """
    exchange = getattr(ccxt, exchange_name)(
        {
            "apiKey": api_key,
            "secret": api_secret,
        }
    )

    now = datetime.now()
    data_frames = []

    for symbol in symbols:
        print(f"Start downloading '{symbol}' ...")
        file_path = os.path.join(data_folder, symbol)
        os.makedirs(file_path, exist_ok=True)  # Ensure that folder exists
        file_name = os.path.join(file_path, f"klines.csv")

        # Get the latest klines to determine the latest available timestamp
        klines = exchange.fetch_ohlcv(symbol, timeframe=freq, limit=5)
        latest_ts = pd.to_datetime(klines[-1][0], unit="ms")

        if os.path.isfile(file_name):
            df = pd.read_csv(file_name)
            df[time_column] = pd.to_datetime(df[time_column], format="ISO8601")
            oldest_point = df[time_column].iloc[-1]  # Use the last point as the new starting point
            print(
                f"File found. Appending data for {symbol} since {str(latest_ts)} to '{file_name}'"
            )
        else:
            df = pd.DataFrame()  # New DataFrame for new data
            oldest_point = datetime(2017, 1, 1)  # Start from a defined old date
            print(f"File not found. Downloading all data for {symbol} into '{file_name}'.")

        # Download klines from the exchange
        klines = exchange.fetch_ohlcv(
            symbol, timeframe=freq, since=int(oldest_point.timestamp() * 1000)
        )
        df = klines_to_df(klines, df)

        if save:
            df.to_csv(file_name, index=False)

        data_frames.append(df)
        print(f"Finished downloading '{symbol}'. Data stored in '{file_name}'")

    elapsed = datetime.now() - now
    print(f"Finished downloading data in {str(elapsed).split('.')[0]}")
    return pd.concat(data_frames, ignore_index=True)


def get_exchange_info(exchange_name):
    """
    Retrieve exchange information and save it as JSON.

    Args:
    - exchange_name: The name of the exchange (e.g., 'binance').
    """
    exchange = getattr(ccxt, exchange_name)()
    exchange_info = exchange.fetch_markets()
    with open(f"{exchange_name}_exchange_info.json", "w") as file:
        json.dump(exchange_info, file, indent=4)
    print(f"Exchange info saved to '{exchange_name}_exchange_info.json'")


def get_account_info(exchange_name, api_key, api_secret):
    """
    Retrieve account information.

    Args:
    - exchange_name: The name of the exchange (e.g., 'binance').
    - api_key: The API key for the exchange.
    - api_secret: The API secret for the exchange.
    """
    exchange = getattr(ccxt, exchange_name)(
        {
            "apiKey": api_key,
            "secret": api_secret,
        }
    )

    account_info = exchange.fetch_balance()
    return account_info


def get_market_info(exchange_name, symbol):
    """
    Retrieve market information including order book depth.

    Args:
    - exchange_name: The name of the exchange (e.g., 'binance').
    - symbol: Trading symbol to fetch market info for.
    """
    exchange = getattr(ccxt, exchange_name)()
    depth = exchange.fetch_order_book(symbol)
    return depth


# The streaming functions would require a different approach,
# as CCXT does not support WebSocket streaming out of the box.
# We would need to rely on another library or handle WebSocket connections separately.

# Example usage:
# if __name__ == "__main__":
#     exchange_name = "binance"  # Specify the exchange
#     api_key = "your_api_key"
#     api_secret = "your_api_secret"
#     data_folder = "./data"
#     time_column = "timestamp"
#     freq = "1m"  # Example frequency
#     symbols = ["BTC/USDT", "ETH/USDT"]  # List of trading pairs

#     # Download klines
#     df = download_klines(
#         exchange_name, api_key, api_secret, data_folder, time_column, freq, symbols
#     )
#     # Retrieve exchange info
#     get_exchange_info(exchange_name)
#     # Retrieve account info
#     account_info = get_account_info(exchange_name, api_key, api_secret)
#     print(account_info)
#     # Retrieve market info
#     market_info = get_market_info(exchange_name, "BTC/USDT")
#     print(market_info)
