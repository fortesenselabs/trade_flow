from rl_fts.environments.stock.environment1 import create_env
from tensortrade.env.generic import TradingEnv
import random

def main():
    config = {
        "type": "train",
        "window_size": 30,
        "min_periods": 30,
        "max_allowed_loss": 1,
    }

    env: TradingEnv = create_env(config)

    for _ in range(10):
        action = random.randint(0,2)
        env.step(action=action)

main()