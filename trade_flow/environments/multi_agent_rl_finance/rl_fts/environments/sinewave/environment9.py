'''
  Sinewave - Environment 1:
    Data: Generated Sinewave
      Training: 5 peaks
      Evaluation: 2 peaks
      Testing: 3 peaks
    Observation Space: 
      price values,
      price -> rolling mean (10 data points),
      price -> rolling mean (20 data points),
      price -> rolliong mean (30 data points),
      price -> log difference
    Action Space: buy-sell-hold
    Reward Strategy: net-worth-change
'''

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
# Environment
from rl_fts.tensortradeExtension.env.standard import create
# Data
from rl_fts.environments.sinewave.data import SineWaveDataGenerator
# Action Schemes
from rl_fts.tensortradeExtension.actions import BSH
# Reward Schemes
from rl_fts.tensortradeExtension.rewards.proportional_reward import NWC, get_reward_clipping, get_max_episode_reward, get_max_net_worth
# Renderer
from rl_fts.tensortradeExtension.renderer.bhsPositionChangeChart import PositionChangeChart

def generate_env(dataframe, config):
  # create price stream
  price_stream = Stream.source(list(dataframe['price']), dtype="float").rename("USD-TTC")
  # create exchange
  sinewavee_xchange = Exchange("sine-wave", service=execute_order, options=ExchangeOptions(commission=0.01))(
    price_stream
  )
  # setup financial instruments
  USD = Instrument("USD", 8, "U.S. Dollar")
  TTC = Instrument("TTC", 8, "TensorTrade Coin")
  cash = Wallet(sinewavee_xchange, 100 * USD)
  asset = Wallet(sinewavee_xchange, 0 * TTC)
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
  reward_scheme = NWC(
    starting_value=cash.balance.as_float()
  )
  # set action scheme
  action_scheme = BSH(
    cash=cash,
    asset=asset
  )
  # create the render feed
  renderer_feed = DataFeed([
    Stream.source(dataframe["price"], dtype="float").rename("price"),
    Stream.sensor(action_scheme, lambda s: s.action, dtype="float").rename("action")
  ])
  renderer = default.renderers.EmptyRenderer()
  if ('render_env' in config and config["render_env"] == True):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5), clear=True)
    plt.tight_layout()
    fig.suptitle("Performance")
    renderer = PositionChangeChart(ax1, ax2)
  # create the environment
  environment = create(
    feed=feed,
    portfolio=portfolio,
    action_scheme=action_scheme,
    reward_scheme=reward_scheme,
    renderer_feed=renderer_feed,
    renderer=renderer,
    config=config,
    window_size=config["window_size"], # number of previous time series datapoints to use as the observation
    min_periods=config["min_periods"], # minimum number of time series datapoints used for warm up
    max_allowed_loss=config["max_allowed_loss"], # % of allowed loss on starting funds
  )
  return environment

# -- HELPER FUNCTIONS --#
def create_env(config):
  # create the data generator
  data_generator = SineWaveDataGenerator(period=config["period"], x_sample=config["trading_days"], d_ratio=config["d_ratio"])
  if config["type"] == "train":
    dataframe = data_generator.train()
  elif config["type"] == "eval":
    dataframe = data_generator.validate()
  else:
    dataframe = data_generator.test()
  return generate_env(dataframe, config)

def normalization_info(config):
  data_generator = SineWaveDataGenerator(period=config["period"], x_sample=config["trading_days"], d_ratio=config["d_ratio"])
  training_data = data_generator.train()
  obs_1 = training_data['price'].values
  obs_2 = training_data['price'].rolling(window=10).mean().fillna(0).values
  obs_3 = training_data['price'].rolling(window=20).mean().fillna(0).values
  obs_4 = training_data['price'].rolling(window=30).mean().fillna(0).values
  obs_5 = np.log(training_data['price']).diff().fillna(0).values

  observation_data = np.array([obs_1, obs_2, obs_3, obs_4, obs_5])
  mean=observation_data.mean(axis=1)
  var=observation_data.var(axis=1)
  return {
    "mean": mean,
    "var": var
  }

def reward_clipping(config):
  data_generator = SineWaveDataGenerator(period=config["period"], x_sample=config["trading_days"], d_ratio=config["d_ratio"])
  training_data = data_generator.train().iloc[config['window_size']:]
  return get_reward_clipping(training_data["price"].values)

def max_episode_reward(config):
  data_generator = SineWaveDataGenerator(period=config["period"], x_sample=config["trading_days"], d_ratio=config["d_ratio"])
  training_data = data_generator.train().iloc[config['window_size']:]
  return get_max_episode_reward(training_data["price"].values)

def max_net_worth(config):
  data_generator = SineWaveDataGenerator(period=config["period"], x_sample=config["trading_days"], d_ratio=config["d_ratio"])
  training_data = data_generator.train().iloc[config['window_size']:]
  return get_max_net_worth(training_data["price"].values, config['starting_cash'])