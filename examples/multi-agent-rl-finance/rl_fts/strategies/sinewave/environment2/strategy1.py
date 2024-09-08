'''
	Strategy 2:
		DRL: 
			PPO with a custom MLP architecture
		Environment: sinewave
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
		Action Space: short-hold
		Reward Strategy: short-networth-change
'''
# base class
from rl_fts.strategies.strategy import Strategy
# Call backs
from rl_fts.rayExtension.callbacks.recordShortNetWorthCallback import RecordNetWorthCallback
# RL Agent
from ray.rllib.agents import ppo
# RL Model
from ray.rllib.models import ModelCatalog
from ray.rllib.utils.typing import ModelConfigDict
from rl_fts.strategies.sinewave.environment2.models.model1 import KerasBatchNormModel
# Environment
from rl_fts.environments.sinewave.environment2 import create_env, normalization_info


class PPO_Sinewave_SH_SNC(Strategy):

    def __init__(self):
        # run configuration
        self.max_epoch = 50
        self.net_worth_threshold = 250
        self.patience = 1
        self.evaluation_frequency = 1
        self.log_name = "sinewave/environment2/strategy1"
        self.log_dir = "/Users/jordandaubinet/Documents/Repositories/masters/masters-code/logs/"

        # register model
        ModelCatalog.register_custom_model(
            "KerasBatchNormModel", KerasBatchNormModel)

        # configure the train environment
        env_train_config = {
            "type": "train",
            "window_size": 30,
            "min_periods": 30,
            "max_allowed_loss": 1,  # allow for 100% loss of funds
            "period": 10,  # the number of periods to generate with the sine wave
            "render_env": True,
            "trading_days": 121,
            "log_name": self.log_name,
            "log_dir": self.log_dir,
            "horizon": 30,
            "id": "PPO_Sinewave_SH_SNC",
        }
        # configure the test environment
        env_test_config = {
            "type": "eval",
            "window_size": 30,
            "min_periods": 30,
            "render_env": True,
            "max_allowed_loss": 1,  # allow for 10% loss of funds
            "num_workers": 1,
            "period": 10,  # the number of periods to generate with the sine wave
            "trading_days": 121,
        }
        # Configure the algorithm.
        config = ppo.PPOConfig(
        ).training(
            # model=model,
            # train_batch_size=300
        ).framework(
            framework="tf2",
            eager_tracing=False
        ).environment(
            env="TradingEnv",
            env_config=env_train_config,
            render_env=True,
            normalize_actions=True
        ).rollouts(
            num_rollout_workers=3,
            batch_mode="complete_episodes",
            horizon=30,
            soft_horizon=False
        ).evaluation(
            evaluation_config=env_test_config,
            evaluation_interval=1,
            evaluation_duration_unit="episodes",
            evaluation_duration=30,
            evaluation_num_workers=1,
            evaluation_parallel_to_training=False
        ).callbacks(RecordNetWorthCallback)

        # number of times we update the NN with a single batch
        # config.num_sgd_iter = 10
        # the size of the minibatch = the size of the batch
        # config.sgd_minibatch_size = 30

        self.config = config.to_dict()
        self.algorithm_name = "PPO"
        self.create_env = create_env
        self.agent = ppo.PPOTrainer


def main():
    strategy = PPO_Sinewave_SH_SNC()
    strategy.clearLogs()
    strategy.train()


main()
