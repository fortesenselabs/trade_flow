from typing import Any, Dict, Optional

from trade_flow.environments.generic.environment import TradingEnvironment


class Agent:
    def __init__(self, env: TradingEnvironment, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the base agent.

        Args:
        - env (TradingEnvironment): The environment to trading in.
        - config (Optional[Dict[str, Any]]): Optional configuration for the agent.
        """

        self.env = env
        self.config = config or {}
        self.trainer = None
        self.continual_learning: bool = False
        self.tensorboard_callback: TensorboardCallback = TensorboardCallback(
            verbose=1, actions=BaseActions
        )

    def get_env(self) -> None:
        """
        return environment
        """
        return self.env

    def get_model(self) -> None:
        """
        return selected model
        """
        pass

    def train_test_split_env(self) -> None:
        """
        https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.train_test_split.html
        """
        pass

    def train(self, env: Any) -> None:
        """
        Train the agent.
        """
        raise NotImplementedError

    def evaluate(self, env: Any) -> Dict[str, Any]:
        """
        Evaluate the agent.

        Returns:
        - Dict[str, Any]: Evaluation results.
        """
        raise NotImplementedError

    def predict(self, state: Any) -> None:
        """
        Agent prediction.

        Returns:
        - Dict[str, Any]: Action.
        """
        pass

    def save(self, checkpoint_path: str) -> None:
        """
        Save the agent's state to disk .

        Args:
        - checkpoint_path (str): Path to save the checkpoint.
        """
        if self.trainer:
            self.trainer.save(checkpoint_path)
        else:
            raise RuntimeError("Trainer not initialized.")

    def load(self, checkpoint_path: str) -> None:
        """
        Load the agent's state from disk.

        Args:
        - checkpoint_path (str): Path to load the checkpoint from.
        """
        if self.trainer:
            self.trainer.restore(checkpoint_path)
        else:
            raise RuntimeError("Trainer not initialized.")


"""
Agent Interface:
__init__(env, **kwargs):
self.continual_learning: bool

train_test_split_env() -> train_env, test_env
https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.train_test_split.html

train(train env) -> model // trained model
evaluate(validation or test env) -> list[score] // list of evaluation metrics
predict(state) -> action 
"""
