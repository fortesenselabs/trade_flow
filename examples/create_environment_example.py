from typing import Optional, Tuple, Union, Dict
import pandas as pd
from sklearn.model_selection import train_test_split
from trade_flow.agents.base import Agent
from trade_flow.environments.generic.environment import TradingEnvironment
from trade_flow.environments.utils import create_env_from_dataframe
from trade_flow.feed import Stream, Coinbase_BTCUSD_1h, Coinbase_BTCUSD_d
from trade_flow.environments.default.engine.exchanges import Exchange
from trade_flow.environments.default.engine.execution.simulated import execute_order
from trade_flow.environments.default.engine.instruments import USD, BTC
from trade_flow.environments.default.engine.wallet import Wallet
from trade_flow.environments.default.engine.portfolio import Portfolio
import trade_flow.environments.default as default
from trade_flow.agents import SB3Agent


def encode_symbols(data: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Encodes the currency symbols in the data using label encoding.

    Parameters:
    ----------
        data (pd.DataFrame): The DataFrame containing the data.

    Returns:
    -------
        Tuple[pd.DataFrame, Dict[str, int]]: The encoded DataFrame and the mapping dictionary.
    """
    symbols = data["symbol"].unique()
    vocabulary = {pair: i for i, pair in enumerate(symbols)}
    data["symbol_encoded"] = data["symbol"].apply(lambda pair: vocabulary[pair])
    return data, vocabulary


def create_portfolio(price_history: pd.DataFrame) -> Portfolio:
    """
    Creates a default portfolio with initial USD and BTC balance for a Coinbase exchange.

    Parameters:
    ----------
        price_history (pd.DataFrame): The DataFrame containing the price history.

    Returns:
    -------
        Portfolio: A trading portfolio containing USD and BTC.
    """
    coinbase = Exchange("coinbase", service=execute_order)(
        Stream.source(price_history["close"].tolist(), dtype=price_history["close"].dtype).rename(
            "USD-BTC"
        )  # TODO: fix Exception: No stream satisfies selector condition. for `multiple stream sources`
    )
    return Portfolio(
        USD,
        [
            Wallet(coinbase, 1000 * USD),
            Wallet(coinbase, 1 * BTC),
        ],
    )


def create_environment(
    df: pd.DataFrame = Coinbase_BTCUSD_d,
    split: bool = False,
    test_size: float = 0.2,
    seed: int = 42,
    shuffle: bool = False,
) -> Union[TradingEnvironment, Tuple[TradingEnvironment, TradingEnvironment]]:
    """
    Creates a trading environment using the provided dataset and configuration.

    Parameters:
    -----------
        df (pd.DataFrame): Input dataset containing market data.
        split (bool): Whether to split the dataset into train and test sets.
        test_size (float): Proportion of the dataset for testing.
        seed (int): Random seed for reproducibility.
        shuffle (bool): Whether to shuffle the data before splitting.

    Returns:
    -------
        Union[TradingEnvironment, Tuple[TradingEnvironment, TradingEnvironment]]:
            Single or tuple of trading environments based on the split parameter.
    """

    dataset = df.reset_index()

    # Preprocess and encode symbols
    dataset_encoded, vocabulary = encode_symbols(dataset)
    print(f"Vocabulary: {vocabulary}")

    # Create a portfolio and action scheme
    portfolio = create_portfolio(dataset_encoded[["close"]])
    action_scheme = default.actions.ManagedRiskOrders()
    action_scheme.portfolio = portfolio

    # Create a reward scheme
    reward_scheme = default.rewards.RiskAdjustedReturns()

    # Split dataset if required
    if split:
        train_data, test_data = train_test_split(
            dataset_encoded,
            test_size=test_size,
            random_state=seed,
            shuffle=shuffle,
        )

        print(train_data)

        portfolio = create_portfolio(train_data[["close"]])
        action_scheme.portfolio = portfolio
        train_env = create_env_from_dataframe(
            name="coinbase_train",
            dataset=train_data,
            action_scheme=action_scheme,
            reward_scheme=reward_scheme,
            window_size=5,
            portfolio=portfolio,
        )

        # portfolio = create_portfolio(test_data[["date", "open", "high", "low", "close", "volume"]])
        # action_scheme.portfolio = portfolio
        test_env = create_env_from_dataframe(
            name="coinbase_test",
            dataset=test_data,
            action_scheme=action_scheme,
            reward_scheme=reward_scheme,
            window_size=5,
            portfolio=portfolio,
        )
        return train_env, test_env

    # Create a single environment if no split
    return create_env_from_dataframe(
        name="coinbase_env",
        dataset=dataset_encoded[["symbol_encoded", "volume_btc"]],
        action_scheme=action_scheme,
        reward_scheme=reward_scheme,
        window_size=5,
    )


def evaluate_model(env: TradingEnvironment, agent: Agent, n_steps: int = 100):
    """
    Evaluate the trained model in a given trading environment.

    Args:
        env (TradingEnvironment): The trading environment to evaluate.
        agent (Agent): The agent to evaluate in the environment.
        n_steps (int): Number of steps to run in the evaluation.
    """
    obs = env.reset()
    for step in range(n_steps):
        print(f"Observation at step {step}: {obs}")

        # Take a random action for evaluation purposes (use agent's action for real evaluations)
        action = env.action_space.sample()
        obs, reward, done, _, _ = env.step(action)
        env.render()

        if done:
            print(f"Episode finished after {step + 1} steps.")
            break


def train_and_evaluate(
    train_env: TradingEnvironment,
    test_env: TradingEnvironment,
    n_episodes: int = 2,
    n_steps: int = 1000,
):
    """
    Train an agent on the training environment and evaluate on the test environment.

    Args:
        train_env (TradingEnvironment): Training environment.
        test_env (TradingEnvironment): Testing environment.
        n_episodes (int): Number of episodes to train the agent.
        n_steps (int): Number of steps per episode.
    """
    agent = SB3Agent(train_env)
    agent.get_model("a2c", {"policy": "MlpPolicy"})
    print(f"Agent: {agent}")

    agent.train(n_episodes=n_episodes, n_steps=n_steps, progress_bar=True)
    performance = pd.DataFrame.from_dict(
        train_env.action_scheme.portfolio.performance, orient="index"
    )
    print("Training performance: \n", performance)
    performance.plot()

    print("Evaluating on test environment...")
    evaluate_model(test_env, agent)


if __name__ == "__main__":
    # Create environments for training and testing
    train_env, test_env = create_environment(Coinbase_BTCUSD_1h, split=True)

    # Train the agent and evaluate performance
    train_and_evaluate(train_env, test_env)
