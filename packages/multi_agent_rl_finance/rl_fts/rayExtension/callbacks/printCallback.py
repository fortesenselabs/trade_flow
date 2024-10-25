
from ray.tune import Callback

class PrintCallback(Callback):
    def on_trial_result(self, iteration, trials, trial, result, **info):
        print('# --- Training Results --- #')
        print(f"iteration: {iteration}, episode_reward_max: {result['episode_reward_max']}")
        print(f"iteration: {iteration}, episode_reward_min: {result['episode_reward_min']}")
        print(f"iteration: {iteration}, episode_reward_mean: {result['episode_reward_mean']}")
        print(f"iteration: {iteration}, episode_len_mean: {result['episode_len_mean']}")
        print(f"iteration: {iteration}, episodes_this_iter: {result['episodes_this_iter']}")
        print(f"iteration: {iteration}, total_reward_mean: {result['custom_metrics']['total_reward_mean']}")
        print(f"iteration: {iteration}, net_worth_mean: {result['custom_metrics']['net_worth_mean']}")
        print(f"iteration: {iteration} total_trades_mean: {result['custom_metrics']['total_trades_mean']}")
        print("")