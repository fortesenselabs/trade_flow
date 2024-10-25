'''
	Strategy 3:
		Environment: Stock - NFLX
			Data: 10 years [2012-12-31 - 2022-12-31
				Training: 5 years (1260 days)
				Evaluation: 3 years (756 days)
				Testing: 2 years
			Observation Space: 
				30x days of the following:
					price values,
					price -> rolling mean (10 data points),
					price -> rolling mean (20 data points),
					price -> rolliong mean (30 data points),
					price -> log difference
			Action Space: buy-sell-hold
			Reward Strategy: net-worth-change
		DRL: 
			PPO
				horizon: Entire training set -> x days
			Model: 
				MLP -> [256, 256]
'''
# base class
from rl_fts.strategies.strategy import Strategy
# Call backs
from rl_fts.rayExtension.callbacks.recordTotalRewardCallback import RecordTotalRewardCallback
from rl_fts.rayExtension.callbacks.recordNetWorthCallback import RecordNetWorthCallback
# RL Agent
from ray.rllib.agents.ppo import PPOConfig, PPOTrainer
# RL Model
from ray.rllib.models import ModelCatalog
from ray.rllib.utils.typing import ModelConfigDict
from rl_fts.strategies.stock.NFLX.environment1.models.model1 import KerasBatchNormModel
# Environment
from rl_fts.environments.stock.environment1 import create_env, normalization_info, reward_clipping_training, max_episode_reward_training 
from rl_fts.environments.stock.environment1 import training_length, evaluation_length
# Callbacks
from ray.rllib.agents import MultiCallbacks

class PPO_NFLX_BSH_NWC(Strategy):
		
	def __init__(self):
			# run configuration
			self.max_epoch = 50
			self.training_length = training_length()
			self.evaluation_length = evaluation_length()
			self.window_size = 30
			self.patience = 1
			self.evaluation_frequency = self.max_epoch / 10
			self.log_name = "stock/NFLX/environment1/strategy3"
			self.log_dir = "/Users/jordandaubinet/Documents/Repositories/masters/masters-code/logs/"
			# 
			self.num_rollout_workers = 4

			# register model
			ModelCatalog.register_custom_model("KerasBatchNormModel", KerasBatchNormModel)

			# configure the train environment
			env_train_config = {
				"type": "train",
				"window_size": self.window_size,
				"min_periods": self.window_size,
				"max_allowed_loss": 1,  # allow for 100% loss of funds
				"render_env": True,
				"log_name": self.log_name,
				"log_dir": self.log_dir,
				"horizon": self.training_length,
				"id": "NFLX_BSH_NWC",
				"starting_cash": 100,
			}
			# evaluation config
			env_eval_config = {
				"type": "eval",
				"window_size": self.window_size,
				"min_periods": self.window_size,
				"max_allowed_loss": 1,  # allow for 100% loss of funds
				"render_env": True,
				"log_name": self.log_name,
				"log_dir": self.log_dir,
				"horizon": self.evaluation_length,
				"id": "NFLX_BSH_NWC",
				"starting_cash": 100,
			}
			# Normalization
			self.norm_info = normalization_info()
			self.reward_clipping_bounds = reward_clipping_training(env_train_config)
			self.episode_max_reward = max_episode_reward_training(env_train_config)
			
			# Model details
			model: ModelConfigDict = {
				"custom_model": "KerasBatchNormModel",
				"custom_model_config": {
					"mean": self.norm_info["mean"],
					"var": self.norm_info["var"],
					"hidden_layers": [256, 256]
				},
			}
			# Configure the algorithm.
			config = (
				PPOConfig()
				.training(
						model=model,
						train_batch_size=self.training_length
				).framework(
						framework="tf2",
						eager_tracing=False
				).environment(
						env="TradingEnv",
						env_config=env_train_config,
						render_env=False,
						normalize_actions=True,
						clip_rewards=self.reward_clipping_bounds
				).rollouts(
						num_rollout_workers=self.num_rollout_workers,
						batch_mode="complete_episodes",
						horizon=self.training_length,
						soft_horizon=False
				)
				.evaluation(
						evaluation_interval=self.evaluation_frequency,
						evaluation_duration=1,
						evaluation_duration_unit="episodes",
						evaluation_parallel_to_training=False,
						evaluation_config=env_eval_config,
						custom_evaluation_function=self.custom_eval_function,
						evaluation_num_workers=1,
				)
				.callbacks(MultiCallbacks([RecordTotalRewardCallback, RecordNetWorthCallback]))
			)
			# number of times we update the NN with a single batch
			config.num_sgd_iter = 10
			# the size of the minibatch = the size of the batch
			config.sgd_minibatch_size = 126
			# the value function is the expected return from a current
			config.vf_clip_param = self.episode_max_reward
			self.config = config.to_dict()
			
			self.algorithm_name = "PPO"
			self.create_env = create_env
			self.agent = PPOTrainer

def main():
		strategy = PPO_NFLX_BSH_NWC()
		strategy.clearLogs()
		strategy.train()

main()
