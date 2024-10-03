'''
	Sinewave: 
		Environment - 7:
			Data: Generated Sinewave
					Training: 5 peaks
					Evaluation: 2 peaks
					Testing: 3 peaks
				Observation Space: 
					price values,
					price -> rolling mean (10 data points),
					price -> rolling mean (20 data points),
					price -> rolliong mean (30 data points),
					price -> log difference
			Action Space: buy-sell-hold
			Reward Strategy: networth-change
		Strategy - 1:
			DRL: 
				PPO with a custom MLP architecture
'''
# base class
from rl_fts.strategies.strategy import Strategy
# Call backs
from rl_fts.rayExtension.callbacks.recordNetWorthCallback import RecordNetWorthCallback
# RL Agent
from ray.rllib.agents import ppo
# RL Model
from ray.rllib.models import ModelCatalog
from ray.rllib.utils.typing import ModelConfigDict
from rl_fts.strategies.sinewave.environment7.models.model1 import Model
# Environment
from rl_fts.environments.sinewave.environment7 import create_env, normalization_info


class PPO_Sinewave_BSH_PBR(Strategy):

    def __init__(self):
        # run configuration
        self.max_epoch = 50
        self.net_worth_threshold = 250
        self.patience = 1
        self.evaluation_frequency = 1
        self.log_name = "sinewave/environment7/strategy1"
        self.log_dir = "/Users/jordandaubinet/Documents/Repositories/masters/masters-code/logs/"

        # register model
        ModelCatalog.register_custom_model(
            "PPO_Sinewave_BSH_NWC_Model1", Model)

        # configure the train environment
        env_train_config = {
            "type": "train",
            "window_size": 1,
            "min_periods": 1,
            "max_allowed_loss": 1,  # allow for 100% loss of funds
            "period": 10,  # the number of periods to generate with the sine wave
            "render_env": True,
            "trading_days": 90,
            "log_name": self.log_name,
            "log_dir": self.log_dir,
            "horizon": 30,
            "id": "PPO_Sinewave_BSH_NWC",
        }
        # configure the test environment
        env_test_config = {
            "type": "eval",
            "window_size": 1,
            "min_periods": 1,
            "render_env": True,
            "explore": False,
            "max_allowed_loss": 1,  # allow for 100% loss of funds
            "period": 10,  # the number of periods to generate with the sine wave
            "trading_days": 90,
            "horizon": 30,
        }
        # normalisation information
        norm_info = normalization_info(env_train_config)
        # Model details
        model: ModelConfigDict = {
            "custom_model": "PPO_Sinewave_BSH_NWC_Model1",
            "custom_model_config": {
                "mean": norm_info["mean"],
                "var": norm_info["var"]
            }
        }
        # variables for configuration
        # this is simply set to the number of CPU cores (could be cahnged to detect this with code)
        num_rollout_workers = 1
        # We set the batch size to the full training size, that fits
        # have 61 -> want 32
        # training_length = training_size(env_train_config)
        # test = divmod(training_length, 2)
        # train_batch_size = divmod(training_length, 2)[0]
        train_batch_size = 30
        # We set this to the train_batch_size / num_rollout_workers (and hope it fits in our memory requirements)
        # We may have to adapt this number to be the maximum minibatch that fits into memory / num_rollout_workers
        sgd_minibatch_size = int(train_batch_size / num_rollout_workers)
        # Configure the algorithm.
        config = ppo.PPOConfig(
        ).training(
            model=model,
            # train_batch_size=500
            train_batch_size=train_batch_size
        ).framework(
            framework="tf2",
            eager_tracing=False
        ).environment(
            env="TradingEnv",
            env_config=env_train_config,
            render_env=True,
            normalize_actions=True
        ).rollouts(
            num_rollout_workers=num_rollout_workers,
            batch_mode="complete_episodes",
            horizon=30,
            soft_horizon=False
        ).evaluation(
            evaluation_config=env_test_config,
            evaluation_interval=1,
            evaluation_duration_unit="timesteps",
            evaluation_duration=30,
            evaluation_num_workers=1,
            evaluation_parallel_to_training=False
        ).callbacks(RecordNetWorthCallback)

        config.rollout_fragment_length = 30
        config.sgd_minibatch_size = sgd_minibatch_size

        self.config = config.to_dict()
        self.algorithm_name = "PPO"
        self.create_env = create_env
        self.agent = ppo.PPOTrainer


def main():
    strategy = PPO_Sinewave_BSH_PBR()
    strategy.clearLogs()
    strategy.train()


main()
