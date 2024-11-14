import numpy as np
from freqtrade.freqai.prediction_models.ReinforcementLearner import ReinforcementLearner
from freqtrade.freqai.RL.Base5ActionRLEnv import Actions, Base5ActionRLEnv, Positions
from freqtrade.freqai.RL.BaseEnvironment import BaseEnvironment
from ft_strategies.indicators import OptimizedSupportResistanceIndicator


class TradeFlowSRAgent(ReinforcementLearner):
    """
    An agent that uses Support and Resistance levels for decision-making in reinforcement learning.

    Save this file to `freqtrade/user_data/freqaimodels`
    Run with:
        freqtrade trade --freqaimodel TradeFlowSRAgent --config config.json --strategy TradeFlowAgentStrategy
    """

    MyRLEnv: type[BaseEnvironment]

    class MyRLEnv(Base5ActionRLEnv):
        """
        Custom environment class that incorporates support and resistance levels based on SR indicators.
        Provides a reward structure based on price movements, proximity to support/resistance levels, and trade duration.
        """

        def __init__(self, **kwargs):
            """
            Initializes the environment and loads support and resistance levels using `OptimizedSupportResistanceIndicator`.

            Attributes:
            -----------
            sr_indicator: OptimizedSupportResistanceIndicator
                The indicator instance used to calculate support/resistance levels.
            get_all_sr_levels: dict
                Dictionary containing all support and resistance levels.
            """
            super().__init__(**kwargs)
            self.sr_indicator = OptimizedSupportResistanceIndicator(self.raw_features)
            self.get_all_sr_levels = self.sr_indicator.get_all_indicators()

        def calculate_reward(self, action: int) -> float:
            """
            Calculates the reward for a given action, considering PnL, transaction costs, volatility,
            and proximity to support/resistance levels.

            Parameters:
            -----------
            action : int
                The action taken by the agent.

            Returns:
            --------
            float
                The calculated reward for the action.
            """
            if not self._is_valid(action):
                self.tensorboard_log("invalid", action)
                return -2

            pnl = self.get_unrealized_profit()
            transaction_cost = self.rl_config.get("transaction_cost", 0.0001)
            price_now = self.current_price()
            price_previous = self.get_previous_price()
            r_t = price_now - price_previous
            volatility = self.calculate_volatility(window=60) or 1  # Prevent division by zero
            reward = (pnl - transaction_cost * price_previous) / volatility

            if (
                action in (Actions.Long_enter.value, Actions.Short_enter.value)
                and self._position == Positions.Neutral
            ):
                return self._calculate_entry_reward(action, price_now)

            if action == Actions.Neutral.value and self._position == Positions.Neutral:
                return self._calculate_inactivity_penalty()

            trade_duration = self._current_tick - self._last_trade_tick
            reward = self._apply_trade_duration_penalty(reward, trade_duration)

            if action == Actions.Neutral.value and self._position in (
                Positions.Long,
                Positions.Short,
            ):
                return self._calculate_position_hold_penalty(trade_duration)

            if action == Actions.Long_exit.value and self._position == Positions.Long:
                return self._calculate_exit_reward(pnl, reward, action)
            elif action == Actions.Short_exit.value and self._position == Positions.Short:
                return self._calculate_exit_reward(pnl, reward, action)

            return reward

        def _calculate_entry_reward(self, action: int, price_now: float) -> float:
            """
            Calculate reward for entering trades based on proximity to support/resistance levels.

            Parameters:
            -----------
            action : int
                The action taken by the agent (Long or Short entry).
            price_now : float
                The current price of the asset.

            Returns:
            --------
            float
                Calculated reward for the entry action.
            """
            base_reward = 25
            near_support = self.is_near_support(price_now)
            near_resistance = self.is_near_resistance(price_now)

            if action == Actions.Long_enter.value and near_support:
                return base_reward * 3.2 

            elif action == Actions.Short_enter.value and near_resistance:
                return base_reward * 3.2 

            return base_reward

        def _calculate_inactivity_penalty(self) -> float:
            """
            Calculate a penalty for inactivity when the agent remains in a neutral position.

            Returns:
            --------
            float
                Calculated penalty for inactivity.
            """
            return -1 * np.log(1 + self._current_tick - self._last_trade_tick)

        def _apply_trade_duration_penalty(self, reward: float, trade_duration: int) -> float:
            """
            Apply a penalty based on the duration of a trade to discourage prolonged holding.

            Parameters:
            -----------
            reward : float
                The base reward to adjust.
            trade_duration : int
                The duration of the trade in ticks.

            Returns:
            --------
            float
                Adjusted reward with the trade duration penalty applied.
            """
            max_duration = self.rl_config.get("max_trade_duration_candles", 300)
            if trade_duration > max_duration:
                penalty_factor = np.exp(trade_duration / max_duration)
                reward *= penalty_factor
            return reward

        def _calculate_position_hold_penalty(self, trade_duration: int) -> float:
            """
            Calculate a penalty for holding a position without taking action.

            Parameters:
            -----------
            trade_duration : int
                The duration of the trade in ticks.

            Returns:
            --------
            float
                Calculated penalty for holding a position too long.
            """
            return -1 * np.log(1 + trade_duration)

        def _calculate_exit_reward(self, pnl: float, reward: float, action: int) -> float:
            """
            Calculate reward for exiting a position based on profit and configured reward factors.

            Parameters:
            -----------
            pnl : float
                Profit or loss of the position.
            reward : float
                The current reward to adjust.
            action : int
                The exit action taken (Long or Short exit).

            Returns:
            --------
            float
                Adjusted reward for exiting the position.
            """
            reward_params = self.rl_config["model_reward_parameters"]
            rr_target = reward_params.get("rr", 2)
            win_factor = reward_params.get("win_reward_factor", 2)

            if pnl > self.profit_aim * rr_target:
                reward *= win_factor

            return np.log(1 + abs(pnl)) * reward  # Log scaling for larger profits

        def get_previous_price(self) -> float:
            """
            Retrieves the 'open' price of the asset at the previous tick.

            Returns:
            --------
            float
                The previous tick's open price.
            """
            if self._current_tick > 0:
                return self.prices.iloc[self._current_tick - 1].open
            else:
                return self.prices.iloc[self._current_tick].open

        def calculate_volatility(self, window: int) -> float:
            """
            Calculate volatility using a rolling standard deviation over a specified window.

            Parameters:
            -----------
            window : int
                The number of ticks over which to calculate volatility.

            Returns:
            --------
            float
                The calculated volatility.
            """
            price_series = self.price_series.close.iloc[
                self._current_tick - window : self._current_tick
            ]
            return price_series.pct_change().ewm(span=window, min_periods=1).std().iloc[-1]

        def is_near_support(self, price: float, proximity_pct: float = 0.02) -> bool:
            """
            Checks if the current price is near a support level within a specified proximity.

            Parameters:
            -----------
            price : float
                The current price of the asset.
            proximity_pct : float
                The allowable proximity percentage to consider as "near" support.

            Returns:
            --------
            bool
                True if near support, False otherwise.
            """
            support_levels = [level[1] for level in self.get_all_sr_levels["support_levels"]]
            return any(abs(price - level) <= proximity_pct * level for level in support_levels)

        def is_near_resistance(self, price: float, proximity_pct: float = 0.02) -> bool:
            """
            Checks if the current price is near a resistance level within a specified proximity.

            Parameters:
            -----------
            price : float
                The current price of the asset.
            proximity_pct : float
                The allowable proximity percentage to consider as "near" resistance.

            Returns:
            --------
            bool
                True if near resistance, False otherwise.
            """
            resistance_levels = [level[1] for level in self.get_all_sr_levels["resistance_levels"]]
            return any(abs(price - level) <= proximity_pct * level for level in resistance_levels)

        def most_recent_return(self) -> float:
            """
            Calculate the return between the current and previous tick based on position type.

            Returns:
            --------
            float
                The tick-to-tick return, positive for Long positions with rising prices
                and negative for Short positions with falling prices.
            """
            if self._position == Positions.Long:
                current_price = self.prices.iloc[self._current_tick].open
                previous_price = self.prices.iloc[self._current_tick - 1].open

                if self._position_history[self._current_tick - 1] in (
                    Positions.Short,
                    Positions.Neutral,
                ):
                    previous_price = self.add_entry_fee(previous_price)

                return np.log(current_price) - np.log(previous_price)

            if self._position == Positions.Short:
                current_price = self.prices.iloc[self._current_tick].open
                previous_price = self.prices.iloc[self._current_tick - 1].open

                if self._position_history[self._current_tick - 1] in (
                    Positions.Long,
                    Positions.Neutral,
                ):
                    previous_price = self.add_exit_fee(previous_price)

                return np.log(previous_price) - np.log(current_price)

            return 0
