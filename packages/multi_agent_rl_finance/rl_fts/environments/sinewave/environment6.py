'''
  Sinewave - Environment 6:
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
    Action Space: proportion-buy-sell-short-hold
    Reward Strategy: short-networth-change
'''

from tensortrade.oms.instruments import Instrument
from tensortrade.feed.core import DataFeed, Stream
from tensortrade.oms.exchanges import Exchange, ExchangeOptions
from tensortrade.oms.services.execution.simulated import execute_order
from tensortrade.oms.wallets import Wallet, Portfolio
import matplotlib.pyplot as plt

from rl_fts.tensortradeExtension.env.short import create
# --- Custom Code --- #
# Data
from rl_fts.environments.sinewave.data import SineWaveDataGenerator
# Action Schemes
from rl_fts.tensortradeExtension.actions import get as getAction
# Reward Schemes
from rl_fts.tensortradeExtension.rewards import get as getReward
# Renderer
from rl_fts.tensortradeExtension.renderer.shPositionChangeChart import PositionChangeChart
from rl_fts.tensortradeExtension.renderer.emptyRenderer import EmptyRenderer

def generate_env(dataframe, config):
  # create price stream
  price_stream = Stream.source(list(dataframe['price']), dtype="float").rename("USD-TTC")
  # create exchange
  sinewave_exchange = Exchange("sine-wave", service=execute_order, options=ExchangeOptions(commission=0.01))(
    price_stream
  )
  # setup financial instruments
  USD = Instrument("USD", 8, "U.S. Dollar")
  TTC = Instrument("TTC", 8, "TensorTrade Coin")
  # setup wallets
  cash = Wallet(sinewave_exchange, 100 * USD)
  asset = Wallet(sinewave_exchange, 0 * TTC)
  deposit_margin = Wallet(sinewave_exchange, 0 * USD)
  broker_asset = Wallet(sinewave_exchange, 0 * TTC)
  broker_cash = Wallet(sinewave_exchange, 0 * USD)
  profit_wallet = Wallet(sinewave_exchange, 0 * USD)
  # create the profit portfolio
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
  reward_scheme = getReward('short-networth-change')(
    starting_value = cash.balance.as_float()
  )
  # set action scheme
  action_scheme = getAction('proportion-buy-sell-short-hold')(
    cash=cash,
    asset=asset,
    profit_wallet=profit_wallet,
    portfolio=portfolio,
    broker_asset=broker_asset,
    broker_cash=broker_cash,
    deposit_margin=deposit_margin,
  )
  # create the render feed
  renderer_feed = DataFeed([
    Stream.source(dataframe["price"], dtype="float").rename("price"),
    Stream.sensor(action_scheme, lambda s: s.action, dtype="float").rename("action")
  ])
  renderer = EmptyRenderer()
  if ('render_env' in config and config["render_env"] == True):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5), clear=True)
    plt.tight_layout()
    fig.suptitle("Performance")
    renderer = PositionChangeChart(fig, ax1, ax2)
  # create the environment
  environment = create(
    feed=feed,
    portfolio=portfolio,
    action_scheme=action_scheme,
    reward_scheme=reward_scheme,
    renderer_feed=renderer_feed,
    renderer=renderer,
    window_size=config["window_size"], # number of previous time series datapoints to use as the observation
    min_periods=config["min_periods"], # minimum number of time series datapoints used for warm up
    max_allowed_loss=config["max_allowed_loss"], # % of allowed loss on starting funds
  )
  return environment

# -- HELPER FUNCTIONS --#
def create_env(config):
  # create the data generator
  data_generator = SineWaveDataGenerator(period=config["period"], x_sample=config["trading_days"])
  if config["type"] == "train":
    dataframe = data_generator.train()
  elif config["type"] == "eval":
    dataframe = data_generator.validate()
  else:
    dataframe = data_generator.test()
  return generate_env(dataframe, config)