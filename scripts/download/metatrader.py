# IMPORTS
import click
import pandas as pd
import os.path
import json
import time
from pathlib import Path
from datetime import timedelta, datetime
from dateutil import parser
from tqdm import tqdm_notebook  # (Optional, used for progress-bars)

# import aiohttp
from tradeflow.metatrader.enums import TimeFrame
from tradeflow.metatrader.dwx import MetaTraderDataProcessor
from application.config import Settings
from application.logger import AppLogger
from application.models import AppConfig
from application.utils import mt_klines_to_df
from tradeflow.metatrader.services import KlinesService


logger = AppLogger(name=__name__)
DOWNLOADER_NAME = "MetaTrader"

#
# Historic data
#


@click.command()
@click.option(
    "--config_file", "-c", type=click.Path(), default="", help="Configuration file name"
)
def main(config_file):
    """
    Retrieving historic klines from metatrader server.

    Client.get_historical_klines
    """
    settings: Settings = Settings(config_file)
    logger.info(settings.model_dump())

    app_config: AppConfig = settings.get_app_config()

    time_column = app_config.config.time_column

    data_path = Path(app_config.config.data_folder)

    now = datetime.now()

    freq = app_config.config.freq  # Pandas frequency
    print(f"Pandas frequency: {freq}")

    freq = TimeFrame.freq_from_pandas(freq)
    print(f"{DOWNLOADER_NAME} frequency: {freq}")

    save = True

    client = MetaTraderDataProcessor(app_config.config.mt_directory_path)

    data_sources = app_config.config.data_sources
    for ds in data_sources:
        # Assumption: folder name is equal to the symbol name we want to download
        quote = ds.folder
        if not quote:
            logger.warn("ERROR. Folder is not specified.")
            continue

        print(f"Start downloading '{quote}' ...")

        file_path = Path(data_path / quote)
        file_path.mkdir(parents=True, exist_ok=True)  # Ensure that folder exists

        file_name = (file_path / "klines").with_suffix(".csv")

        # Get a few latest klines to determine the latest available timestamp
        # klines_service = KlinesService(client).symbol(quote).interval(freq).limit(5)
        # start_time, end_time = parse_time(
        #     request.interval,
        #     (
        #         datetime.fromtimestamp(request.start_time)
        #         if request.start_time is not None
        #         else None
        #     ),
        #     (
        #         datetime.fromtimestamp(request.end_time)
        #         if request.start_time is not None
        #         else None
        #     ),
        #     request.limit,
        # )

        latest_klines = None
        for i in range(5):
            latest_klines = client.get_historical_klines(symbol=quote, time_frame=freq)
            if latest_klines is not None:
                break

            logger.error(f"Could not fetch klines, Retrying {i + 1}....")
            time.sleep(0.5)

        if latest_klines is None:
            logger.error(f"Could not fetch klines, Retry Failed")
            return

        logger.info(latest_klines[-1])

        latest_ts = pd.to_datetime(latest_klines[-1].time, unit="s", utc=True)

        if file_name.is_file():
            # Load the existing data in order to append newly downloaded data
            df = pd.read_csv(file_name)
            df[time_column] = pd.to_datetime(df[time_column], format="ISO8601")

            # oldest_point = parser.parse(data["timestamp"].iloc[-1])
            oldest_point = df["timestamp"].iloc[
                -5
            ]  # Use an older point so that new data will overwrite old data

            print(
                f"File found. Downloaded data for {quote} and {freq} since {str(latest_ts)} will be appended to the existing file {file_name}"
            )
        else:
            # No existing data so we will download all available data and store as a new file
            df = pd.DataFrame()

            oldest_point = datetime(2017, 1, 1)

            print(
                f"File not found. All data will be downloaded and stored in newly created file for {quote} and {freq}."
            )

        # delta_minutes = (latest_ts - oldest_point).total_seconds() / 60
        # binsizes = {"1m": 1, "5m": 5, "1h": 60, "1d": 1440}
        # delta_lines = math.ceil(delta_minutes / binsizes[freq])

        # === Download from the remote server using metatrader client
        klines = client.get_historical_klines(
            symbol=quote,
            time_frame=freq,
            start=oldest_point.timestamp(),
            # end=latest_ts.isoformat()  # fetch everything up to now
        )

        # Convert list of Pydantic models to list of dictionaries and convert the list to dataframe
        df = mt_klines_to_df([kline.model_dump() for kline in klines], df)

        # Remove last row because it represents a non-complete kline (the interval not finished yet)
        df = df.iloc[:-1]

        if save:
            df.to_csv(file_name)

        print(f"Finished downloading '{quote}'. Stored in '{file_name}'")

    elapsed = datetime.now() - now
    print(f"Finished downloading data in {str(elapsed).split('.')[0]}")

    return df


#
# Static data
#


def get_exchange_info():
    """
    Client.get_exchange_info
    /api/v1/exchangeInfo
    """
    exchange_info = client.get_exchange_info()

    with open("exchange_info.json", "w") as file:
        json.dump(exchange_info, file, indent=4)  # , sort_keys=True

    return


def get_account_info():
    orders = App.client.get_all_orders(symbol="BTCUSDT")
    trades = App.client.get_my_trades(symbol="BTCUSDT")
    info = App.client.get_account()
    status = App.client.get_account_status()
    details = App.client.get_asset_details()


def get_market_info():
    depth = App.client.get_order_book(symbol="BTCUSDT")


#
# Utility
#


def minutes_of_new_data(symbol, freq, data):
    if len(data) > 0:
        # old = parser.parse(data["timestamp"].iloc[-1])
        old = data["timestamp"].iloc[-1]
    else:
        # old = datetime.strptime('1 Aug 2019', '%d %b %Y')
        old = datetime.strptime("1 Jan 2017", "%d %b %Y")

    # Get a few latest klines in order to determine timestamp of the latest entry. Size of the return array is limited by default parameters of the server
    # List of tuples like this: [1569728580000, '8156.65000000', '8156.66000000', '8154.75000000', '8155.32000000', '4.63288700', 1569728639999, '37786.23994297', 74, '3.18695100', '25993.68396886', '0']
    new_info = App.client.get_klines(symbol=symbol, interval=freq)
    new = pd.to_datetime(new_info[-1][0], unit="ms")

    return old, new


#
# Streaming functions (do not work - for test purposes)
#


# !!! DOES NOT WORK - do not use
async def get_futures_klines_all(symbol, freq, save=False):
    """
    https://binance-docs.github.io/apidocs/testnet/en/#kline-candlestick-data
    https://fapi.binance.com - production
    https://testnet.binancefuture.com - test
    GET /fapi/v1/exchangeInfo: to get a list of symbolc
    GET /fapi/v1/klines: symbol*, interval*, startTime, endTime, limit
    """

    filename = f"futures.csv"

    if os.path.isfile(filename):
        data_df = pd.read_csv(filename)
    else:
        data_df = pd.DataFrame()

    # INFO:
    # API-keys are passed into the Rest API via the X-MBX-APIKEY header
    # curl -H "X-MBX-APIKEY: vmPUZE6mv9SD5VNHk4HlWFsOr6aKE2zvsw0MuIgwCIPy6utIco14y7Ju91duEh8A"
    # API-secret is used to create a HMAC SHA256 signature and then pass it in the signature parameter
    # [linux]$ echo -n "symbol=LTCBTC&side=BUY&type=LIMIT&timeInForce=GTC&quantüity=1&price=0.1&recvWindow=5000&timestamp=1499827319559" | openssl dgst -sha256 -hmac "API-secret"
    # (stdin)= c8db56825ae71d6d79447849e617115f4a920fa2acdcab2b053c4b2838bd6b71 - signature

    import hmac
    import hashlib
    import urllib.parse

    headers = {"X-MBX-APIKEY": binance_api_key}

    params = {}
    query = urllib.parse.urlencode(params)  # These our parameters passed in url
    signature = hmac.new(
        binance_api_secret.encode("utf8"),
        query.encode("utf8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    params["signature"] = signature  # We simply add signature to the parametes

    #
    # Test connection (ping server): GET /fapi/v1/ping
    #
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, params=params) as response:
            print(response.status)
            result = await response.json()

    print(result)

    #
    # /fapi/v1/klines: symbol*, interval*, startTime, endTime, limit
    #

    start = 1483228800000  # 1483228800000 2017
    end = 1569888000000  # 1569888000000 2019-10-7, 1569888000000 - 2019-10-1

    params = {"symbol": symbol, "interval": freq, "startTime": start, "endTime": end}
    query = urllib.parse.urlencode(params)  # These our parameters passed in url
    signature = hmac.new(
        binance_api_secret.encode("utf8"),
        query.encode("utf8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    params["signature"] = signature  # We simply add signature to the parametes

    url = "https://fapi.binance.com/fapi/v1/klines"

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, params=params) as response:
            print(response.status)
            klines = await response.json()

    data_df = klines_to_df(klines, None)

    if save:
        data_df.to_csv(filename)


def check_market_stream():
    """
    Streams:
    - depth (order book):
        1) Order book price and quantity depth updates used to locally keep an order book
        2) Top 20 levels of bids and asks
    - kline: The kline/candlestick stream pushes updates to the current klines/candlestick every second
    - ticker,
    - trade,
    """
    bm = BinanceSocketManager(App.client)

    # trade socket (one event for each new trade - quote intensive)
    conn_key = bm.start_trade_socket("BTCUSDT", message_fn)
    # {'e': 'trade', 'E': 1570114844102, 's': 'BTCUSDT', 't': 185892444, 'p': '8090.33000000', 'q': '0.00247300', 'b': 682929714, 'a': 682929708, 'T': 1570114844098, 'm': False, 'M': True}

    # depths sockets: either partial book or diff response
    # partial book response
    # conn_key = bm.start_depth_socket('BTCUSDT', message_fn, depth=BinanceSocketManager.WEBSOCKET_DEPTH_5)
    # Output: {'lastUpdateId': 1142001769, 'bids': [['8097.09000000', '0.02469400'], ['8097.07000000', '0.13411300'], ['8097.02000000', '2.00000000'], ['8097.01000000', '0.55502000'], ['8096.91000000', '0.29088400']], 'asks': [['8099.01000000', '0.02640000'], ['8099.02000000', '0.06944200'], ['8099.07000000', '0.08537200'], ['8099.28000000', '0.50000000'], ['8100.54000000', '0.00372200']]}
    # depth diff response
    # conn_key = bm.start_depth_socket('BTCUSDT', message_fn)

    # kline socket
    conn_key = bm.start_kline_socket(
        "BTCUSDT", message_fn, interval=KLINE_INTERVAL_30MINUTE
    )
    # {'e': 'kline', 'E': 1570114725899, 's': 'BTCUSDT', 'k': {'t': 1570113000000, 'T': 1570114799999, 's': 'BTCUSDT', 'i': '30m', 'f': 185878257, 'L': 185891547, 'o': '8114.88000000', 'c': '8102.91000000', 'h': '8124.50000000', 'l': '8065.00000000', 'v': '1888.20453300', 'n': 13291, 'x': False, 'q': '15291535.03269335', 'V': '1004.09638500', 'Q': '8131835.50527485', 'B': '0'}}

    # Aggregated Trade Socket
    # conn_key = bm.start_aggtrade_socket('BTCUSDT', message_fn)
    # Trade Socket
    # conn_key = bm.start_trade_socket('BTCUSDT', message_fn)

    # Symbol ticker Socket
    # conn_key = bm.start_symbol_ticker_socket('BTCUSDT', message_fn)
    # Output: {'e': '24hrTicker', 'E': 1570114641432, 's': 'BTCUSDT', 'p': '-157.27000000', 'P': '-1.907', 'w': '8247.56704052', 'x': '8247.57000000', 'c': '8090.30000000', 'Q': '0.07074700', 'b': '8089.03000000', 'B': '0.09080800', 'a': '8090.29000000', 'A': '2.00000000', 'o': '8247.57000000', 'h': '8393.00000000', 'l': '8060.00000000', 'v': '28067.68120000', 'q': '231490082.36887328', 'O': 1570028241429, 'C': 1570114641429, 'F': 185628703, 'L': 185890956, 'n': 262254}

    # Ticker Socket
    # conn_key = bm.start_ticker_socket(message_fn)

    # Mini Ticker Socket
    # by default updates every second
    # conn_key = bm.start_miniticker_socket(message_fn)
    # this socket can take an update interval parameter
    # set as 5000 to receive updates every 5 seconds
    # conn_key = bm.start_miniticker_socket(message_fn, 5000)

    #
    # then start the socket manager
    #
    bm.start()

    time.sleep(10)

    # Close individual socket
    bm.stop_socket(conn_key)

    # stop all sockets and end the manager call close after doing this a start call would be required to connect any new sockets.
    bm.close()

    # to exist, stop twisted reactor loop - otherwise the code will NOT exist when you expect
    from twisted.internet import reactor

    reactor.stop()


def message_fn(msg):
    # print(f"Message type: {msg['e']}")
    print(msg)


def check_market_stream_multiplex():
    """
    Symbols in socket name must be lowercase i.e bnbbtc@aggTrade, neobtc@ticker
    """
    bm = BinanceSocketManager(App.client)
    conn_key = bm.start_multiplex_socket(
        ["bnbbtc@aggTrade", "neobtc@ticker"], multiples_fn
    )


def multiples_fn(msg):
    print("stream: {} data: {}".format(msg["stream"], msg["data"]))


def check_user_stream():
    """
    User streams (requires extra authentication):
    - Account Update Event - Return account updates
    - Order Update Event - Returns individual order updates
    - Trade Update Event - Returns individual trade updates
    """
    bm = BinanceSocketManager(App.client)

    # The Manager handles keeping the socket alive.
    bm.start_user_socket(user_message_fn)


def user_message_fn(msg):
    print(f"Message type: {msg['e']}")
    print(msg)


if __name__ == "__main__":
    main()
