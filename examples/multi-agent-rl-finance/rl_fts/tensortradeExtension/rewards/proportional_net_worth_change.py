from tensortrade.env.default.rewards import TensorTradeRewardScheme
from tensortrade.env.generic import TradingEnv

from rl_fts.tensortradeExtension.actions.buy_sell_hold import BSH

class PNWC(TensorTradeRewardScheme):
    """
       At every time step, reward the agent on the proportional networth change.
            preportion_net_worth_change = (net_worth - self.previous_net_worth) / self.previous_net_worth
    """

    def __init__(self, starting_value: float):
        self.net_worth_history = []
        self.starting_value = starting_value
        self.previous_net_worth = starting_value
        self.total_reward = 0

    def reward(self, env: TradingEnv) -> float:
        return self.get_reward(env.action_scheme)

    def get_reward(self, action_scheme: BSH) -> float:
        """
        Parameters
        ----------
        action_scheme : `BSH | PBSH `
            The action scheme used for managing simple or proportion buy sell hold.
        Returns
            reward = (new_net_worth - old_net_worth) / old_net_worth
        -------
        float
            The difference in networth as profit / loss 
        """
        asset_balance = action_scheme.asset.balance.convert(action_scheme.exchange_pair)
        cash_balance = action_scheme.cash.balance
        net_worth = (asset_balance + cash_balance).as_float()
        if self.previous_net_worth != net_worth:
            preportion_net_worth_change = (net_worth - self.previous_net_worth) / self.previous_net_worth
            self.previous_net_worth = net_worth
        else:
            preportion_net_worth_change = 0
        self.total_reward += preportion_net_worth_change
        self.net_worth_history.append(net_worth)
        return preportion_net_worth_change

    def reset(self) -> None:
        """Resets the history and previous net worth of the reward scheme."""
        self.net_worth_history = []
        self.previous_net_worth = self.starting_value
        self.total_reward = 0
