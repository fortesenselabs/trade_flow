from typing import Optional
import uuid
import json
import os
import gymnasium as gym
import ray
import ray.rllib
import ray.rllib.utils
from ray.tune.registry import register_env
from commons import Logger, EnvironmentMode, AssetClass 
from environments import LiveEnvironment, SandboxEnvironment, BacktestEnvironment, TrainingEnvironment
from venues import VenueManager

class EnvironmentManager:
    def __init__(self, mode: EnvironmentMode, venue_manager: VenueManager, asset_class: AssetClass = AssetClass.FOREX, is_new: bool = True) -> None:
        self.logger = Logger(name=__class__.__name__)
        self.mode = mode
        self.asset_class = asset_class
        self.venue_manager = venue_manager

        self.environments = {}
        self.env_ids_file = "training_environment_ids.json"
        self._init_environment()

        if not is_new:
            self._load_env_ids()  # Load saved environment IDs

        ray.init(ignore_reinit_error=True)  # Initialize Ray

    # Fixed the Error: _pickle.PicklingError: logger cannot be pickled | source(s): https://stackoverflow.com/questions/2999638/how-to-stop-attributes-from-being-pickled-in-python/2999833#2999833
    def __getstate__(self):
        d = self.__dict__.copy()
        if 'logger' in d:
            d['logger'] = d['logger'].name
        return d
    
    def __setstate__(self, d):
        if 'logger' in d:
            d['logger'] = Logger(name=d['logger'])
        self.__dict__.update(d)
    
    def _init_environment(self) -> None:
        self.logger.info(f"Initializing environment for mode: {self.mode}")

        if self.mode == EnvironmentMode.LIVE:
            self.selected_environment = LiveEnvironment(self.venue_manager)
        elif self.mode == EnvironmentMode.SANDBOX:
            self.selected_environment = SandboxEnvironment(self.venue_manager)
        elif self.mode == EnvironmentMode.BACKTEST:
            self.selected_environment = BacktestEnvironment(self.venue_manager)
        elif self.mode == EnvironmentMode.TRAIN:
            # Register a new training environment if not already done
            env_id = f"TradingEnv-{EnvironmentMode.TRAIN.value}-{uuid.uuid4()}"
            self.create_environment(env_id)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    def _register_training_environment(self, env_id: str):
        """Generates a unique environment ID, registers it with Ray, and saves it."""
        def create_env(env_config):
            """Environment creator function that creates a TrainingEnvironment."""
            return TrainingEnvironment(self.venue_manager, env_id)

        try:
            # Register the environment with Ray
            register_env(env_id, create_env)

            # Check if environment was registered correctly
            # ray.rllib.utils.check_env(TrainingEnvironment(self.venue_manager, env_id)) 
            self.logger.info(f"Registered environment with ID: {env_id}")

            # Save the environment ID
            self._save_env_id(env_id)
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

    def create_environment(self, env_id: Optional[str] = None):
        """Creates and registers a new environment with a unique ID."""
        if self.mode == EnvironmentMode.TRAIN:
            # Use provided env_id or generate a new one
            env_id = env_id if env_id else f"TradingEnv-{EnvironmentMode.TRAIN.value}-{uuid.uuid4()}"
            self._register_training_environment(env_id)
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

    # Placeholder methods for specific tasks; need implementation as required
    def get_portfolio(self):
        pass
    
    def generate_positions_report(self):
        pass
    
    def generate_order_fills_report(self):
        pass
    
    def generate_account_report(self):
        pass
    
    def place_order(self):
        pass
    
    def close_order(self):
        pass


