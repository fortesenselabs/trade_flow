import gymnasium as gym
from trade_flow.environments.generic import Venue
from trade_flow.environments.generic import TradingEnvironment


class GymEnvironment(TradingEnvironment):
    """
    Gym Environment for training trading agents.

    This class provides an interface for interacting with Gym environments within a trading context. It inherits from the `Environment` base class and offers methods for resetting, stepping, rendering, and closing the environment.

    Args:
        venue (Venue): The associated venue for this environment.
        env_id (str, optional): The environment ID to use for Gym. Defaults to "Trading-v0".
    """

    def __init__(self, venue: Venue, env_id: str = "Trading-v0") -> None:
        super().__init__(venue)
        self.venue.set_trader_id(env_id)

        self.env_type = "gym"
        self.engine = gym.make(env_id)  # Initialize with Gym environment

        # Define action and observation spaces
        self.action_space = self.engine.action_space
        self.observation_space = self.engine.observation_space

    def get_action_space(self):
        """
        Get the action space of the environment.

        Returns:
            gym.spaces.Space: The action space of the environment.
        """
        return self.action_space

    def get_observation_space(self):
        """
        Get the observation space of the environment.

        Returns:
            gym.spaces.Space: The observation space of the environment.
        """
        return self.observation_space

    def get_venue(self):
        """
        Get the associated venue.

        Returns:
            Venue: The venue object associated with this environment.
        """
        return self.venue

    def get_state(self):
        """
        Get the current state of the environment.

        Returns:
            object: The current state of the environment.
        """
        return self.engine.state

    def reset(self):
        """
        Reset the Gym environment to its initial state.

        Returns:
            object: The initial state of the environment.
        """
        self.venue.reset()
        return self.engine.reset()

    def step(self, action):
        """
        Take a step in the Gym environment.

        Args:
            action (object): The action to take.

        Returns:
            tuple: A tuple containing the next state, reward, done flag, and info dictionary.
        """

        next_state, reward, done, info = self.engine.step(action)
        return next_state, reward, done, info

    def render(self, mode="human"):
        """
        Render the Gym environment.

        Args:
            mode (str, optional): The rendering mode. Defaults to "human".

        Returns:
            object: The rendered output.
        """
        self.engine.render_mode = mode
        return self.engine.render(mode)

    def close(self):
        """
        Close the Gym environment.
        """
        self.venue.close()
        return self.engine.close()
