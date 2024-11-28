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


class TradeFlowSimpleAgent(ReinforcementLearner):
    """
    A user-defined reinforcement learning (RL) prediction model for Freqtrade, tailored with custom reward
    and action logic.

    Save this file to `freqtrade/user_data/freqaimodels`.
    
    Usage:
    ------
        freqtrade trade --freqaimodel TradeFlowSimpleAgent --config config.json --strategy TradeFlowAgentStrategy

    Notes:
    ------
    Users can override any methods in the `IFreqaiModel` inheritance tree for customization, including 
    reward function (`calculate_reward`) and other core functions like `fit`, `train`, or `predict`.

    """

    MyRLEnv: type[BaseEnvironment]

    class MyRLEnv(Base5ActionRLEnv):
        """
        Custom environment for reinforcement learning in Freqtrade, inheriting from BaseEnvironment and gym.Env.
        Includes a customized reward function (`calculate_reward`) that balances trade profitability, 
        trade duration, inactivity penalties, and transaction costs.

        **Warning**:
            This environment setup is intended as a functional showcase and is optimized for benchmark
            purposes. It may not be suitable for production.
        """

        def calculate_reward(self, action: int) -> float:
            """
            Calculate the reward for the agent's action, based on unrealized profit/loss (PnL),
            transaction costs, trade duration, and volatility scaling.

            Parameters:
            -----------
            action : int
                Action taken by the agent (Long, Short, Neutral, Exit Long, Exit Short).

            Returns:
            --------
            float
                Reward for the chosen action.
            """

            # Penalize invalid actions
            if not self._is_valid(action):
                self.tensorboard_log("invalid", action)
                return -2

            # Retrieve PnL and transaction cost
            pnl = self.get_unrealized_profit()
            transaction_cost = self.rl_config.get("transaction_cost", 0.0001)

            # Calculate price change and volatility
            price_now = self.current_price()
            price_previous = self.get_previous_price()
            r_t = price_now - price_previous
            volatility = self.calculate_volatility(window=60) or 1  # Avoid division by zero

            # Base reward adjusted for volatility and transaction costs
            reward = (pnl - transaction_cost * price_previous) / volatility

            # Reward for entering trades
            if action in (Actions.Long_enter.value, Actions.Short_enter.value) and self._position == Positions.Neutral:
                return self._calculate_entry_reward()

            # Penalty for inactivity
            if action == Actions.Neutral.value and self._position == Positions.Neutral:
                return self._calculate_inactivity_penalty()

            # Adjust reward based on trade duration
            reward = self._apply_trade_duration_penalty(reward)

            # Penalty for holding a position too long without action
            if action == Actions.Neutral.value and self._position in (Positions.Long, Positions.Short):
                return self._calculate_position_hold_penalty()

            # Reward for exiting positions
            if action == Actions.Long_exit.value and self._position == Positions.Long:
                return self._calculate_exit_reward(pnl, reward, "long")

            if action == Actions.Short_exit.value and self._position == Positions.Short:
                return self._calculate_exit_reward(pnl, reward, "short")

            return reward

        def _calculate_entry_reward(self) -> float:
            """
            Calculate the reward for entering a trade based on RSI and favorable conditions.
            
            Returns:
            --------
            float
                Entry reward value.
            """
            base_reward = 25
            rsi_now = self.raw_features["%-rsi-period"].iloc[self._current_tick]
            factor = 40 / rsi_now if rsi_now < 40 else 1
            return base_reward * factor

        def _calculate_inactivity_penalty(self) -> float:
            """
            Calculate a penalty for inactivity when the agent stays in a neutral position for too long.

            Returns:
            --------
            float
                Inactivity penalty value.
            """
            return -1 * np.log(1 + self._current_tick - self._last_trade_tick)

        def _apply_trade_duration_penalty(self, reward: float) -> float:
            """
            Adjust reward based on the duration of a trade to discourage overly long positions.

            Parameters:
            -----------
            reward : float
                Initial reward to adjust based on trade duration.

            Returns:
            --------
            float
                Reward adjusted by trade duration penalty.
            """
            max_duration = self.rl_config.get("max_trade_duration_candles", 300)
            trade_duration = self._current_tick - self._last_trade_tick
            if trade_duration > max_duration:
                penalty_factor = np.exp(trade_duration / max_duration)
                reward *= penalty_factor
            return reward

        def _calculate_position_hold_penalty(self) -> float:
            """
            Apply a penalty for holding a position without taking any further action.

            Returns:
            --------
            float
                Penalty for prolonged holding without action.
            """
            trade_duration = self._current_tick - self._last_trade_tick
            return -1 * np.log(1 + trade_duration)

        def _calculate_exit_reward(self, pnl: float, reward: float, position_type: str) -> float:
            """
            Calculate the reward for exiting a position, with scaling based on PnL and reward factors.

            Parameters:
            -----------
            pnl : float
                Profit or loss from the position.
            reward : float
                Current reward to adjust.
            position_type : str
                Type of position being exited ('long' or 'short').

            Returns:
            --------
            float
                Reward for exiting the position.
            """
            reward_params = self.rl_config["model_reward_parameters"]
            rr_target = reward_params.get("rr", 2)
            win_factor = reward_params.get("win_reward_factor", 2)

            if pnl > self.profit_aim * rr_target:
                reward *= win_factor

            return np.log(1 + abs(pnl)) * reward  # Log scaling for larger profits

        def get_previous_price(self) -> float:
            """
            Retrieve the 'open' price at the previous tick.

            Returns:
            --------
            float
                Previous tick's open price.
            """
            if self._current_tick > 0:
                return self.prices.iloc[self._current_tick - 1].open
            else:
                return self.prices.iloc[self._current_tick].open

        def calculate_volatility(self, window: int) -> float:
            """
            Calculate volatility over a specified window using rolling standard deviation.

            Parameters:
            -----------
            window : int
                Number of ticks for calculating volatility.

            Returns:
            --------
            float
                Calculated volatility.
            """
            price_series = self.price_series.close.iloc[self._current_tick - window : self._current_tick]
            return price_series.pct_change().ewm(span=window, min_periods=1).std().iloc[-1]
