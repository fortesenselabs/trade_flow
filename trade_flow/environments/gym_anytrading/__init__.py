from copy import deepcopy
from trade_flow.environments.generic import register_gym_env

from . import datasets

# v0

register_gym_env(
    id="forex-v0",
    entry_point="trade_flow.environments.gym_anytrading.envs:ForexEnv",
    kwargs={
        "df": deepcopy(datasets.FOREX_EURUSD_1H_ASK),
        "window_size": 24,
        "frame_bound": (24, len(datasets.FOREX_EURUSD_1H_ASK)),
    },
)

register_gym_env(
    id="stocks-v0",
    entry_point="trade_flow.environments.gym_anytrading.envs:StocksEnv",
    kwargs={
        "df": deepcopy(datasets.STOCKS_GOOGL),
        "window_size": 30,
        "frame_bound": (30, len(datasets.STOCKS_GOOGL)),
    },
)
