import numpy as np
from freqtrade.freqai.prediction_models.ReinforcementLearner import ReinforcementLearner
from freqtrade.freqai.RL.Base5ActionRLEnv import Actions, Base5ActionRLEnv, Positions


class TradeFlowAgent(ReinforcementLearner):
    """
    User created RL prediction model.

    Save this file to `freqtrade/user_data/freqaimodels`

    then use it with:

    freqtrade trade --freqaimodel TradeFlowAgent --config config.json --strategy TradeFlowAgentStrategy

    Here the users can override any of the functions
    available in the `IFreqaiModel` inheritance tree. Most importantly for RL, this
    is where the user overrides `MyRLEnv` (see below), to define custom
    `calculate_reward()` function, or to override any other parts of the environment.

    This class also allows users to override any other part of the IFreqaiModel tree.
    For example, the user can override `def fit()` or `def train()` or `def predict()`
    to take fine-tuned control over these processes.

    Another common override may be `def data_cleaning_predict()` where the user can
    take fine-tuned control over the data handling pipeline.
    """

    class MyRLEnv(Base5ActionRLEnv):
        """
        User made custom environment. This class inherits from BaseEnvironment and gym.Env.
        Users can override any functions from those parent classes. Here is an example
        of a user customized `calculate_reward()` function.

        Warning!
        This is function is a showcase of functionality designed to show as many possible
        environment control features as possible. It is also designed to run quickly
        on small computers. This is a benchmark, it is *not* for live production.

        TODO: fix get_unrealized_profit, get_current_price, get_previous_price, calculate_volatility methods

        Formula: Volatility is often computed using the standard deviation of price changes over a given period. In Freqtrade,
        it may be done using Python’s pandas library or a custom function that handles price variations.

        TODO: make transaction_cost dynamic
        """

        def calculate_reward(self, action: int) -> float:
            # Penalize if the action is invalid
            if not self._is_valid(action):
                self.tensorboard_log("invalid")
                return -2

            pnl = self.get_unrealized_profit()

            # Transaction cost and volatility scaling
            factor = 100
            pair = self.pair.replace(":", "")
            transaction_cost = 0.0001  # Example: 1 basis point

            # Calculate price change (r_t)
            price_now = self.get_current_price(self.pair, True)
            price_previous = self.get_previous_price()
            r_t = price_now - price_previous  # Price change from previous step

            # Calculate volatility (sigma_t-1) - using exponential moving standard deviation (60-period window)
            volatility = self.calculate_volatility(window=60)
            # Calculate 252-period rolling volatility (standard deviation of daily returns)
            # dataframe["%-volatility_252"] = (
            #     dataframe["%-daily_returns"].ewm(span=60, min_periods=1).std()
            # )

            # Basic reward (adjusted for volatility and transaction costs)
            reward = (pnl - transaction_cost * price_previous) / volatility

            # Reward for entering trades (using RSI as an example)
            if (
                action in (Actions.Long_enter.value, Actions.Short_enter.value)
                and self._position == Positions.Neutral
            ):
                rsi_now = self.raw_features["%-rsi-period_10_shift-1"].iloc[self._current_tick]
                factor = 40 / rsi_now if rsi_now < 40 else 1
                return 25 * factor

            # Small penalty for inactivity (scaled with duration)
            inactivity_penalty = -1 * np.log(1 + self._current_tick - self._last_trade_tick)
            if action == Actions.Neutral.value and self._position == Positions.Neutral:
                return inactivity_penalty

            # Scale penalty for long trade duration
            max_trade_duration = self.rl_config.get("max_trade_duration_candles", 300)
            trade_duration = self._current_tick - self._last_trade_tick
            if trade_duration > max_trade_duration:
                penalty_factor = np.exp(
                    trade_duration / max_trade_duration
                )  # Exponentially increasing penalty
                factor *= penalty_factor

            # Penalty for sitting too long in position
            if (
                self._position in (Positions.Short, Positions.Long)
                and action == Actions.Neutral.value
            ):
                return -1 * np.log(1 + trade_duration)  # Logarithmic penalty

            # Exit long position reward
            if action == Actions.Long_exit.value and self._position == Positions.Long:
                if pnl > self.profit_aim * self.rl_config["model_reward_parameters"]["rr"]:
                    factor *= self.rl_config["model_reward_parameters"].get("win_reward_factor", 2)
                return np.log(1 + abs(pnl)) * factor  # Log scaling for large profits

            # Exit short position reward
            if action == Actions.Short_exit.value and self._position == Positions.Short:
                if pnl > self.profit_aim * self.rl_config["model_reward_parameters"]["rr"]:
                    factor *= self.rl_config["model_reward_parameters"].get("win_reward_factor", 2)
                return np.log(1 + abs(pnl)) * factor

            return reward


"""
Hint

The best reward functions are ones that are continuously differentiable, and well scaled. In other words, adding a 
single large negative penalty to a rare event is not a good idea, and the neural net will not be able to learn that function. 
Instead, it is better to add a small negative penalty to a common event. This will help the agent learn faster. 
Not only this, but you can help improve the continuity of your rewards/penalties by having them scale with severity 
according to some linear/exponential functions. In other words, you'd slowly scale the penalty as the duration of the 
trade increases. This is better than a single large penalty occurring at a single point in time.
"""

"""

"pair_whitelist": [".*/USDT:USDT"],

`
  "rl_config": {
    "train_cycles": 25,
    "add_state_info": true,
    "max_trade_duration_candles": 300,
    "max_training_drawdown_pct": 0.2,
    "model_type": "PPO",
    "policy_type": "MlpPolicy",
    "model_reward_parameters": {
      "rr": 3,
      "profit_aim": 0.25
    }
  }
`

for the model type, test PPO, A2c and DQN.
for the policy type, if LSTM policy is available test it too.
"""
