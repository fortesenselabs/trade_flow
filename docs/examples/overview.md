# Code Structure

The TradeFlow library is modular. The `trade_flow` library usually has a
common setup when using components. If you wish to make a particular class a
component all you need to do is subclass `Component`.

```python
class Example(Component):
    """An example component to show how to subclass."""

    def foo(self, arg1, arg2) -> str:
        """A method to return a string."""
        raise NotImplementedError()

    def bar(self, arg1, arg2, **kwargs) -> int:
        """A method to return an integer."""
```

From this abstract base class, more concrete and custom subclasses can be made
that provide the implementation of these methods.

<br>**Example of Structure**<br>
A good example of this structure is the `RewardScheme` component. This component
controls the reward mechanism of a `TradingEnvironment`.

The beginning of the code in [RewardScheme](https://github.com/fortesenselabs/trade_flow/blob/master/trade_flow/environments/generic/components/reward_scheme.py) is seen here.

```python
from abc import abstractmethod

from trade_flow.core.component import Component
from trade_flow.core import TimeIndexed


class RewardScheme(Component, TimeIndexed):
    """A component to compute the reward at each step of an episode."""

    registered_name = "rewards"

    @abstractmethod
    def reward(self, env: 'TradingEnv') -> float:
        """Computes the reward for the current step of an episode.

        Parameters
        ----------
        env : `TradingEnv`
            The trading environment

        Returns
        -------
        float
            The computed reward.
        """
        raise NotImplementedError()

    def reset(self) -> None:
        """Resets the reward scheme."""
        pass
```

As you can see above, the [RewardScheme](https://github.com/fortesenselabs/trade_flow/blob/master/trade_flow/environments/generic/components/reward_scheme.py) has a majority of the
structural and mechanical details that guide all other representations of that
type of class. When creating a new reward scheme, one needs to add further
details for how information from then environment gets converted into a reward.
