from typing import Optional, Tuple, Union
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
from trade_flow.environments.generic.components.stopper import Stopper
from trade_flow.environments.generic.environment import TradingEnvironment
from trade_flow.feed import Stream, DataFeed, NameSpace


def get_available_environments() -> list[tuple]:
    """
    List available environments in Trade Flow using environment metadata files.

    This function scans through the modules in the `trade_flow.environments` path,
    reads the `metadata.toml` files, and extracts relevant details like environment name,
    version, and description based on the expected schema.

    Returns
    -------
    list[tuple]
        A list of tuples, where each tuple contains:
        - `environment_name`: Name of the environment.
        - `environment_description`: Short description of the environment.
        - `environment_version`: Version of the environment.
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
                    "url": {"type": "string"},
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
                        environment_type = environment_config["environment"]["type"]
                        environment_engine = environment_config["environment"]["engine"]
                        environment_url = environment_config["environment"]["url"]
                        environments.append(
                            (
                                environment_name,
                                environment_description,
                                environment_version,
                                environment_type,
                                environment_engine,
                                environment_url,
                            )
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
    action_scheme: ActionScheme,
    reward_scheme: RewardScheme,
    window_size: int = 1,
    min_periods: Optional[int] = 100,
    random_start_pct: float = 0.00,
    observer: Optional[Observer] = None,
    stopper: Optional[Stopper] = None,
    **kwargs,
) -> TradingEnvironment:
    """
    Creates a `TradingEnvironment` instance from a given DataFrame.

    This function initializes a trading environment using a provided dataset, portfolio,
    action scheme, and other configurable components.

    Parameters
    ----------
    name : str
        The name of the environment instance.
    dataset : pd.DataFrame
        The input dataset containing historical market data.
    action_scheme : ActionScheme
        The scheme for possible trading actions.
    reward_scheme : RewardScheme
        The reward scheme used to compute rewards.
    window_size : int, default=1
        The observation window size for the environment.
    min_periods : Optional[int], default=100
        Minimum number of observations required before trading.
    random_start_pct : float, default=0.00
        Percentage of the dataset for a randomized starting point.
    observer : Optional[Observer], default=None
        Custom observer, if not provided, the default is used.
    stopper : Optional[Stopper], default=None
        Custom stopper. If not provided, a `MaxLossStopper` is used with a loss threshold.
    **kwargs : Additional keyword arguments for other components.

    Returns
    -------
    TradingEnvironment
        A trading environment configured with the specified dataset, action scheme,
        reward scheme, observer, and other components.

    Raises
    ------
    AttributeError
        If the specified action scheme does not have a `portfolio` attribute.

    """
    # Check for the portfolio in the action scheme
    if not hasattr(action_scheme, "portfolio"):
        raise AttributeError("action scheme no attribute named portfolio.")

    # If split is not enabled, create a single environment
    with NameSpace(name):
        streams = [
            Stream.source(dataset[c].tolist(), dtype=dataset[c].dtype).rename(c)
            for c in dataset.columns
        ]

    # Create a data feed from the streams
    feed = DataFeed(streams)

    # Create the observer if not provided
    if observer is None:
        observer = observers.TradeFlowObserver(
            portfolio=kwargs.get("portfolio", None),
            feed=feed,
            renderer_feed=kwargs.get("renderer_feed", None),
            window_size=window_size,
            min_periods=min_periods,
        )

    # Create the stopper if not provided
    if stopper is None:
        stopper = stoppers.MaxLossStopper(max_allowed_loss=kwargs.get("max_allowed_loss", 0.5))

    # Create the renderer based on the provided renderer options
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
