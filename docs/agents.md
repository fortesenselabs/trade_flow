# Agents

This is where the "deep" part of the deep reinforcement learning framework come in. Learning agents are where the math (read: magic) happens. In the context of TradeFlow, an **agent** is an autonomous decision-making entity responsible for executing trading strategies. It interacts with the trading environment (market) by observing market data, making trading decisions, and executing orders.

At each time step, the agent takes the observation from the environment as input, runs it through its underlying model (a neural network most of the time), and outputs the action to take. For example, the observation might be the previous `open`, `high`, `low`, and `close` price from the exchange. The learning model would take these values as input and output a value corresponding to the action to take, such as `buy`, `sell`, or `hold`.

It is important to remember the learning model has no intuition of the prices or trades being represented by these values. Rather, the model is simply learning which values to output for specific input values or sequences of input values, to earn the highest reward.

In this example, we will be using the Stable Baselines library to provide learning agents to our trading scheme, however, the TradeFlow framework is compatible with many reinforcement learning libraries such as Tensorforce, Ray's RLLib, OpenAI's Baselines, Intel's Coach, or anything from the TensorFlow line such as TF Agents.

It is possible that custom TradeFlow learning agents will be added to this framework in the future, though it will always be a goal of the framework to be interoperable with as many existing reinforcement learning libraries as possible, since there is so much concurrent growth in the space.
But for now, Stable Baselines is simple and powerful enough for our needs.

![Image of a flowchart depicting the decision-making process of a deep reinforcement learning agent](./images/Schematic-structure-of-deep-reinforcement-learning-agent_W640.jpg)

## [Ray](https://docs.ray.io/en/latest/rllib.html)

The following is an example of how to train a strategy on `ray` using the `PPO`
algorithm.

```python
import ray
import numpy as np

from ray import tune
from ray.tune.registry import register_env

import trade_flow.environments.default as default

from trade_flow.core.feed import DataFeed, Stream
from trade_flow.model.instruments import Instrument
from trade_flow.model.exchanges import Exchange
from trade_flow.model.services.execution.simulated import execute_order
from trade_flow.model.wallets import Wallet, Portfolio


USD = Instrument("USD", 2, "U.S. Dollar")
TTC = Instrument("TFC", 8, "TradeFlow Coin")


def create_env(config):
    x = np.arange(0, 2*np.pi, 2*np.pi / 1000)
    p = Stream.source(50*np.sin(3*x) + 100, dtype="float").rename("USD-TTC")

    bitfinex = Exchange("bitfinex", service=execute_order)(
        p
    )

    cash = Wallet(bitfinex, 100000 * USD)
    asset = Wallet(bitfinex, 0 * TTC)

    portfolio = Portfolio(USD, [
        cash,
        asset
    ])

    feed = DataFeed([
        p,
        p.rolling(window=10).mean().rename("fast"),
        p.rolling(window=50).mean().rename("medium"),
        p.rolling(window=100).mean().rename("slow"),
        p.log().diff().fillna(0).rename("lr")
    ])

    reward_scheme = default.rewards.PBR(price=p)

    action_scheme = default.actions.BSH(
        cash=cash,
        asset=asset
    ).attach(reward_scheme)

    env = default.create(
        feed=feed,
        portfolio=portfolio,
        action_scheme=action_scheme,
        reward_scheme=reward_scheme,
        window_size=config["window_size"],
        max_allowed_loss=0.6
    )
    return env

register_env("TradingEnv", create_env)


analysis = tune.run(
    "PPO",
    stop={
      "episode_reward_mean": 500
    },
    config={
        "env": "TradingEnv",
        "env_config": {
            "window_size": 25
        },
        "log_level": "DEBUG",
        "framework": "torch",
        "ignore_worker_failures": True,
        "num_workers": 1,
        "num_gpus": 0,
        "clip_rewards": True,
        "lr": 8e-6,
        "lr_schedule": [
            [0, 1e-1],
            [int(1e2), 1e-2],
            [int(1e3), 1e-3],
            [int(1e4), 1e-4],
            [int(1e5), 1e-5],
            [int(1e6), 1e-6],
            [int(1e7), 1e-7]
        ],
        "gamma": 0,
        "observation_filter": "MeanStdFilter",
        "lambda": 0.72,
        "vf_loss_coeff": 0.5,
        "entropy_coeff": 0.01
    },
    checkpoint_at_end=True
)

```

And then to restore the agent just use the following code.

```python
import ray.rllib.agents.ppo as ppo

# Get checkpoint
checkpoints = analysis.get_trial_checkpoints_paths(
    trial=analysis.get_best_trial("episode_reward_mean"),
    metric="episode_reward_mean"
)
checkpoint_path = checkpoints[0][0]

# Restore agent
agent = ppo.PPOTrainer(
    env="TradingEnv",
    config={
        "env_config": {
            "window_size": 25
        },
        "framework": "torch",
        "log_level": "DEBUG",
        "ignore_worker_failures": True,
        "num_workers": 1,
        "num_gpus": 0,
        "clip_rewards": True,
        "lr": 8e-6,
        "lr_schedule": [
            [0, 1e-1],
            [int(1e2), 1e-2],
            [int(1e3), 1e-3],
            [int(1e4), 1e-4],
            [int(1e5), 1e-5],
            [int(1e6), 1e-6],
            [int(1e7), 1e-7]
        ],
        "gamma": 0,
        "observation_filter": "MeanStdFilter",
        "lambda": 0.72,
        "vf_loss_coeff": 0.5,
        "entropy_coeff": 0.01
    }
)
agent.restore(checkpoint_path)
```

## [Stable Baselines](https://stable-baselines.readthedocs.io/en/master/)

```python
from stable_baselines.common.policies import MlpLnLstmPolicy
from stable_baselines import PPO2

model = PPO2
policy = MlpLnLstmPolicy
params = { "learning_rate": 1e-5 }

agent = model(policy, environment, model_kwargs=params)
```

## Key Components of a TradeFlow Agent

1. **Perception:**
   - Receives market data (prices, volumes, indicators) from the environment.
   - Processes and interprets data to extract relevant information.
2. **Decision Making:**
   - Employs trading strategies and algorithms to analyze market conditions.
   - Determines optimal actions (buy, sell, hold) based on the current state.
3. **Execution:**
   - Sends trading orders to the execution platform.
   - Manages order lifecycle (placement, modification, cancellation).
4. **Learning (Optional):**
   - For reinforcement learning-based agents, continuously learns from trading experiences to improve performance.

## Types of TradeFlow Agents

1. **Rule-Based Agent:**
   - Follows predefined trading rules and conditions.
   - Typically simpler to implement but less adaptable to changing market conditions.
2. **Technical Agent:**
   - Employs advanced algorithms (e.g., moving averages, RSI, Bollinger Bands) for decision making.
   - Offers more flexibility than rule-based agents.
3. **Non-Self Learning Agent:**
   - Leverages machine learning techniques (e.g., decision trees, neural networks) to learn from historical data and make predictions.
   - Can adapt to complex market patterns and potentially outperform traditional methods.
4. **Self Learning Agent:**
   - Learns optimal trading strategies through interaction with the environment.
   - Requires extensive training but can achieve high performance in dynamic markets.

**PS:** We will focus on number 4 for now.

## Agent Architecture (Optional)

A typical TradeFlow agent can be structured as follows:

```python
class Agent:
    def __init__(self, environment, strategy):
        self.environment = environment
        self.strategy = strategy

    def perceive(self):
        # Observe market data from environment
        pass

    def decide(self):
        # Make trading decision based on strategy and observations
        pass

    def act(self):
        # Execute trading order
        pass

    def learn(self):
        # Update agent's knowledge based on experience (optional)
        pass
```

## Agent Evaluation

To assess agent performance, key metrics such as:

- Profit and loss
- Sharpe ratio
- Maximum drawdown
- Win rate
- Average holding period
  should be considered.
