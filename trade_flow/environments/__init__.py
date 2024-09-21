# This module for everything related to environments and their exchanges/brokers.
#
# This module was heavily lifted from https://github.com/tensortrade-org/tensortrade
#
# The following are organized by system environment context:
# - Train: Historical data with simulated venues For training RL Agents
# - **Backtest:** Historical data with simulated venues for testing RL Agents
# - **Sandbox:** Real-time data with simulated venues
# - **Live:** Real-time data with live venues (paper trading or real accounts)

import os
import pkgutil
import toml
import jsonschema
from trade_flow.environments import generic
from trade_flow.environments import default
from trade_flow.environments import nautilus_trader
from trade_flow.environments import __path__ as environments_path


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
