from typing import Any, Dict, Optional, List
import numpy as np
from stable_baselines3 import A2C, DDPG, PPO, SAC, TD3
from stable_baselines3.common.noise import NormalActionNoise, OrnsteinUhlenbeckActionNoise
from stable_baselines3.common.callbacks import BaseCallback
from trade_flow.agents.tensorboard import TensorboardCallback
from trade_flow.environments.generic.environment import TradingEnvironment
from trade_flow.agents.base import Agent


class SB3Agent(Agent):
    """
    Provides implementations for Stable Baselines3 RL algorithms.

    Attributes
    ----------
    env : TradingEnvironment
        The custom trading environment.
    config : Optional[Dict[str, Any]]
        Configuration parameters for the agent.
    """

    def __init__(self, env: TradingEnvironment, config: Optional[Dict[str, Any]] = None):
        super().__init__(env, config)

        # Supported models and their corresponding classes
        self.models = {"a2c": A2C, "ddpg": DDPG, "td3": TD3, "sac": SAC, "ppo": PPO}

        # Configuration for each model type from the user-provided config
        self.model_kwargs = {
            model_name: config.get(f"{model_name.upper()}_PARAMS", {})
            for model_name in self.models.keys()
        }

        # Supported noise models for action noise
        self.noise = {
            "normal": NormalActionNoise,
            "ornstein_uhlenbeck": OrnsteinUhlenbeckActionNoise,
        }

    def _add_action_noise(
        self, noise_type: str, noise_params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Add action noise to the agent if needed (for continuous action spaces).

        Args:
        - noise_type (str): The type of noise to apply ('normal' or 'ornstein_uhlenbeck').
        - noise_params (Optional[Dict[str, Any]]): Parameters for the noise model.

        Returns:
        - action_noise: An instance of the action noise to be used in training.
        """
        if noise_type not in self.noise:
            raise ValueError(f"Noise type '{noise_type}' is not supported.")

        n_actions = self.env.action_space.shape[-1]
        default_noise_params = {"mean": np.zeros(n_actions), "sigma": 0.1 * np.ones(n_actions)}

        # Combine provided noise params with defaults
        noise_params = {**default_noise_params, **(noise_params or {})}
        noise_class = self.noise[noise_type]

        return noise_class(**noise_params)

    def get_model(self, model_name: str, model_kwargs: Optional[Dict[str, Any]] = None) -> Any:
        """
        Initialize and return the specified RL model.

        Args:
        - model_name (str): The name of the model to use (e.g., 'a2c', 'ppo').
        - model_kwargs (Optional[Dict[str, Any]]): Optional keyword arguments to pass to the model.

        Returns:
        - model: An instance of the selected RL model.
        """
        if model_name not in self.models:
            raise NotImplementedError(f"Model '{model_name}' is not supported.")

        if model_kwargs is None:
            model_kwargs = self.model_kwargs.get(model_name, {})

        if "action_noise" in model_kwargs:
            noise_type = model_kwargs["action_noise"]
            model_kwargs["action_noise"] = self._add_action_noise(noise_type)

        model_class = self.models[model_name]
        self.model = model_class(env=self.env, seed=self.seed, **model_kwargs)
        return self.model

    def train(
        self,
        n_episodes: int = 5,
        n_steps: int = 1000,
        tb_log_name: str = "run_sb3_agent",
        callbacks: Optional[List[BaseCallback]] = None,
    ) -> Any:
        """
        Train the agent using the specified environment.

        Agent's total_timesteps = n_episodes * n_steps

        Args:
            n_episodes (int): The number of episodes to train for.
            n_steps (int): The number of steps per episode.
            tb_log_name (str, optional): The name for the TensorBoard log. Defaults to 'run_sb3_agent'.
            callbacks (optional): A list of callbacks to pass to the training process.

        Returns:
            Any: The trained model.
        """
        if self.model is None:
            raise ValueError("Model not initialized. Cannot start training.")

        if callbacks is None:
            # Use a default TensorboardCallback if no custom callbacks are provided
            callbacks = [TensorboardCallback()]

        total_timesteps = n_episodes * n_steps

        try:
            # Start training the model with the provided timesteps, logging, and callbacks
            self.model.learn(
                total_timesteps=total_timesteps,
                tb_log_name=tb_log_name,
                callback=callbacks,
            )
        except Exception as e:
            raise RuntimeError(f"Error during training: {str(e)}")

        return self.model

    def evaluate(self, env: Any) -> Dict[str, Any]:
        """
        Evaluate the agent using the given environment.

        Args:
        - env (Any): The environment for evaluation.

        Returns:
        - Dict[str, Any]: The evaluation results.
        """
        raise NotImplementedError

    def predict(self, state: Any) -> Dict[str, Any]:
        """
        Predict the next action based on the current state.

        Args:
        - state (Any): The current observation from the environment.

        Returns:
        - Dict[str, Any]: The predicted action.
        """
        if self.model is None:
            raise ValueError("Model not initialized. Cannot make a prediction.")

        if not isinstance(state, np.ndarray):
            state = np.array(state)

        try:
            action, _states = self.model.predict(state)
            return {"action": action}
        except Exception as e:
            raise RuntimeError(f"Error during prediction: {str(e)}")
