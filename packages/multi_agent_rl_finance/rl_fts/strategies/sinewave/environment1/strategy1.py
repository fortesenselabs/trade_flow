'''
	Sinewave:
		Environment - 9:
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
				Reward Strategy: net-worth-change
		Strategy - 1:
			DRL: 
				Default PPO
'''
# base class
from rl_fts.strategies.strategy import Strategy
# Call backs
from rl_fts.rayExtension.callbacks.recordNetWorthCallback import RecordNetWorthCallback
# RL Agent
from ray.rllib.agents import ppo
from ray.rllib.utils.typing import ModelConfigDict
# Environment
from rl_fts.environments.sinewave.environment1 import create_env

class PPO_Sinewave_BSH_NWC(Strategy):

		def __init__(self):
				# run configuration
				self.max_epoch = 100
				self.net_worth_threshold = 275
				self.patience = 1
				self.evaluation_frequency = 1
				self.log_name = "sinewave/environment9/strategy1"
				self.log_dir = "/Users/jordandaubinet/Documents/Repositories/masters/masters-code/logs/"

				# configure the train environment
				env_train_config = {
						"type": "train",
						"window_size": 30,
						"min_periods": 30,
						"max_allowed_loss": 1,  # allow for 100% loss of funds
						"period": 10,  # the number of periods to generate with the sine wave
						"render_env": True,
						"trading_days": 1000,
						"d_ratio": [0.5, 0.3, 0.2],
						"log_name": self.log_name,
						"log_dir": self.log_dir,
						"horizon": 30,
						"id": "PPO_Sinewave_BSH_NWC",
				}
				# configure the test environment
				env_test_config = {
						"type": "eval",
						"window_size": 30,
						"min_periods": 30,
						"render_env": True,
						"max_allowed_loss": 0.1,  # allow for 10% loss of funds
						"num_workers": 1,
						"period": 10,  # the number of periods to generate with the sine wave
						"trading_days": 1000,
						"d_ratio": [0.5, 0.3, 0.2]
				}
				# Model details
				model: ModelConfigDict = {
						# "_disable_preprocessor_api": False,
						"fcnet_hiddens": [256, 256],
						"fcnet_activation": "relu",
				}
				# Normalization
				# reward_clipping_bounds = reward_clipping(env_train_config)
				# Configure the algorithm.
				config = ppo.PPOConfig(
				).training(
						model=model,
				).framework(
						framework="tf2",
						eager_tracing=False
				).environment(
						env="TradingEnv",
						env_config=env_train_config,
						render_env=True,
						normalize_actions=True,
				).rollouts(
						num_rollout_workers=4,
						batch_mode="complete_episodes",
						horizon=30,
						soft_horizon=False,
				).evaluation(
						evaluation_config=env_test_config,
						evaluation_interval=1,
						evaluation_duration_unit="timesteps",
						evaluation_duration=30,
						evaluation_num_workers=1,
						evaluation_parallel_to_training=False
				).callbacks(RecordNetWorthCallback)

				self.config = config.to_dict()
				self.algorithm_name = "PPO"
				self.create_env = create_env
				self.agent = ppo.PPOTrainer

def main():
		strategy = PPO_Sinewave_BSH_NWC()
		strategy.clearLogs()
		strategy.train()

main()
