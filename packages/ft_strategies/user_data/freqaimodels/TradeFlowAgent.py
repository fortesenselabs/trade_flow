"""
Hint

The best reward functions are ones that are continuously differentiable, and well scaled. In other words, adding a 
single large negative penalty to a rare event is not a good idea, and the neural net will not be able to learn that function. 
Instead, it is better to add a small negative penalty to a common event. This will help the agent learn faster. 
Not only this, but you can help improve the continuity of your rewards/penalties by having them scale with severity 
according to some linear/exponential functions. In other words, you'd slowly scale the penalty as the duration of the 
trade increases. This is better than a single large penalty occurring at a single point in time.

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
      "profit_aim": 0.25,
      "rsi_overbought_threshold": 80,
      "rsi_oversold_threshold": 20
    }
  }
`

for the model type, test PPO, A2c and DQN.
for the policy type, if LSTM policy is available test it too.
"""

import numpy as np
from freqtrade.freqai.prediction_models.ReinforcementLearner import ReinforcementLearner
from freqtrade.freqai.RL.Base5ActionRLEnv import Actions, Base5ActionRLEnv, Positions
from freqtrade.freqai.RL.BaseEnvironment import BaseEnvironment


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

    MyRLEnv: type[BaseEnvironment]

    class MyRLEnv(Base5ActionRLEnv):
        """
        User made custom environment. This class inherits from BaseEnvironment and gym.Env.
        Users can override any functions from those parent classes. Here is an example
        of a user customized `calculate_reward()` function.

        Warning!
        This is function is a showcase of functionality designed to show as many possible
        environment control features as possible. It is also designed to run quickly
        on small computers. This is a benchmark, it is *not* for live production.

        Formula: Volatility is often computed using the standard deviation of price changes over a given period. In Freqtrade,
        it may be done using Python’s pandas library or a custom function that handles price variations.
        """

        def calculate_reward(self, action: int) -> float:
            # Penalize if the action is invalid
            if not self._is_valid(action):
                self.tensorboard_log("invalid", action)
                return -2

            # Get unrealized profit (PnL) and transaction cost
            pnl = self.get_unrealized_profit()
            transaction_cost = self.rl_config.get("transaction_cost", 0.0001)

            # Calculate price change (r_t) and volatility
            price_now = self.current_price()
            price_previous = self.get_previous_price()
            r_t = price_now - price_previous
            volatility = self.calculate_volatility(window=60)

            # Basic reward (adjusted for volatility and transaction costs)
            reward = (pnl - transaction_cost * price_previous) / (
                volatility or 1
            )  # Avoid division by zero

            # Reward for entering trades (using RSI as an example)
            if (
                action in (Actions.Long_enter.value, Actions.Short_enter.value)
                and self._position == Positions.Neutral
            ):
                rsi_now = self.raw_features["%-rsi-period"].iloc[self._current_tick]
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
                reward *= penalty_factor

            # Penalty for sitting too long in position
            if (
                self._position in (Positions.Short, Positions.Long)
                and action == Actions.Neutral.value
            ):
                return -1 * np.log(1 + trade_duration)  # Logarithmic penalty

            # Exit long position reward
            if action == Actions.Long_exit.value and self._position == Positions.Long:
                if pnl > self.profit_aim * self.rl_config["model_reward_parameters"].get("rr", 2):
                    reward *= self.rl_config["model_reward_parameters"].get("win_reward_factor", 2)
                return np.log(1 + abs(pnl)) * reward  # Log scaling for large profits

            # Exit short position reward
            if action == Actions.Short_exit.value and self._position == Positions.Short:
                if pnl > self.profit_aim * self.rl_config["model_reward_parameters"].get("rr", 2):
                    reward *= self.rl_config["model_reward_parameters"].get("win_reward_factor", 2)
                return np.log(1 + abs(pnl)) * reward

            return reward

        def get_previous_price(self) -> float:
            """
            Retrieves the previous price by accessing the 'open' price at the previous tick.
            """
            if self._current_tick > 0:
                return self.prices.iloc[self._current_tick - 1].open
            else:
                # Fallback for the first tick where there is no previous price
                return self.prices.iloc[self._current_tick].open

        def calculate_volatility(self, window: int) -> float:
            """
            Calculate volatility using a rolling standard deviation over the specified window.
            """
            price_series = self.price_series.close.iloc[
                self._current_tick - window : self._current_tick
            ]
            return price_series.pct_change().ewm(span=window, min_periods=1).std().iloc[-1]

        def most_recent_return(self):
            """
            Calculate the tick to tick return if in a trade.
            Return is generated from rising prices in Long
            and falling prices in Short positions.
            The actions Sell/Buy or Hold during a Long position trigger the sell/buy-fee.
            """
            # Long positions
            if self._position == Positions.Long:
                current_price = self.prices.iloc[self._current_tick].open
                previous_price = self.prices.iloc[self._current_tick - 1].open

                if (
                    self._position_history[self._current_tick - 1] == Positions.Short
                    or self._position_history[self._current_tick - 1] == Positions.Neutral
                ):
                    previous_price = self.add_entry_fee(previous_price)

                return np.log(current_price) - np.log(previous_price)

            # Short positions
            if self._position == Positions.Short:
                current_price = self.prices.iloc[self._current_tick].open
                previous_price = self.prices.iloc[self._current_tick - 1].open
                if (
                    self._position_history[self._current_tick - 1] == Positions.Long
                    or self._position_history[self._current_tick - 1] == Positions.Neutral
                ):
                    previous_price = self.add_exit_fee(previous_price)

                return np.log(previous_price) - np.log(current_price)

            return 0
