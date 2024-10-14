import logging
from typing import Optional, Callable, List
from trade_flow.common.logging import Logger


class RiskManager:
    """
    Risk Management class to support multiple strategies for position sizing and risk control.
    """

    def __init__(
        self,
        initial_balance: float,
        risk_percentage: float = 1.0,
        contract_size: float = 1.0,
        drawdown_factor: float = 0.5,  # Risk reduction during drawdown
        profit_factor: float = 1.5,  # Risk increment during profit
        logger: Optional[Logger] = None,
    ) -> None:
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.risk_percentage = risk_percentage
        self.contract_size = contract_size
        self.drawdown_factor = drawdown_factor
        self.profit_factor = profit_factor
        self.current_strategy: Optional[Callable] = self.fixed_percentage_strategy
        self.logger = logger or Logger(name="it_bot", log_level=logging.DEBUG, filename="ITBot.log")

        # Track the equity curve
        self.equity_curve: List[float] = [initial_balance]

    def _equity_curve_scaling_factor(self) -> float:
        """
        Calculate a scaling factor based on the account's equity curve.

        Returns:
            float: Scaling factor based on the equity curve.
        """
        # Current performance relative to the highest equity achieved
        max_equity = max(self.equity_curve)
        min_equity = min(self.equity_curve)
        current_equity = self.current_balance

        if current_equity < max_equity:  # In a drawdown
            drawdown_percent = (max_equity - current_equity) / max_equity
            return max(1.0 - (drawdown_percent * self.drawdown_factor), 0.1)  # Scale down
        elif current_equity > min_equity:  # In a profit phase
            profit_percent = (current_equity - min_equity) / min_equity
            return min(1.0 + (profit_percent * self.profit_factor), 3.0)  # Scale up
        else:
            return 1.0  # No change

    def select_strategy(self, strategy_name: str) -> None:
        """
        Dynamically switch between different strategies.

        Args:
            strategy_name (str): Name of the strategy to use.
        """
        strategies = {
            "fixed_percentage": self.fixed_percentage_strategy,
            "kelly_criterion": self.kelly_criterion_strategy,
            "martingale": self.martingale_strategy,
            "mean_reversion": self.mean_reversion_strategy,
            "equity_curve": self.equity_curve_strategy,
            "volatility_based": self.volatility_based_strategy,
        }

        if strategy_name not in strategies:
            raise ValueError(f"Strategy {strategy_name} is not supported")
        self.current_strategy = strategies[strategy_name]
        self.logger.info(f"Selected Strategy: {strategy_name}")

    def update_balance(self, new_balance: float) -> None:
        """
        Update the current balance and track equity curve.

        Args:
            new_balance (float): Updated balance after a trade.
        """
        self.current_balance = new_balance
        self.equity_curve.append(new_balance)
        self.logger.info(f"Updated balance: {new_balance}")

    def calculate_position_size(
        self,
        current_balance: Optional[float] = None,
        min_position_size: float = 0.01,
        max_position_size: float = 100.0,
        **kwargs,
    ) -> float:
        """
        Calculate the position size based on the currently selected strategy.

        Args:
            current_balance (Optional[float]): The current account balance. If not provided, defaults to the current balance of the risk manager instance.
            min_position_size (float): The minimum allowable position size based on broker or exchange restrictions. Default is 0.01.
            max_position_size (float): The maximum allowable position size based on broker or exchange restrictions. Default is 100.0.
            **kwargs: Additional parameters that can be passed to specific strategies.

        Returns:
            float: The calculated position size, constrained by the minimum and maximum position size limits.

        The function first calculates the position size based on the currently selected strategy (e.g., fixed percentage, Kelly criterion, etc.).
        It then ensures that the position size is within the bounds of the specified minimum and maximum limits. If the calculated position size is
        smaller than the minimum, it is adjusted up to the minimum. If it exceeds the maximum, it is adjusted down to the maximum. This ensures
        compliance with broker or exchange restrictions, preventing invalid position sizes.
        """
        if current_balance is None:
            current_balance = self.current_balance

        # Use the selected strategy for position size calculation.
        position_size = self.current_strategy(current_balance=current_balance, **kwargs)

        # Constrain position size within the broker's/exchange's min and max limits
        position_size = max(min_position_size, min(position_size, max_position_size))

        self.logger.info(f"Calculated position size: {position_size}")
        return position_size

    def fixed_percentage_strategy(self, current_balance: float, **kwargs) -> float:
        """
        Fixed Percentage Strategy.
        Calculate position size as a fixed percentage of the current balance.

        Args:
            current_balance (float): The current account balance.

        Returns:
            float: Position size.
        """
        return (self.risk_percentage / 100) * current_balance / self.contract_size

    def equity_curve_strategy(self, current_balance: float, **kwargs) -> float:
        """
        Calculate position size based on the equity curve strategy.

        Args:
            current_balance (float): The current trading balance.

        Returns:
            float: The position size.
        """
        # Equity curve strategy might adjust risk based on the account's equity curve growth.
        base_position_size = current_balance * self.risk_percentage

        # Apply the equity curve risk management scaling factor.
        return base_position_size * self._equity_curve_scaling_factor()

    def kelly_criterion_strategy(
        self,
        win_probability: float = 0.55,
        reward_risk_ratio: float = 1.5,
        current_balance: float = 0,
        **kwargs,
    ) -> float:
        """
        Kelly Criterion Strategy.

        Args:
            win_probability (float): Probability of a win (0.0 - 1.0).
            reward_risk_ratio (float): Reward-to-risk ratio for trades.
            current_balance (float): Current balance.

        Returns:
            float: Position size.
        """
        kelly_fraction = (win_probability * (reward_risk_ratio + 1) - 1) / reward_risk_ratio
        return kelly_fraction * current_balance / self.contract_size

    def martingale_strategy(
        self, base_lot: float = 0.01, losses_in_a_row: int = 0, **kwargs
    ) -> float:
        """
        Martingale Strategy.
        Double the position size after each loss, reset after a win.

        Args:
            base_lot (float): Base position size.
            losses_in_a_row (int): Consecutive losses count.

        Returns:
            float: Position size.
        """
        return base_lot * (2**losses_in_a_row)

    def mean_reversion_strategy(
        self, mean_price: float, current_price: float, mean_deviation: float = 0.1, **kwargs
    ) -> float:
        """
        Mean Reversion Strategy.
        Increase position size when the current price is far from the mean, reduce it otherwise.

        Args:
            mean_price (float): The mean price value.
            current_price (float): The current market price.
            mean_deviation (float): Deviation factor.

        Returns:
            float: Position size.
        """
        distance_from_mean = abs(current_price - mean_price) / mean_price
        if distance_from_mean > mean_deviation:
            return self.fixed_percentage_strategy(current_balance=self.current_balance) * 1.5
        else:
            return self.fixed_percentage_strategy(current_balance=self.current_balance) * 0.75

    def volatility_based_strategy(
        self, atr_value: float, current_balance: float, **kwargs
    ) -> float:
        """
        Volatility-Based Strategy.
        Calculate position size based on volatility (e.g., ATR). Position size is inversely proportional to volatility.

        Args:
            atr_value (float): Average True Range (ATR) value representing market volatility.
            current_balance (float): Current account balance.

        Returns:
            float: Position size.
        """
        if atr_value <= 0:
            raise ValueError("ATR value must be greater than zero")

        return (self.risk_percentage / 100) * current_balance / (atr_value * self.contract_size)
