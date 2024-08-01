import gym
from venues import VenueManager
from environments import BaseEnvironment

def cli_help():
    return "Training Environment"

class TrainingEnvironment(BaseEnvironment):
    def __init__(self, venue_manager: VenueManager, env_id: str = "Trading-v0") -> None:
        super().__init__(venue_manager)
        self.env_type = "gym"

        if self.env_type == "gym":
            self.engine = gym.make(env_id)  # Replace with your custom Gym environment
        else:
            self._action_spec = self._get_action_spec()
            self._observation_spec = self._get_observation_spec()
            # self.engine = 

    
    def add_data(self):
        # self.venue_manager.data_manager
        return 
    
    def reset(self):
        """
        Reset the environment.
        """
        if self.env_type == "gym":
            return self.engine.reset()

    def step(self, action):
        """
        Take a step in the environment.

        Args:
        - action: Action to take
        """
        if self.env_type == "gym":
            return self.engine.step(action)

    def render(self, mode="human"):
        """
        Render the environment.

        Args:
        - mode (str): Rendering mode
        """
        if self.env_type == "gym":
            return self.engine.render(mode)

    def close(self):
        """
        Close the environment.
        """
        if self.env_type == "gym":
            return self.engine.close()
