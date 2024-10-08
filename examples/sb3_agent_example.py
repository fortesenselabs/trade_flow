import tqdm
import pandas as pd

# import pandas_ta as ta

# import trade_flow
from trade_flow.agents.base import Agent
from trade_flow.environments.generic.environment import TradingEnvironment
from trade_flow.feed import Stream, DataFeed, NameSpace, Coinbase_BTCUSD_1h, Coinbase_BTCUSD_d
from trade_flow.environments.default.oms.exchanges import Exchange
from trade_flow.environments.default.oms.execution.simulated import execute_order
from trade_flow.environments.default.oms.instruments import USD, BTC
from trade_flow.environments.default.oms.wallet import Wallet
from trade_flow.environments.default.oms.portfolio import Portfolio
from trade_flow.environments.default.renderers import PlotlyTradingChart, FileLogger
import trade_flow.environments.default as default
from trade_flow.agents import SB3Agent
from stable_baselines3.common.callbacks import BaseCallback


# ProgressBarCallback for model.
class ProgressBarCallback(BaseCallback):

    def __init__(self, check_freq: int = 100, verbose: int = 1):
        super().__init__(verbose)
        self.check_freq = check_freq

    def _on_training_start(self) -> None:
        """
        This method is called before the first rollout starts.
        """
        self.progress_bar = tqdm(total=self.model._total_timesteps, desc="model.learn()")

    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq == 0:
            self.progress_bar.update(self.check_freq)
        return True

    def _on_training_end(self) -> None:
        """
        This event is triggered before exiting the `learn()` method.
        """
        self.progress_bar.close()


def encode_symbols(data):
    """Encodes the currency symbols in the data using one-hot or label encoding.

    Args:
        data (pandas.DataFrame): The DataFrame containing the data.

    Returns:
        pandas.DataFrame: The DataFrame with the one-hot encoded symbols.
    """

    # Extract currency pairs
    symbols = data["symbol"].unique()

    # Create a vocabulary mapping
    vocabulary = {pair: i for i, pair in enumerate(symbols)}

    data["symbol_encoded"] = data["symbol"].apply(lambda pair: vocabulary[pair])

    # One-hot encode the symbols
    # data = pd.get_dummies(data, columns=["symbol_encoded"], prefix="")

    return data, vocabulary


def get_env(df: pd.DataFrame = Coinbase_BTCUSD_d):
    print("df.head(): ", df.head())

    dataset = df.reset_index()
    print("dataset.head(3): ", dataset.head(3))

    price_history = dataset[["date", "open", "high", "low", "close", "volume"]]  # chart data
    print("price_history: ", price_history.head(3))

    dataset.drop(columns=["date", "open", "high", "low", "close", "volume"], inplace=True)
    print("dataset: ", dataset)

    dataset_encoded, vocabulary = encode_symbols(dataset)
    print("vocabulary: ", vocabulary)
    print("dataset_encoded: ", dataset_encoded)

    dataset_encoded = dataset_encoded[["symbol_encoded", "volume_btc"]]
    print("dataset_encoded: ", dataset_encoded)

    selected_dataset = dataset_encoded
    print("selected_dataset: ", selected_dataset)

    coinbase = Exchange("coinbase", service=execute_order)(
        Stream.source(price_history["close"].tolist(), dtype="float").rename("USD-BTC")
    )

    portfolio = Portfolio(
        USD,
        [
            Wallet(coinbase, 1000 * USD),
            Wallet(coinbase, 1 * BTC),
        ],
    )

    with NameSpace("coinbase"):
        streams = [
            Stream.source(selected_dataset[c].tolist(), dtype=selected_dataset[c].dtype).rename(c)
            for c in selected_dataset.columns
        ]

    feed = DataFeed(streams)
    print("feed.next(): ", feed.next())

    env = default.create(
        portfolio=portfolio,
        action_scheme="managed-risk",
        reward_scheme="risk-adjusted",
        feed=feed,
        renderer="screen-log",  # ScreenLogger used with default settings
        window_size=20,
    )
    return env


def get_env_with_multiple_renderers(df: pd.DataFrame = Coinbase_BTCUSD_d):
    print("df.head(): ", df.head())

    dataset = df.reset_index()
    print("dataset.head(3): ", dataset.head(3))

    price_history = dataset[["date", "open", "high", "low", "close", "volume"]]  # chart data
    print("price_history: ", price_history.head(3))

    dataset.drop(columns=["date", "volume"], inplace=True)
    print("dataset: ", dataset)

    dataset_encoded, vocabulary = encode_symbols(dataset)
    print("vocabulary: ", vocabulary)
    print("dataset_encoded: ", dataset_encoded)

    dataset_encoded = dataset_encoded[
        ["symbol_encoded", "open", "high", "low", "close", "volume_btc"]
    ]
    print("dataset_encoded: ", dataset_encoded)

    selected_dataset = dataset_encoded
    print("selected_dataset: ", selected_dataset)

    coinbase = Exchange("coinbase", service=execute_order)(
        Stream.source(price_history["close"].tolist(), dtype="float").rename("USD-BTC")
    )  # TODO: fix Exception: No stream satisfies selector condition. for `multiple stream sources`

    portfolio = Portfolio(
        USD,
        [
            Wallet(coinbase, 1000 * USD),
            Wallet(coinbase, 1 * BTC),
        ],
    )

    with NameSpace("coinbase"):
        streams = [
            Stream.source(selected_dataset[c].tolist(), dtype="float").rename(c)
            for c in selected_dataset.columns
        ]

    feed = DataFeed(streams)
    print("feed.next(): ", feed.next())

    renderer_feed = DataFeed(
        [Stream.source(price_history[c].tolist(), dtype="float").rename(c) for c in price_history]
    )

    chart_renderer = PlotlyTradingChart(
        display=True,  # show the chart on screen (default)
        height=800,  # affects both displayed and saved file height. None for 100% height.
        save_format="html",  # save the chart to an HTML file
        auto_open_html=True,  # open the saved HTML chart in a new browser tab
    )

    file_logger = FileLogger(
        filename="coinbase.log",  # omit or None for automatic file name
        path="training_logs",  # create a new directory if doesn't exist, None for no directory
    )

    env = default.create(
        portfolio=portfolio,
        action_scheme="managed-risk",
        reward_scheme="risk-adjusted",
        feed=feed,
        window_size=5,
        renderer_feed=renderer_feed,
        renderer=[chart_renderer, file_logger],
    )
    return env


def evaluate_model(env: TradingEnvironment, agent: Agent):
    """
    Evaluate the model
    """
    obs = env.reset()
    for i in range(100):
        print(obs)
        # action, _states = agent.predict(obs[0])

        # Take a random action
        action = env.action_space.sample()

        obs, reward, done, _, info = env.step(action)
        env.render()

        if done:
            print(f"Episode finished after {i + 1} steps")
            break


if __name__ == "__main__":
    env = get_env(Coinbase_BTCUSD_1h)  # df = Coinbase_BTCUSD_d  | Coinbase_BTCUSD_1h

    agent = SB3Agent(env)
    agent.get_model("a2c", {"policy": "MlpPolicy"})
    print("agent: ", agent)
    agent.train(
        n_episodes=2,
        n_steps=1000,
        progress_bar=True,
        # callbacks=[ProgressBarCallback(100)]
    )

    performance = pd.DataFrame.from_dict(env.action_scheme.portfolio.performance, orient="index")
    print(performance)

    performance.plot()

    # evaluate_model(env, agent)

    print("\n\n---------Environment with Multiple Renderers-------------\n\n")

    env_multiple = get_env_with_multiple_renderers(
        Coinbase_BTCUSD_1h
    )  # df = Coinbase_BTCUSD_d  | Coinbase_BTCUSD_1h
    agent = SB3Agent(env_multiple)
    agent.get_model("dqn", {"policy": "MlpPolicy"})
    print("agent: ", agent)
    agent.train(
        n_episodes=10,
        n_steps=1000,
        progress_bar=True,
        # callbacks=[ProgressBarCallback(100)]
    )

    performance = pd.DataFrame.from_dict(
        env_multiple.action_scheme.portfolio.performance, orient="index"
    )
    print(performance)

    performance.plot()

    performance.net_worth.plot()

    # evaluate_model(env, agent)
