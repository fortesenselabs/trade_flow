# tensortrade Environment
from tensortrade.oms.instruments import Instrument
from tensortrade.env import default
from tensortrade.feed.core import DataFeed, Stream
from tensortrade.oms.exchanges import Exchange, ExchangeOptions
from tensortrade.oms.services.execution.simulated import execute_order
from tensortrade.oms.wallets import Wallet, Portfolio
import matplotlib.pyplot as plt
import numpy as np

# --- Custom Code --- #
# Env
from rl_fts.tensortradeExtension.env.standard import create
# Data
from rl_fts.environments.stock.data import StockDataGenerator
# Action Schemes
from rl_fts.tensortradeExtension.actions import BSH
# Reward Schemes
from rl_fts.tensortradeExtension.rewards.proportional_net_worth_change import PNWC
# Renderer
from rl_fts.tensortradeExtension.renderer.stockEnvironment1 import Chart

def generate_env(dataframe, config):
    # create price stream
    price_stream = Stream.source(
        list(dataframe['Close']), dtype="float").rename("USD-NFLX")
    # create exchange
    nflx_exchange = Exchange("NASDAQ", service=execute_order)(
        price_stream
    )
    # setup financial instruments
    USD = Instrument("USD", 8, "U.S. Dollar")
    NFLX = Instrument("NFLX", 8, "NFLX Stock")
    cash = Wallet(nflx_exchange, 100 * USD)
    asset = Wallet(nflx_exchange, 0 * NFLX)
    # creat portfolio
    portfolio = Portfolio(USD, [
        cash,
        asset
    ])
    # create data feed
    feed = DataFeed([
        price_stream,
        price_stream.rolling(window=10).mean().rename("fast"),
        price_stream.rolling(window=20).mean().rename("medium"),
        price_stream.rolling(window=30).mean().rename("slow"),
        price_stream.log().diff().fillna(0).rename("lr")
    ])
    # set reward scheme
    reward_scheme = PNWC(
        starting_value=cash.balance.as_float()
    )
    # set action scheme
    action_scheme = BSH(
        cash=cash,
        asset=asset
    )
    # create the render feed
    renderer_feed = DataFeed([
        Stream.source(dataframe["Close"], dtype="float").rename("price"),
        price_stream.rolling(window=10).mean().rename("fast"),
        price_stream.rolling(window=20).mean().rename("medium"),
        price_stream.rolling(window=30).mean().rename("slow"),
        price_stream.log().diff().fillna(0).rename("lr"),
        Stream.sensor(action_scheme, lambda s: s.action,
                      dtype="float").rename("action")
    ])
    renderer = default.renderers.EmptyRenderer()
    if ('render_env' in config and config["render_env"] == True):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5), clear=True)
        plt.tight_layout()
        fig.suptitle("Performance")
        renderer = Chart(ax1, ax2)
    # create the environment
    environment = create(
        feed=feed,
        portfolio=portfolio,
        action_scheme=action_scheme,
        reward_scheme=reward_scheme,
        renderer_feed=renderer_feed,
        renderer=renderer,
        config=config,
        # number of previous time series datapoints to use as the observation
        window_size=config["window_size"],
        # minimum number of time series datapoints used for warm up
        min_periods=config["min_periods"],
        # % of allowed loss on starting funds
        max_allowed_loss=config["max_allowed_loss"],
    )
    return environment

# -- HELPER FUNCTIONS --#
def create_env(config):
    # create the data generator
    data_generator = StockDataGenerator(
        ticker="NFLX", interval="1d", start="2012-12-31", end="2022-12-31")
    if config["type"] == "train":
        dataframe = data_generator.train()
    elif config["type"] == "eval":
        dataframe = data_generator.validate()
    else:
        dataframe = data_generator.test()
    return generate_env(dataframe, config)

def normalization_info():
    data_generator = data_generator = StockDataGenerator(ticker="NFLX", interval="1d", start="2012-12-31", end="2022-12-31")
    training_data = data_generator.train()
    obs_1 = training_data['Close'].values
    obs_2 = training_data['Close'].rolling(window=10).mean().fillna(0).values
    obs_3 = training_data['Close'].rolling(window=20).mean().fillna(0).values
    obs_4 = training_data['Close'].rolling(window=30).mean().fillna(0).values
    obs_5 = np.log(training_data['Close']).diff().fillna(0).values

    observation_data = np.array([obs_1, obs_2, obs_3, obs_4, obs_5])
    mean = observation_data.mean(axis=1)
    var = observation_data.var(axis=1)
    return {
        "min": training_data['Close'].values.min(),
        "max": training_data['Close'].values.max(),
        "mean": mean,
        "var": var
    }

# Helper Functions
def get_reward_clipping(price_stream):
    biggest_gain = float('-inf')
    biggest_loss = float('inf')

    # at every time step
    for t in range(0, len(price_stream)-1):
        # Check the proportion difference in values
        proportional_price_difference = (
            price_stream[t+1] - price_stream[t]) / price_stream[t]
        # update biggest gain
        if proportional_price_difference > biggest_gain:
            biggest_gain = proportional_price_difference
        # update biggest loss
        if proportional_price_difference < biggest_loss:
            biggest_loss = proportional_price_difference
    return max(abs(biggest_loss), biggest_gain)

def get_max_episode_reward(data_stream):
    price_stream = data_stream
    episode_max_reward = 0
    for t in range(0, len(price_stream)-1):
        # if the price is going up
        if price_stream[t+1] > price_stream[t]:
            # get the reward
            proportional_price_difference = (price_stream[t+1] - price_stream[t]) / price_stream[t]
            # add the reward to the max
            episode_max_reward += proportional_price_difference
    return episode_max_reward

def reward_clipping_training(config):
    data_generator = StockDataGenerator(
        ticker="NFLX", interval="1d", start="2012-12-31", end="2022-12-31")
    training_data = data_generator.train().iloc[config['window_size']:]
    return get_reward_clipping(training_data["Close"].values)

def max_episode_reward_training(config):
    data_generator = StockDataGenerator(
        ticker="NFLX", interval="1d", start="2012-12-31", end="2022-12-31")
    training_data = data_generator.train().iloc[config['window_size']:]
    return get_max_episode_reward(training_data["Close"].values)

def max_episode_reward_evaluation(config):
    data_generator = StockDataGenerator(
        ticker="NFLX", interval="1d", start="2012-12-31", end="2022-12-31")
    training_data = data_generator().validate.iloc[config['window_size']:]
    return get_max_episode_reward(training_data["Close"].values)

def training_length():
    data_generator = StockDataGenerator(
        ticker="NFLX", interval="1d", start="2012-12-31", end="2022-12-31")
    training_data = data_generator.train()
    return len(training_data)

def evaluation_length():
    data_generator = StockDataGenerator(
        ticker="NFLX", interval="1d", start="2012-12-31", end="2022-12-31")
    training_data = data_generator.validate()
    return len(training_data)
