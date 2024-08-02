from ray.rllib.agents.dqn import DQNTrainer
from ray.rllib.utils import try_import_tf
from typing import Optional, Dict, Any
from trade_flow.agents.agent import BaseAgent

# Import TensorFlow
tf = try_import_tf()


class DqnAgent(BaseAgent):
    def __init__(self, env_name: str, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(env_name, config)
        self.trainer = DQNTrainer(env=env_name, config=self.config)

    def train(self) -> None:
        """
        Train the DQN agent.
        """
        if self.trainer:
            self.trainer.train()
        else:
            raise RuntimeError("Trainer not initialized.")

    def evaluate(self) -> Dict[str, Any]:
        """
        Evaluate the DQN agent.

        Returns:
        - Dict[str, Any]: Evaluation results.
        """
        if self.trainer:
            # Example evaluation
            results = self.trainer.evaluate()
            return results
        else:
            raise RuntimeError("Trainer not initialized.")