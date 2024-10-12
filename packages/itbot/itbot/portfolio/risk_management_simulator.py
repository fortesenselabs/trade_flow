from typing import List

from packages.itbot.itbot.db import Database


class LevelFailed(Exception):
    """Base class for exceptions related to failing a level in the game."""

    pass


class InsufficientBalance(LevelFailed):
    """Exception raised when failing the starting level due to insufficient balance."""

    pass


class RiskManagementSim:
    """
    This class represents a risk management system for a trading game.
    It calculates risk and reward based on initial balance, contract size, return rates,
    and entry price. It also tracks trade execution and updates balance based on trade outcomes.

    Attributes:
        initial_balance (float): Initial balance for the simulation.
        balance (float): Current balance after each trade.
        previous_balance (float): Balance before the current trade.
        contract_size (float): Contract size for each trade.
        return_rates (List[float]): List of return rates for different difficulty levels.
        total_levels (int): Total number of difficulty levels based on return rates.
        current_level (int): Current difficulty level in the game (starts at 0).
        lot_size (float): Calculated lot size for each trade based on risk and balance.
        previous_lot_size (float): Previous lot size used for calculating subsequent lot sizes.
        take_profit_pips (int): Target profit in pips for each trade.
        trade_type (str): "buy" or "sell" for the current trade.
        entry_price (float): Entry price for the current trade.
        stop_loss_pips (int): Calculated stop loss in pips for each trade.
        sl_price (float): Stop loss price calculated based on entry price and stop loss pips.
        tp_price (float): Take profit price calculated based on entry price and take profit pips.
        stage (str): Current stage of the trade ("Pending", "Executed", "Closed").
        risk_dollars (float): Calculated risk amount in dollars for each trade.
        profit_dollars (float): Calculated potential profit amount in dollars for each trade.
        profit_percentage (float): Calculated potential profit percentage for each trade.
        risk_reward_ratio (float): Calculated risk-reward ratio for each trade.
        ending_balance (List[float]): List to store the balance history after each level.
        history (List[dict]): List to store individual trade details and results.
    """

    def __init__(
        self,
        initial_balance: float = 20,
        contract_size: float = 10,
        return_rates: List[float] = [3] * 10,
    ):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.previous_balance = initial_balance
        self.contract_size = contract_size
        self.return_rates = return_rates
        self.total_levels = len(return_rates)  # Set the total game levels
        self.current_level = 0  # Track the current level in the game
        self.lot_size = (0.03 / 3) * 10  # Initial lot size calculation
        self.previous_lot_size = self.lot_size
        self.take_profit_pips = 15  # Updated take profit pips to 15
        self.trade_type = "buy"  # Example initial trade type
        self.entry_price = 8000  # Example initial entry price
        self.stop_loss_pips = self.calculate_stop_loss_pips()  # Initialize stop loss pips
        self.sl_price = None
        self.tp_price = None
        self.stage = "Pending"  # Initial stage
        self.risk_dollars = self.calculate_risk_dollars()
        self.profit_dollars = self.calculate_profit_dollars()
        self.profit_percentage = self.calculate_profit_percentage()
        self.risk_reward_ratio = self.calculate_risk_reward_ratio()
        self.ending_balance = []  # To store the balance history
        self.history = []  # To store trading history

    @staticmethod
    def generate_return_rates(
        target_returns: List[float], period_per_return: int = 3, total_periods: int = 30
    ):
        """
        Generates a list of return rates based on provided target returns, period per return, and total period.

        Args:
            target_returns (List[float]): List of target return values for each segment.
            period_per_return (int): Number of periods for each target return value. Default is 3.
            total_periods (int): Total number of periods to generate return rates for. Default is 30.

        Returns:
            list: A list of return rates for the specified total period.

        Raises:
            ValueError: If the total period is not divisible by the length of target_returns.
        """
        if total_periods % len(target_returns) != 0:
            raise ValueError("Total periods must be divisible by the number of target returns")

        if total_periods % period_per_return != 0:
            raise ValueError("Total periods must be divisible by the period per return")

        return_rates = []
        for return_value in target_returns:
            if len(return_rates) < total_periods:
                return_rates.extend([return_value] * period_per_return)

        return return_rates, total_periods

    def calculate_risk_dollars(self):
        if self.current_level == 0:
            return (10 * self.lot_size) * self.stop_loss_pips
        else:
            return self.balance - self.previous_balance

    def current_risk_percentage(self):
        return self.calculate_risk_dollars() / self.balance

    def calculate_profit_dollars(self):
        return (self.take_profit_pips * self.contract_size) * self.lot_size

    def calculate_profit_percentage(self):
        return self.profit_dollars / self.balance

    def calculate_risk_reward_ratio(self):
        return self.profit_dollars / self.risk_dollars

    def set_trade(self, entry_price, take_profit_pips, trade_type):
        self.entry_price = entry_price
        self.take_profit_pips = take_profit_pips
        self.trade_type = trade_type
        self.calculate_lot_size()
        self.stop_loss_pips = self.calculate_stop_loss_pips()
        self.calculate_sl_tp_prices()
        self.risk_dollars = self.calculate_risk_dollars()
        self.profit_dollars = self.calculate_profit_dollars()
        self.profit_percentage = self.calculate_profit_percentage()
        self.risk_reward_ratio = self.calculate_risk_reward_ratio()

    def calculate_stop_loss_pips(self):
        return_rate = self.return_rates[self.current_level % len(self.return_rates)]
        if self.current_level == 0:
            return self.take_profit_pips / return_rate
        else:
            return (self.risk_dollars / self.lot_size) / 10

    def calculate_sl_tp_prices(self):
        if self.trade_type.lower() == "buy":
            self.sl_price = self.entry_price - self.stop_loss_pips
            self.tp_price = self.entry_price + self.take_profit_pips
        elif self.trade_type.lower() == "sell":
            self.sl_price = self.entry_price + self.stop_loss_pips
            self.tp_price = self.entry_price - self.take_profit_pips

    def calculate_lot_size(self):
        if self.current_level != 0:
            return_rate = self.return_rates[self.current_level % len(self.return_rates)]
            self.lot_size = self.previous_lot_size * return_rate  # Subsequent lot size calculation
        self.previous_lot_size = self.lot_size

    def execute_trade(self, db):
        print(f"Executing {self.trade_type.upper()} trade:")
        print(f"Entry Price: {self.entry_price}")
        print(f"Stop Loss Price: {self.sl_price}")
        print(f"Take Profit Price: {self.tp_price}")
        print(f"Lot Size: {self.lot_size:.2f}")
        print(f"Risk/Reward Ratio: {self.risk_reward_ratio:.2f}")
        self.stage = "Executed"
        db.insert_trade(
            self.trade_type,
            self.entry_price,
            self.sl_price,
            self.tp_price,
            self.lot_size,
            self.stage,
        )
        self.history.append(
            {
                "level": self.current_level,
                "trade_type": self.trade_type,
                "entry_price": self.entry_price,
                "sl_price": self.sl_price,
                "tp_price": self.tp_price,
                "lot_size": self.lot_size,
                "risk_reward_ratio": self.risk_reward_ratio,
                "status": "Executed",
            }
        )

    def update_trade_status(self, db, trade_id, hit_tp=False):
        self.stage = "Closed"
        status = "TP Hit" if hit_tp else "SL Hit"
        db.update_trade_status(trade_id, status)
        # Update balance based on the result of the trade
        self.previous_balance = self.balance
        if hit_tp:
            self.balance += self.profit_dollars
        else:
            self.balance -= self.risk_dollars
            if self.current_level == 0:
                raise InsufficientBalance(
                    f"Level {self.current_level + 1} Failed. Top up your balance to start again."
                )

        # Store the ending balance of the current level
        self.ending_balance.append(self.balance)

        # Update history with trade result
        self.history[-1]["status"] = status
        self.history[-1]["ending_balance"] = self.balance

        # Recalculate risk and profit dollars for the next level
        self.risk_dollars = self.calculate_risk_dollars()
        self.profit_dollars = self.calculate_profit_dollars()
        self.profit_percentage = self.calculate_profit_percentage()
        self.risk_reward_ratio = self.calculate_risk_reward_ratio()

        self.current_level += 1  # Move to the next level in the game


def simulate_trades(
    initial_balance: float,
    contract_size: float,
    return_rates: List[float],
    num_trades: int,
):
    db = Database()
    risk_management = RiskManagementSim(
        initial_balance=initial_balance,
        contract_size=contract_size,
        return_rates=return_rates,
    )

    for i in range(num_trades):
        risk_management.set_trade(entry_price=8000 + i, take_profit_pips=15, trade_type="buy")
        risk_management.execute_trade(db)
        risk_management.update_trade_status(
            db, trade_id=i + 1, hit_tp=True
        )  # Simulating hitting take profit for each trade

    final_balance = risk_management.balance
    balance_history = risk_management.ending_balance
    trade_history = risk_management.history
    db.close()
    return final_balance, balance_history, trade_history


# Example usage
if __name__ == "__main__":
    initial_balance = 20
    contract_size = 1
    return_rates, total_periods = RiskManagementSim.generate_return_rates(
        target_returns=[3, 1, 2, 1, 1.5, 1, 1.2, 1, 1.2, 1],
        period_per_return=3,
        total_periods=30,
    )

    num_trades = total_periods

    final_balance, balance_history, trade_history = simulate_trades(
        initial_balance, contract_size, return_rates, num_trades
    )
    print(f"Final balance after {num_trades} trades: ${final_balance:.2f}")
    print(f"Balance history: {balance_history}")
    print(f"Return Rates: {return_rates}")
