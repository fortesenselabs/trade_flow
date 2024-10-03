from typing import Optional, Tuple
import os
import pkgutil
import toml
import jsonschema
import pandas as pd
from sklearn.model_selection import train_test_split
from trade_flow.core.component import Component
from trade_flow.environments import __path__ as environments_path
from trade_flow.environments.default import informers, observers, renderers, stoppers
from trade_flow.environments.generic.components.action_scheme import ActionScheme
from trade_flow.environments.generic.components.observer import Observer
from trade_flow.environments.generic.components.renderer import AggregateRenderer
from trade_flow.environments.generic.components.reward_scheme import RewardScheme
from trade_flow.environments.generic.environment import TradingEnvironment
from trade_flow.feed import Stream, DataFeed, NameSpace


def get_available_environments() -> list[tuple]:
    """
        List available environments in Trade Flow, using environment.toml files for information.

    Returns:
        A list of tuples, where each tuple contains the environment name, version, and description.
    """
    schema = {
        "type": "object",
        "required": ["environment"],
        "properties": {
            "environment": {
                "type": "object",
                "required": ["name", "version", "description", "type", "engine"],
                "properties": {
                    "name": {"type": "string"},
                    "version": {"type": "string"},
                    "description": {"type": "string"},
                    "type": {"type": "string"},
                    "engine": {"type": "string"},
                },
            },
        },
    }

    try:
        environments = []

        for module_info in pkgutil.iter_modules(environments_path):
            environment_toml_path = os.path.join(
                f"{environments_path[0]}/{module_info.name}", "metadata.toml"
            )

            if os.path.exists(environment_toml_path):
                try:
                    with open(environment_toml_path, "r") as f:
                        environment_config = toml.load(f)
                        jsonschema.validate(environment_config, schema)
                        environment_name = environment_config["environment"]["name"]
                        environment_version = environment_config["environment"]["version"]
                        environment_description = environment_config["environment"]["description"]
                        environments.append(
                            (environment_name, environment_description, environment_version)
                        )
                except FileNotFoundError as e:
                    raise ValueError(
                        f"Environment.toml file not found for {environments_path}: {e}"
                    )
                except KeyError as e:
                    raise ValueError(
                        f"Missing required field in environment.toml for {environments_path}: {e}"
                    )
                except jsonschema.ValidationError as e:
                    raise ValueError(f"Invalid environment.toml for {environments_path}: {e}")

        return environments
    except Exception as e:
        raise ValueError(f"Error listing environments: {e}") from e


def create_env_from_dataframe(
    name: str,
    dataset: pd.DataFrame,
    portfolio: Component,
    action_scheme: ActionScheme,
    reward_scheme: RewardScheme,
    window_size: int = 1,
    min_periods: Optional[int] = 100,
    random_start_pct: float = 0.00,
    observer: Optional[Observer] = None,
    **kwargs,
) -> TradingEnvironment:
    """Creates a `TradingEnvironment` from a dataframe.

    Parameters
    ----------
    name : `str`
        The name to be used by the environment.
    dataset : `pd.DataFrame`
        The dataset to be used by the environment.
    portfolio : `Component`
        The portfolio component to be used by the environment.
    action_scheme : `ActionScheme`
        The action scheme for computing actions at every step of an episode.
    reward_scheme : `RewardScheme`
        The reward scheme for computing rewards at every step of an episode.
    window_size : int
        The size of the look back window to use for the observation space.
    min_periods : int, optional
        The minimum number of steps to warm up the `feed`.
    random_start_pct : float, optional
        Whether to randomize the starting point within the environment at each
        observer reset, starting in the first X percentage of the sample
    **kwargs : keyword arguments
        Extra keyword arguments needed to build the environment.

    Returns
    -------
    `TradingEnvironment`

        The default trading environment.
    """

    # Create a namespace for the environment
    with NameSpace(name):
        # Create streams from the dataset columns
        streams = [
            Stream.source(dataset[c].tolist(), dtype=dataset[c].dtype).rename(c)
            for c in dataset.columns
        ]

    # Create a data feed from the streams
    feed = DataFeed(streams)

    # Set the portfolio in the action scheme
    action_scheme.portfolio = portfolio

    # Create an observer with the portfolio, feed, and other parameters
    if observer is None:
        observer = observers.TradeFlowObserver(
            portfolio=portfolio,
            feed=feed,
            renderer_feed=kwargs.get("renderer_feed", None),
            window_size=window_size,
            min_periods=min_periods,
        )

    # Create a stopper with the maximum allowed loss
    stopper = stoppers.MaxLossStopper(max_allowed_loss=kwargs.get("max_allowed_loss", 0.5))

    # Create a renderer based on the provided renderer options
    renderer_list = kwargs.get("renderer", renderers.EmptyRenderer())

    if isinstance(renderer_list, list):
        # If multiple renderers are provided, create an aggregate renderer
        for i, r in enumerate(renderer_list):
            if isinstance(r, str):
                renderer_list[i] = renderers.get(r)
        renderer = AggregateRenderer(renderer_list)
    else:
        # If a single renderer is provided, use it directly
        if isinstance(renderer_list, str):
            renderer = renderers.get(renderer_list)
        else:
            renderer = renderer_list

    # Create the trading environment with the specified components
    env = TradingEnvironment(
        action_scheme=action_scheme,
        reward_scheme=reward_scheme,
        observer=observer,
        stopper=kwargs.get("stopper", stopper),
        informer=kwargs.get("informer", informers.TradeFlowInformer()),
        renderer=renderer,
        min_periods=min_periods,
        random_start_pct=random_start_pct,
    )

    return env


def train_test_split_env(
    dataset: pd.DataFrame, test_size: float = 0.2, seed: int = 42
) -> Tuple[TradingEnvironment, TradingEnvironment]:
    """
    Splits the environment into training and testing environments by
    splitting the underlying data it uses.

    This function assumes the TradingEnvironment has a method to reset
    with different data subsets.

    Args:
        dataset: The DataFrame to split.
        test_size: The proportion of data to allocate to the testing environment (default: 0.2).
        seed: Random seed for splitting the data (default: 42).

    Returns:
        Tuple[TradingEnvironment, TradingEnvironment]: The training and testing environments.
    """
    # Split the data using train_test_split
    train_data, test_data = train_test_split(dataset, test_size=test_size, random_state=seed)

    # Create new environments with the split data (assuming a reset_with_data method)
    train_env = create_env_from_dataframe(dataset=train_data)
    test_env = create_env_from_dataframe(dataset=test_data)

    return train_env, test_env
