from typing import Tuple
from tensortrade.env.default.rewards import TensorTradeRewardScheme
from tensortrade.feed.core import Stream, DataFeed

class PPBR(TensorTradeRewardScheme):
    """A simple reward scheme that rewards the agent based on the change in its networth
    """

    registered_name = "cpbr"

    def __init__(self, price: 'Stream') -> None:
        super().__init__()
        self.position = -1
        self.proportion = 0

        position_difference = Stream.sensor(price, lambda p: p.value, dtype="float").diff()
        direction = Stream.sensor(self, lambda self: self.position, dtype="float")

        reward = (direction * position_difference).fillna(0).rename("reward")
        self.feed = DataFeed([reward])
        self.feed.compile()

    def on_action(self, actions: Tuple) -> None:
        self.proportion = actions[1][0]

    def get_reward(self, portfolio: 'Portfolio') -> float:
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
        reward = self.feed.next()["reward"]
        preportion_reward = reward * self.proportion / 100

        return preportion_reward

    def reset(self) -> None:
        """Resets the history and previous net worth of the reward scheme."""
        self.position = -1
        self.feed.reset()
        self.proportion = 0
        

