from tensortrade.env.default.rewards import TensorTradeRewardScheme
from tensortrade.env.generic import TradingEnv

from rl_fts.tensortradeExtension.actions.proportion_short_hold import PSH

class PSNWC(TensorTradeRewardScheme):
    """A simple reward scheme that rewards the agent based on the change in its networth
    """

    def __init__(self, starting_value: float):
        self.net_worth_history = []
        self.reward_history = []
        self.starting_value = starting_value
        self.previous_net_worth = starting_value
        self.total_reward = 0

    def reward(self, env: TradingEnv) -> float:
        return self.get_reward(env.action_scheme)

    def get_reward(self, action_scheme: PSH) -> float:
        """
        Parameters
        ----------
        short_action_scheme : `SH`
            The action scheme used for managing simple short positions.
        Returns
        -------
        float
            The difference in networth as profit / loss 
        """
        # this represents how much asset we currently have in our wallet
        asset_balance = action_scheme.asset.balance.convert(action_scheme.exchange_pair)
        # this represents how much cash we currently have in our wallet
        #   We get cash from the broker when we enter a short position and this cash remains fixed until we exit the short position
        cash_balance = action_scheme.cash.balance
        # this represents how much money we have deposited with the broker as margin for our short position
        #   This value remains fixed until we exit the short position, however interest is charged on this value over time
        deposit_margin = action_scheme.deposit_margin.balance
        # This represents how much, in cash, the borrowed asset is currently worth
        #  This value changes over time as the price of the borrowed asset changes
        borrowed_asset_current_cash_value = action_scheme.borrow_asset.convert(action_scheme.exchange_pair)
        # This represents the current net worth of the agent
        net_worth = (asset_balance + cash_balance + (deposit_margin) - borrowed_asset_current_cash_value).as_float()
        if self.previous_net_worth != net_worth:
            preportion_net_worth_change = (net_worth - self.previous_net_worth) / self.previous_net_worth
            self.previous_net_worth = net_worth
        else:
            preportion_net_worth_change = 0
        self.total_reward += preportion_net_worth_change
        self.net_worth_history.append(net_worth)
        self.reward_history.append(preportion_net_worth_change)
        return preportion_net_worth_change

    def reset(self) -> None:
        """Resets the history and previous net worth of the reward scheme."""
        self.net_worth_history = []
        self.reward_history = []
        self.previous_net_worth = self.starting_value
        self.total_reward = 0
        

