import gymnasium as gym
from trade_flow.venues import VenueManager
from trade_flow.environments.environment import BaseEnvironment

def cli_help():
    return "Forex Training Environment"


class ForexTrainingEnvironment(BaseEnvironment):
    def __init__(self, venue_manager: VenueManager, env_id: str = "Trading-v0") -> None:
        super().__init__(venue_manager)
        self.env_type = "gym"
        print(f"TrainingEnvironment: {env_id}")
        self.engine = gym.make(env_id)  # Initialize with Gym environment

        # Define action and observation spaces
        self.action_space = self.engine.action_space
        self.observation_space = self.engine.observation_space

    def reset(self):
        """
        Reset the Gym environment.
        """
        if self.env_type == "gym":
            return self.engine.reset()

    def step(self, action):
        """
        Take a step in the Gym environment.

        Args:
        - action: Action to take
        """
        if self.env_type == "gym":
            next_state, reward, done, info = self.engine.step(action)
            return next_state, reward, done, info

    def render(self, mode="human"):
        """
        Render the Gym environment.

        Args:
        - mode (str): Rendering mode
        """
        if self.env_type == "gym":
            return self.engine.render(mode)

    def close(self):
        """
        Close the Gym environment.
        """
        if self.env_type == "gym":
            return self.engine.close()
