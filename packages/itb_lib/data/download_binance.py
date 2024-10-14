import pandas as pd
import os
import json
from datetime import datetime
from binance.client import Client
from binance.streams import BinanceSocketManager
from binance.enums import *

from packages.itb_lib.utils import (
    klines_to_df,
    binance_freq_from_pandas,
)


def download_binance(api_key, api_secret, data_folder, time_column, freq, data_sources, save=True):
    """
    Retrieve historical klines from the Binance server.

    Args:
    - api_key: The API key for Binance.
    - api_secret: The API secret for Binance.
    - data_folder: The folder path where data will be stored.
    - time_column: The name of the column representing time in the data.
    - freq: The frequency of the data (Pandas frequency).
    - data_sources: A list of data sources containing folder names (symbols).
    - save: Boolean indicating whether to save the data to CSV files (default is True).

    Returns:
    - df: DataFrame containing the downloaded klines data.
    """
    client = Client(api_key=api_key, api_secret=api_secret)

    # Convert Pandas frequency to Binance frequency
    binance_freq = binance_freq_from_pandas(freq)
    print(f"Binance frequency: {binance_freq}")

    now = datetime.now()

    for ds in data_sources:
        quote = ds.get("folder")
        if not quote:
            print("ERROR: Folder is not specified.")
            continue

        print(f"Start downloading '{quote}' ...")
        file_path = os.path.join(data_folder, quote)
        os.makedirs(file_path, exist_ok=True)  # Ensure that folder exists
        file_name = os.path.join(file_path, f"klines.csv")

        # Get the latest klines to determine the latest available timestamp
        latest_klines = client.get_klines(symbol=quote, interval=binance_freq, limit=5)
        latest_ts = pd.to_datetime(latest_klines[-1][0], unit="ms")

        if os.path.isfile(file_name):
            df = pd.read_csv(file_name)
            df[time_column] = pd.to_datetime(df[time_column], format="ISO8601")
            oldest_point = df["timestamp"].iloc[-5]  # Use an older point to overwrite old data
            print(f"File found. Appending data for {quote} since {str(latest_ts)} to '{file_name}'")
        else:
            df = pd.DataFrame()  # New DataFrame for new data
            oldest_point = datetime(2017, 1, 1)  # Start from a defined old date
            print(f"File not found. Downloading all data for {quote} into '{file_name}'.")

        # Download klines from Binance
        klines = client.get_historical_klines(
            symbol=quote, interval=binance_freq, start_str=oldest_point.isoformat()
        )

        df = klines_to_df(klines, df)
        df = df.iloc[:-1]  # Remove the last row (incomplete kline)

        if save:
            df.to_csv(file_name, index=False)

        print(f"Finished downloading '{quote}'. Data stored in '{file_name}'")

    elapsed = datetime.now() - now
    print(f"Finished downloading data in {str(elapsed).split('.')[0]}")
    return df


def get_exchange_info(client):
    """
    Retrieve exchange information from Binance and save it as JSON.

    Args:
    - client: Binance Client instance.
    """
    exchange_info = client.get_exchange_info()
    with open("exchange_info.json", "w") as file:
        json.dump(exchange_info, file, indent=4)
    print("Exchange info saved to 'exchange_info.json'")


def get_account_info(client):
    """
    Retrieve account information including orders and trades.

    Args:
    - client: Binance Client instance.
    """
    orders = client.get_all_orders(symbol="BTCUSDT")
    trades = client.get_my_trades(symbol="BTCUSDT")
    info = client.get_account()
    status = client.get_account_status()
    details = client.get_asset_details()
    return info, status, details


def get_market_info(client):
    """
    Retrieve market information including order book depth.

    Args:
    - client: Binance Client instance.
    """
    depth = client.get_order_book(symbol="BTCUSDT")
    return depth


def minutes_of_new_data(client, symbol, freq, data):
    """
    Calculate the time range of new data for the given symbol and frequency.

    Args:
    - client: Binance Client instance.
    - symbol: Trading symbol.
    - freq: Frequency of the data (Binance frequency).
    - data: DataFrame containing existing data.

    Returns:
    - old: Timestamp of the last available data.
    - new: Timestamp of the latest entry from the server.
    """
    if len(data) > 0:
        old = data["timestamp"].iloc[-1]
    else:
        old = datetime.strptime("1 Jan 2017", "%d %b %Y")

    new_info = client.get_klines(symbol=symbol, interval=freq)
    new = pd.to_datetime(new_info[-1][0], unit="ms")

    return old, new


# Streaming functions (not fully implemented)
async def get_futures_klines_all(symbol, freq, save=False):
    """
    Retrieve futures klines data for the specified symbol.

    Args:
    - symbol: Trading symbol.
    - freq: Frequency of the data (Binance frequency).
    - save: Boolean indicating whether to save the data to CSV files.

    (This function requires aiohttp for asynchronous HTTP requests.)

    https://binance-docs.github.io/apidocs/testnet/en/#kline-candlestick-data
    https://fapi.binance.com - production
    https://testnet.binancefuture.com - test
    GET /fapi/v1/exchangeInfo: to get a list of symbolc
    GET /fapi/v1/klines: symbol*, interval*, startTime, endTime, limit
    """
    filename = "futures.csv"
    data_df = pd.read_csv(filename) if os.path.isfile(filename) else pd.DataFrame()

    # Implement Binance API calls for retrieving futures data here...

    # Placeholder for implementation
    return


def check_market_stream(client):
    """
    Check the market stream for live updates on trades, order books, and kline data.

    Args:
    - client: Binance Client instance.
    """
    bm = BinanceSocketManager(client)

    # Example of starting a trade socket
    conn_key = bm.start_trade_socket("BTCUSDT", message_fn)
    print(f"Trade socket started for 'BTCUSDT'.")

    # Example of starting a kline socket
    conn_key = bm.start_kline_socket("BTCUSDT", message_fn, interval=KLINE_INTERVAL_30MINUTE)
    print(f"Kline socket started for 'BTCUSDT'.")


# Note: message_fn needs to be defined for handling incoming messages.
def message_fn(msg):
    # print(f"Message type: {msg['e']}")
    print(msg)


def check_market_stream_multiplex(client):
    """
    Symbols in socket name must be lowercase i.e. bnbbtc@aggTrade, neobtc@ticker.
    Establishes a multiplexed socket for market data streams.

    Args:
    - client: Binance Client instance.
    """
    try:
        bm = BinanceSocketManager(client)
        conn_key = bm.start_multiplex_socket(["bnbbtc@aggTrade", "neobtc@ticker"], multiples_fn)
        print(f"Multiplex socket started with connection key: {conn_key}")
    except Exception as e:
        print(f"Error starting multiplex socket: {e}")


def multiples_fn(msg):
    print(f"stream: {msg['stream']} data: {msg['data']}")


def check_user_stream(client):
    """
    User streams (requires extra authentication):
    - Account Update Event - Return account updates.
    - Order Update Event - Returns individual order updates.
    - Trade Update Event - Returns individual trade updates.

    Args:
    - client: Binance Client instance.
    """
    try:
        bm = BinanceSocketManager(client)

        # The Manager handles keeping the socket alive.
        bm.start_user_socket(user_message_fn)
        print("User stream started successfully.")
    except Exception as e:
        print(f"Error starting user socket: {e}")


def user_message_fn(msg):
    print(f"Message type: {msg['e']}")
    print(msg)
