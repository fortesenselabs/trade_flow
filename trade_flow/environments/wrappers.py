from tf_agents.environments.tf_py_environment import TFPyEnvironment
from tf_agents.trajectories import time_step as ts
from tf_agents.environments import py_environment
from tf_agents.specs import array_spec
import gymnasium as gym
import gym_anytrading.datasets as DS

# From: https://datascience.stackexchange.com/questions/120649/compatibility-of-anytrading-gym-environment-with-tf-agents

class GymWrapper(py_environment.PyEnvironment):
    def __init__(self, gym_env):
        super().__init__()
        self._gym_env = gym_env
        self._action_spec = self._get_action_spec()
        self._observation_spec = self._get_observation_spec()

    def _get_action_spec(self):
        action_space = self._gym_env.action_space
        if isinstance(action_space, gym.spaces.Box):
            return array_spec.BoundedArraySpec(
                shape=action_space.shape,
                dtype=action_space.dtype,
                minimum=action_space.low,
                maximum=action_space.high
            )
        elif isinstance(action_space, gym.spaces.Discrete):
            return array_spec.BoundedArraySpec(
                shape=(),
                dtype=action_space.dtype,
                minimum=0,
                maximum=action_space.n-1
            )
        else:
            raise ValueError(f"Unsupported action space type: {type(action_space)}")

    def _get_observation_spec(self):
        observation_space = self._gym_env.observation_space
        return array_spec.ArraySpec(
            shape=observation_space.shape,
            dtype=observation_space.dtype
        )

    def action_spec(self):
        return self._action_spec

    def observation_spec(self):
        return self._observation_spec

    def _reset(self):
        return ts.restart(self._gym_env.reset())

    def _step(self, action):
        obs, reward, done, info = self._gym_env.step(action)
        if done:
            return ts.termination(obs, reward)
        else:
            return ts.transition(obs, reward)


# env = gym.make('forex-v0', df=DS.FOREX_EURUSD_1H_ASK, window_size = 10, frame_bound=(10, len(DS.FOREX_EURUSD_1H_ASK) - 1), unit_side = 'right')

# train_py_env = GymWrapper(env);
# eval_py_env = GymWrapper(env);

# train_env = TFPyEnvironment(train_py_env);
# eval_env = TFPyEnvironment(eval_py_env);