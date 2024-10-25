"""Example of using RLlib's debug callbacks.
Here we use callbacks to track the average CartPole pole angle magnitude as a
custom metric.
"""

from typing import Dict, Tuple
# import argparse
import numpy as np
# import os

# import ray
# from ray import tune
from ray.rllib.agents import DefaultCallbacks
# from ray.tune import Callback

from ray.rllib.env import BaseEnv
from ray.rllib.evaluation import Episode, RolloutWorker
from ray.rllib.policy import Policy

class RecordNetWorthCallback(DefaultCallbacks):
    def setup(self, **info):
        pass

    def on_step_begin(self, **info):
        pass

    def on_step_end(self, **info):
        pass

    def on_trial_start(self, **info):
        pass

    def on_trial_restore(self, **info):
        pass

    def on_trial_save(self, **info):
        pass

    def on_trial_result(self, **info):
        pass

    def on_trial_complete(self, **info):
        pass

    def on_trial_error(self, **info):
        pass

    def on_checkpoint(self, **info):
        pass

    def on_experiment_end(self, **info):
        pass

    def on_episode_start(
        self,
        *,
        worker: RolloutWorker,
        base_env: BaseEnv,
        policies: Dict[str, Policy],
        episode: Episode,
        env_index: int,
        **kwargs
    ):
        episode.custom_metrics["net_worth"] = 0

    def on_episode_step(
        self,
        *,
        worker: RolloutWorker,
        base_env: BaseEnv,
        policies: Dict[str, Policy],
        episode: Episode,
        env_index: int,
        **kwargs
    ):
        pass

    def on_episode_end(
        self,
        *,
        worker: RolloutWorker,
        base_env: BaseEnv,
        policies: Dict[str, Policy],
        episode: Episode,
        env_index: int,
        **kwargs
    ):
        net_worth = worker.env.reward_scheme.previous_net_worth
        episode.custom_metrics["net_worth"] = net_worth