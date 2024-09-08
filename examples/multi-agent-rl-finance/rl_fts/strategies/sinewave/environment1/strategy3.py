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
		Strategy - 3:
			DRL: 
				PPO with custom configuration parameters and custom Model
			MODEL:
				"fcnet_hiddens": [125, 125],
				"fcnet_activation": "relu",
				Batch Normalization input
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
from rl_fts.strategies.sinewave.environment1.models.model1 import KerasBatchNormModel
# Environment
from rl_fts.environments.sinewave.environment9 import create_env, normalization_info, reward_clipping, max_episode_reward, max_net_worth

class PPO_Sinewave_BSH_NWC(Strategy):

		def __init__(self):
				# run configuration
				self.max_epoch = 100
				threshold_potential_max_worth = 0.95
				self.patience = 1
				self.evaluation_frequency = 1
				self.log_name = "sinewave/environment9/strategy3"
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
						"d_ratio": [0.5, 0.3, 0.2],
						"log_name": self.log_name,
						"log_dir": self.log_dir,
						"horizon": 30,
						"starting_cash": 100,
						"id": "PPO_Sinewave_BSH_NWC",
				}
				# Configure the algorithm.
				norm_info = normalization_info(env_train_config)
				# Model details
				model: ModelConfigDict = {
					"custom_model": "KerasBatchNormModel",
					"custom_model_config": {
					"mean": norm_info["mean"],
					"var": norm_info["var"]
					}
				}
				# Normalization
				reward_clipping_bounds = reward_clipping(env_train_config)
				episode_reward_bound = max_episode_reward(env_train_config)
				# Configure the algorithm.
				config = ppo.PPOConfig(
				).training(
						model=model,
						train_batch_size=300
				).framework(
						framework="tf2",
						eager_tracing=False
				).environment(
						env="TradingEnv",
						env_config=env_train_config,
						render_env=True,
						normalize_actions=True,
						clip_rewards=reward_clipping_bounds
				).rollouts(
						num_rollout_workers=4,
						batch_mode="complete_episodes",
						horizon=30,
						soft_horizon=False,
				).evaluation(
						evaluation_config=env_train_config,
						evaluation_interval=1,
						evaluation_duration_unit="timesteps",
						evaluation_duration=30,
						evaluation_num_workers=1,
						evaluation_parallel_to_training=False
				).callbacks(RecordNetWorthCallback)

				# number of times we update the NN with a single batch
				config.num_sgd_iter = 10
				# the size of the minibatch = the size of the batch
				config.sgd_minibatch_size = 30
				# the value function is the expected return from a current
				config.vf_clip_param = episode_reward_bound
				# strategy should stop at this threshold
				self.net_worth_threshold = threshold_potential_max_worth*max_net_worth(env_train_config)

				self.config = config.to_dict()
				self.algorithm_name = "PPO"
				self.create_env = create_env
				self.agent = ppo.PPOTrainer

def main():
		strategy = PPO_Sinewave_BSH_NWC()
		strategy.clearLogs()
		strategy.train()

main()
