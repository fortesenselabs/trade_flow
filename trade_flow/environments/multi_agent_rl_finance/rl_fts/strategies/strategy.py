"""
  A strategy class combines a DRL algorithm and an environment.
	- An environment defines an action scheme, a reward scheme and an observation space.
"""
import time
import shutil
import os

import ray
from ray import tune
from ray.tune import Analysis
from ray.tune.stopper import CombinedStopper, MaximumIterationStopper, TrialPlateauStopper

# Tune CallBack
from rl_fts.rayExtension.callbacks.printCallback import PrintCallback
# Tune Stopper
from rl_fts.rayExtension.stoppers.rewardThresholdStopper import RewardThresholdStopper
# Evaluation
from ray.rllib.evaluation.metrics import collect_episodes, summarize_episodes
import matplotlib.pyplot as plt
import tensorflow as tf
import io

class Strategy():

	def __init__(self) -> None:
		self.max_epoch = None
		self.evaluation_frequency = None
		self.net_worth_threshold = None
		self.patience = None

		self.config = None
		self.env_test_config = None
		self.agent = None
		self.algorithm_name = None
		self.log_name = None
		self.log_dir = None
		raise NotImplementedError

	def train(self) -> Analysis:
		'''
		  Train the RL agent for this strategy
		'''
		# Register the environment
		tune.register_env("TradingEnv", self.create_env)

		# dashboard
		ray.init(local_mode=True)

		start = time.time()

		# Setup stopping conditions
		stopper = CombinedStopper(
			MaximumIterationStopper(max_iter=self.max_epoch),
			RewardThresholdStopper(
				reward_threshold=self.episode_max_reward_training * 0.8, patience=self.patience),
			TrialPlateauStopper(metric="net_worth_mean")
		)

		self.print_training_information()

		# train an agent
		analysis = tune.run(
			self.algorithm_name,
			name=self.log_name,
			config=self.config,
			stop=stopper,
			metric="episode_reward_mean",
			mode="max",
			verbose=0,
			local_dir=self.log_dir,
			checkpoint_freq=0,
			checkpoint_at_end=True,
			callbacks=[
				PrintCallback(),
			],
			reuse_actors=True,
		)
		print(f"Best Trail log directory: {analysis.best_logdir}")
		ray.shutdown()

		taken = time.time() - start
		print(f"Time taken: {taken:.2f} seconds.")

		self.best_logdir = analysis.best_trial.checkpoint.value
		return analysis

	def test(self, best_logdir=None):
		'''
		  Evaluate the RL agent for this strategy
		'''
		# # Register the environment
		# tune.register_env("TradingEnv", self.create_env)

		# if not best_logdir:
		#   best_logdir = self.best_logdir

		# # Restore agent
		# self.agent(
		#   env="TradingEnv",
		#   config=self.config
		# )
		# self.agent.restore(best_logdir)
		# # evaluate an episode
		# # agent.evaluate()

		# # Instantiate the environment
		# env = self.create_env(self.env_test_config)

		# # Run until episode ends
		# episode_reward = 0
		# done = False
		# obs = env.reset()

		# while not done:
		#     action = self.agent.compute_single_action(obs)
		#     obs, reward, done, _ = env.step(action)
		#     episode_reward += reward

		# env.render()

		# TODO
		pass

	def getConfig(self):
		return self.config

	def clearLogs(self):
		path = f'{self.log_dir}{self.log_name}'
		if os.path.exists(path):
			shutil.rmtree(path, ignore_errors=False)

	def print_training_information(self):
		print()
		print("#-- Training Information --#")
		print(f"horizon: {self.training_length}")
		print(
			f"stochastic gradient decent minibatch size: {self.config['sgd_minibatch_size']}")
		print(
			f"stochastic gradient decent iterations: {self.config['num_sgd_iter']}")
		print(f"number of rollout workers: {self.config['num_workers']}")
		print()

		print("#-- Evaluation Information --#")
		print(f"horizon: {self.evaluation_length}")
		print(f"evaluation frequency: {self.evaluation_frequency}")
		print(f"maximum episode reward for evaluation: {self.episode_max_reward_evaluation}")
		print()

		print("#-- Normalisation Information --#")
		print(f"reward_clipping_bounds: {self.config['clip_rewards']}")
		print(f"max possible episode reward: {self.config['vf_clip_param']}")
		# print(f"minimum price value: {self.norm_info['min']}")
		# print(f"maximum price value: {self.norm_info['max']}")
		# print(f"mean price value: {self.norm_info['mean'][0]}")
		print()

	def custom_eval_function(self, algorithm, eval_workers):
		"""Example of a custom evaluation function.
		Args:
			algorithm: Algorithm class to evaluate.
			eval_workers: Evaluation WorkerSet.
		Returns:
			metrics: Evaluation metrics dict.
		"""
		
		# Calling .sample() runs exactly one episode per worker due to how the
		# eval workers are configured.
		eval_workers.foreach_worker(func=lambda w: w.sample())

		# plot the current figure to the board 
		fig = plt.gcf()
		# send image to tensorboard
		writer = tf.summary.create_file_writer(self.log_dir+self.log_name)
		with writer.as_default():
			data = self.plot_to_image(fig)
			tf.summary.image(self.log_name, data=data, step=algorithm.iteration)

		# get evaluation workers
		remote_workers = eval_workers.remote_workers()
		# Collect the accumulated episodes on the workers, and then summarize the
		episodes = collect_episodes(remote_workers=remote_workers, timeout_seconds=99999)
		# episode stats into a metrics dict.
		metrics = summarize_episodes(episodes[0])

		print('# --- Evaluation Results --- #')
		print(f"iteration: {algorithm.iteration} episode_reward_mean: {metrics['episode_reward_mean']}")
		print(f"iteration: {algorithm.iteration} episode_len_mean: {metrics['episode_len_mean']}")
		print(f"iteration: {algorithm.iteration} episodes_this_iter: {metrics['episodes_this_iter']}")
		print(f"iteration: {algorithm.iteration} total_reward_mean: {metrics['custom_metrics']['total_reward_mean']}")
		print(f"iteration: {algorithm.iteration} net_worth_mean: {metrics['custom_metrics']['net_worth_mean']}")
		print(f"iteration: {algorithm.iteration} total_trades_mean: {metrics['custom_metrics']['total_trades_mean']}")
		print("")
		return metrics
	
	def plot_to_image(self, figure):
		"""Converts the matplotlib plot specified by 'figure' to a PNG image and
		returns it. The supplied figure is closed and inaccessible after this call."""
		# Save the plot to a PNG in memory.
		buf = io.BytesIO()
		plt.savefig(buf, format='png')
		buf.seek(0)
		# Convert PNG buffer to TF image
		image = tf.image.decode_png(buf.getvalue(), channels=4)
		# Add the batch dimension
		image = tf.expand_dims(image, 0)
		return image
