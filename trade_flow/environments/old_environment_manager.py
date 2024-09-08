from typing import Dict, Optional, Union
import uuid
import json
import os
import ray
from ray.tune.registry import register_env
from trade_flow.common import Logger, EnvironmentMode
from trade_flow.core import AssetClass
from trade_flow.environments.generic import Venue
from trade_flow.environments.generic import TradingEnvironment
from trade_flow.environments.live import LiveEnvironment
from trade_flow.environments.nautilus_trader_sandbox.sandbox import SandboxEnvironment
from trade_flow.environments.nautilus_trader_backtest.backtest import BacktestEnvironment
from trade_flow.environments.gym_train.train import TrainingEnvironment


class EnvironmentManager:
    def __init__(
        self,
        mode: EnvironmentMode,
        venue: Venue,
        asset_class: AssetClass = AssetClass.FOREX,
        new: bool = True,
    ) -> None:
        """
        There is no need for a manager since all environment will have the same interface
        """
        self.logger = Logger(name=__class__.__name__)
        self.mode = mode
        self.asset_class = asset_class
        self.venue = venue

        self.environments: Dict[str, TradingEnvironment] = {}

        # Set the path to the JSON file relative to the current working directory
        self.env_ids_file = os.path.join(os.getcwd(), "training_environment_ids.json")

        if not new:
            self._load_env_ids()  # Load saved environment IDs

    # Fixed the Error: _pickle.PicklingError: logger cannot be pickled | source(s): https://stackoverflow.com/questions/2999638/how-to-stop-attributes-from-being-pickled-in-python/2999833#2999833
    def __getstate__(self):
        d = self.__dict__.copy()
        if "logger" in d:
            d["logger"] = d["logger"].name
        return d

    def __setstate__(self, d):
        if "logger" in d:
            d["logger"] = Logger(name=d["logger"])
        self.__dict__.update(d)

    def init(self) -> None:
        self.logger.info(f"Initializing environment for mode: {self.mode}")

        ray.init(ignore_reinit_error=True)  # Initialize Ray

        # Register a new training environment if not already done
        env_id = f"TradingEnv-{self.mode.value}-{uuid.uuid4()}"

        if self.mode == EnvironmentMode.LIVE:
            self.selected_environment = LiveEnvironment(self.venue_manager)
        elif self.mode == EnvironmentMode.SANDBOX:
            self.selected_environment = SandboxEnvironment(self.venue_manager)
        elif self.mode == EnvironmentMode.BACKTEST:
            self.selected_environment = BacktestEnvironment(self.venue_manager)
        elif self.mode == EnvironmentMode.TRAIN:
            self.create_environment(env_id, True)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

        self.environments[env_id] = self.selected_environment

    def _register_training_environment(self, env_id: str, save: bool = False):
        """Generates a unique environment ID, registers it with Ray, and saves it."""

        def create_env(env_config):
            """Environment creator function that creates a TrainingEnvironment."""
            return TrainingEnvironment(self.venue_manager, env_id, new_engine=True)

        try:
            # Register the environment with Ray
            register_env(env_id, create_env)

            # Check if environment was registered correctly
            # ray.rllib.utils.check_env(TrainingEnvironment(self.venue_manager, env_id))
            self.logger.info(f"Registered environment with ID: {env_id}")

            # Save the environment ID
            if save:
                self._save_env_id(env_id)

            # Create and assign the TrainingEnvironment instance | a dirty fix for the error => gymnasium.error.NameNotFound
            self.selected_environment = TrainingEnvironment(self.venue_manager, env_id)

        except ValueError:
            self.logger.error(f"Error registering environment with ID: {env_id}")

    def _save_env_id(self, env_id: str):
        """Saves the environment ID to a JSON file."""
        if os.path.exists(self.env_ids_file):
            with open(self.env_ids_file, "r") as file:
                data = json.load(file)
            env_ids = data.get("ids", [])
        else:
            env_ids = []

        env_ids.append(env_id)

        with open(self.env_ids_file, "w") as file:
            json.dump({"ids": env_ids}, file)
        self.logger.info(f"Saved environment ID: {env_id}")

    def _load_env_ids(self):
        """Loads environment IDs from the JSON file."""
        if os.path.exists(self.env_ids_file):
            with open(self.env_ids_file, "r") as file:
                data = json.load(file)
                env_ids = data.get("ids", [])
            for env_id in env_ids:
                try:
                    # Register the environment with Ray
                    self._register_training_environment(env_id)
                    self.logger.info(f"Loaded environment with ID: {env_id}")
                except Exception as e:
                    self.logger.error(f"Failed to load environment with ID {env_id}: {e}")

    def create_environment(self, env_id: Optional[str] = None, save: bool = False):
        """Creates and registers a new training environment with a unique ID."""
        if self.mode == EnvironmentMode.TRAIN:
            # Use provided env_id or generate a new one
            env_id = (
                env_id if env_id else f"TradingEnv-{EnvironmentMode.TRAIN.value}-{uuid.uuid4()}"
            )
            self._register_training_environment(env_id, save)
        else:
            self.logger.error("Creating environments is only applicable in TRAIN mode.")
            raise ValueError("Cannot create environment in the current mode.")

    def get_environment(self, env_id: str):
        """Retrieves the specified environment."""
        return self.environments.get(env_id)

    def manage_environment(self, env_id: str):
        """Manage operations for a specific environment."""
        if env_id not in self.environments:
            raise ValueError(f"Environment {env_id} does not exist.")
        return self.environments[env_id]

    def dispose(self):
        """Dispose of all environments."""
        for env_id, env in self.environments.items():
            try:
                env.close()  # Ensure environment is closed properly
                self.logger.info(f"Disposed environment with ID: {env_id}")
            except Exception as e:
                self.logger.error(f"Failed to dispose environment with ID {env_id}: {e}")
        self.environments.clear()
        self.logger.info("All environments disposed.")

    def reset(self):
        """
        Reset all environments (not applicable to live and sandbox modes).
        """
        if self.mode in [EnvironmentMode.BACKTEST, EnvironmentMode.TRAIN]:
            for env_id, env in self.environments.items():
                try:
                    env.reset()
                    self.logger.info(f"Reset environment with ID: {env_id}")
                except Exception as e:
                    self.logger.error(f"Failed to reset environment with ID {env_id}: {e}")
        else:
            self.logger.error("Reset not applicable for live and sandbox modes.")