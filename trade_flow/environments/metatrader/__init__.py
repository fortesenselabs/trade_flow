from gymnasium.envs.registration import register

from .terminal import Timeframe, SymbolInfo
from .simulator import Simulator, OrderType, Order, SymbolNotFound, OrderNotFound
from .envs import MT5Env
from .data import FOREX_DATA_PATH, STOCKS_DATA_PATH, CRYPTO_DATA_PATH, MIXED_DATA_PATH


register(
    id="forex-hedge-v0",
    entry_point="trade_flow.environments.metatrader.envs:MT5Env",
    kwargs={
        "original_simulator": Simulator(symbols_filename=FOREX_DATA_PATH, hedge=True),
        "trading_symbols": ["EURUSD", "GBPCAD", "USDJPY"],
        "window_size": 10,
        "symbol_max_orders": 2,
        "fee": lambda symbol: 0.03 if "JPY" in symbol else 0.0003,
    },
)

register(
    id="forex-unhedge-v0",
    entry_point="trade_flow.environments.metatrader.envs:MT5Env",
    kwargs={
        "original_simulator": Simulator(symbols_filename=FOREX_DATA_PATH, hedge=False),
        "trading_symbols": ["EURUSD", "GBPCAD", "USDJPY"],
        "window_size": 10,
        "fee": lambda symbol: 0.03 if "JPY" in symbol else 0.0003,
    },
)

register(
    id="stocks-hedge-v0",
    entry_point="trade_flow.environments.metatrader.envs:MT5Env",
    kwargs={
        "original_simulator": Simulator(symbols_filename=STOCKS_DATA_PATH, hedge=True),
        "trading_symbols": ["GOOG", "AAPL", "TSLA", "MSFT"],
        "window_size": 10,
        "symbol_max_orders": 2,
        "fee": 0.2,
    },
)

register(
    id="stocks-unhedge-v0",
    entry_point="trade_flow.environments.metatrader.envs:MT5Env",
    kwargs={
        "original_simulator": Simulator(symbols_filename=STOCKS_DATA_PATH, hedge=False),
        "trading_symbols": ["GOOG", "AAPL", "TSLA", "MSFT"],
        "window_size": 10,
        "fee": 0.2,
    },
)

register(
    id="crypto-hedge-v0",
    entry_point="trade_flow.environments.metatrader.envs:MT5Env",
    kwargs={
        "original_simulator": Simulator(symbols_filename=CRYPTO_DATA_PATH, hedge=True),
        "trading_symbols": ["BTCUSD", "ETHUSD", "BCHUSD"],
        "window_size": 10,
        "symbol_max_orders": 2,
        "fee": lambda symbol: {
            "BTCUSD": 50.0,
            "ETHUSD": 3.0,
            "BCHUSD": 0.5,
        }[symbol],
    },
)

register(
    id="crypto-unhedge-v0",
    entry_point="trade_flow.environments.metatrader.envs:MT5Env",
    kwargs={
        "original_simulator": Simulator(symbols_filename=CRYPTO_DATA_PATH, hedge=False),
        "trading_symbols": ["BTCUSD", "ETHUSD", "BCHUSD"],
        "window_size": 10,
        "fee": lambda symbol: {
            "BTCUSD": 50.0,
            "ETHUSD": 3.0,
            "BCHUSD": 0.5,
        }[symbol],
    },
)

register(
    id="mixed-hedge-v0",
    entry_point="trade_flow.environments.metatrader.envs:MT5Env",
    kwargs={
        "original_simulator": Simulator(symbols_filename=MIXED_DATA_PATH, hedge=True),
        "trading_symbols": ["EURUSD", "USDCAD", "GOOG", "AAPL", "BTCUSD", "ETHUSD"],
        "window_size": 10,
        "symbol_max_orders": 2,
        "fee": lambda symbol: {
            "EURUSD": 0.0002,
            "USDCAD": 0.0005,
            "GOOG": 0.15,
            "AAPL": 0.01,
            "BTCUSD": 50.0,
            "ETHUSD": 3.0,
        }[symbol],
    },
)

register(
    id="mixed-unhedge-v0",
    entry_point="trade_flow.environments.metatrader.envs:MT5Env",
    kwargs={
        "original_simulator": Simulator(symbols_filename=MIXED_DATA_PATH, hedge=False),
        "trading_symbols": ["EURUSD", "USDCAD", "GOOG", "AAPL", "BTCUSD", "ETHUSD"],
        "window_size": 10,
        "fee": lambda symbol: {
            "EURUSD": 0.0002,
            "USDCAD": 0.0005,
            "GOOG": 0.15,
            "AAPL": 0.01,
            "BTCUSD": 50.0,
            "ETHUSD": 3.0,
        }[symbol],
    },
)
