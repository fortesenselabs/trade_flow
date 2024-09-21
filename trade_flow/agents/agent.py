from typing import Any, Dict, Optional


class Agent:
    def __init__(self, env_name: str, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the base agent.

        Args:
        - env_name (str): The name of the environment to train in.
        - config (Optional[Dict[str, Any]]): Optional configuration for the agent.
        """
        self.env_name = env_name
        self.config = config or {}
        self.trainer = None

    def train(self) -> None:
        """
        Train the agent.
        """
        raise NotImplementedError

    def evaluate(self) -> Dict[str, Any]:
        """
        Evaluate the agent.

        Returns:
        - Dict[str, Any]: Evaluation results.
        """
        raise NotImplementedError

    def save(self, checkpoint_path: str) -> None:
        """
        Save the agent's state.

        Args:
        - checkpoint_path (str): Path to save the checkpoint.
        """
        if self.trainer:
            self.trainer.save(checkpoint_path)
        else:
            raise RuntimeError("Trainer not initialized.")

    def load(self, checkpoint_path: str) -> None:
        """
        Load the agent's state.

        Args:
        - checkpoint_path (str): Path to load the checkpoint from.
        """
        if self.trainer:
            self.trainer.restore(checkpoint_path)
        else:
            raise RuntimeError("Trainer not initialized.")
