"""
Provides a Generic Environment tool set
"""
from typing import Tuple
from gymnasium.envs.registration import register as register_gym_env
from sklearn.model_selection import train_test_split

from trade_flow.environments.generic.components.reward_scheme import RewardScheme
from trade_flow.environments.generic.components.action_scheme import ActionScheme
from trade_flow.environments.generic.components.observer import Observer
from trade_flow.environments.generic.components.stopper import Stopper
from trade_flow.environments.generic.components.informer import Informer
from trade_flow.environments.generic.components.renderer import Renderer
from trade_flow.environments.generic.environment import TradingEnvironment


def train_test_split_env(
    env: TradingEnvironment, test_size: float = 0.2, seed: int = 42
) -> Tuple[TradingEnvironment, TradingEnvironment]:
    """
    Splits the environment into training and testing environments by
    splitting the underlying data it uses.

    This function assumes the TradingEnvironment has a method to reset
    with different data subsets. 

    Args:
        env: The TradingEnvironment to split.
        test_size: The proportion of data to allocate to the testing environment (default: 0.2).
        seed: Random seed for splitting the data (default: 42).

    Returns:
        Tuple[TradingEnvironment, TradingEnvironment]: The training and testing environments.
    """

    # Extract data (assuming env has a method to get data)
    data = env.get_data()

    # Split the data using train_test_split
    train_data, test_data = train_test_split(data, test_size=test_size, random_state=seed)

    # Create new environments with the split data (assuming a reset_with_data method)
    train_env = TradingEnvironment(reset_with_data=train_data)
    test_env = TradingEnvironment(reset_with_data=test_data)

    return train_env, test_env