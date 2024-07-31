import gymnasium as gym
from trade_flow.flow import DataManager


class TrainingEnvironment(gym.Env):
    def __init__(self, mode: str, config_path: str, data_manager: DataManager) -> None:
        super().__init__()
        self.mode = mode
        self.config_path = config_path
        self.engine = None
        self.data_manager = data_manager

        if env_type == "gym":
            self.gym_env = gym.make(
                "Trading-v0"
            )  # Replace with your custom Gym environment

    def reset(self):
        """
        Reset the environment.
        """
        if self.env_type == "gym":
            self.gym_env.reset()

    def step(self, action):
        """
        Take a step in the environment.

        Args:
        - action: Action to take
        """
        if self.env_type == "gym":
            return self.gym_env.step(action)

    def render(self, mode="human"):
        """
        Render the environment.

        Args:
        - mode (str): Rendering mode
        """
        if self.env_type == "gym":
            self.gym_env.render(mode)

    def close(self):
        """
        Close the environment.
        """
        if self.env_type == "gym":
            self.gym_env.close()

    # def step(self, action):
    #     # Implement the logic to take a step in the environment
    #     observation, reward, done, info = self.engine.step(action)
    #     return observation, reward, done, info

    # def reset(self):
    #     # Implement the logic to reset the environment
    #     return self.engine.reset()

    # def render(self, mode="human"):
    #     # Implement the logic to render the environment
    #     pass

    # def close(self):
    #     # Implement the logic to close the environment
    #     self.engine.shutdown()



# class TestingEnvironment(BacktestEngine):
#     def __init__(self, mode: str, config_path: str) -> None:
#         super().__init__()
#         self.mode = mode
#         self.config_path = config_path
#         self.engine = None
#         self.data_manager = DataManager()

#     def step(self, action):
#         # Implement the logic to take a step in the environment
#         observation, reward, done, info = self.engine.step(action)
#         return observation, reward, done, info

#     def reset(self):
#         # Implement the logic to reset the environment
#         return self.engine.reset()

#     def render(self, mode="human"):
#         # Implement the logic to render the environment
#         pass

#     def close(self):
#         # Implement the logic to close the environment
#         self.engine.shutdown()
