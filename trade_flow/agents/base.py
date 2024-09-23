from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from trade_flow.agents.tensorboard import TensorboardCallback
from trade_flow.environments.generic.environment import TradingEnvironment


class Agent(ABC):
    """
    Base agent class for training, evaluating, and interacting with the environment.

    Args:
    - env (TradingEnvironment): The environment to trade in.
    - config (Optional[Dict[str, Any]]): Optional configuration for the agent.
    """

    def __init__(self, env: TradingEnvironment, config: Optional[Dict[str, Any]] = None) -> None:
        self.env = env
        self.config = config or {}
        self.model = None
        self.continual_learning: bool = False
        self.seed = 42  # Default seed for reproducibility

        self.train_env: Optional[TradingEnvironment] = None
        self.test_env: Optional[TradingEnvironment] = None

        self.tensorboard_callback: Optional[TensorboardCallback] = None

    def get_env(self) -> TradingEnvironment:
        """
        Return the environment instance.

        Returns:
        - TradingEnvironment: The environment instance.
        """
        return self.env

    @abstractmethod
    def get_model(self, model_name: str, model_kwargs: Optional[Dict[str, Any]] = None) -> Any:
        """
        Initialize and return the specified RL model.

        Args:
        - model_name (str): The name of the model to use (e.g., 'a2c', 'ppo').
        - model_kwargs (Optional[Dict[str, Any]]): Optional keyword arguments to pass to the model.

        Returns:
        - Any: The model instance.
        """
        pass

    @abstractmethod
    def train(self) -> Any:
        """
        Train the agent using the environment.

        Returns:
        - Any: The trained model.
        """
        pass

    @abstractmethod
    def evaluate(self) -> Dict[str, Any]:
        """
        Evaluate the agent using the given environment.

        Returns:
        - Dict[str, Any]: The evaluation results.
        """
        pass

    @abstractmethod
    def predict(self, state: Any) -> Dict[str, Any]:
        """
        Make a prediction based on the current state.

        Args:
        - state (Any): The current state of the environment.

        Returns:
        - Dict[str, Any]: The action predicted by the agent.
        """
        pass

    def save(self, checkpoint_path: str) -> None:
        """
        Save the agent's model and state to a file.

        Args:
        - checkpoint_path (str): The path to save the checkpoint.
        """
        if self.model is None:
            raise ValueError("Model is not initialized. Cannot save the model.")

        try:
            self.model.save(checkpoint_path)
        except Exception as e:
            raise RuntimeError(f"Failed to save the model: {e}")

    def load(self, checkpoint_path: str) -> None:
        """
        Load the agent's model and state from a file.

        Args:
        - checkpoint_path (str): The path to load the checkpoint from.
        """
        if self.model is None:
            raise ValueError("Model is not initialized. Cannot load the model.")

        try:
            self.model.load(checkpoint_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load the model from {checkpoint_path}: {e}")
