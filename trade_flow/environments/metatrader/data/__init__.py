import os

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

FOREX_DATA_PATH = os.path.join(DATA_DIR, "forex_symbols.joblib")
STOCKS_DATA_PATH = os.path.join(DATA_DIR, "stocks_symbols.joblib")
CRYPTO_DATA_PATH = os.path.join(DATA_DIR, "crypto_symbols.joblib")
MIXED_DATA_PATH = os.path.join(DATA_DIR, "mixed_symbols.joblib")
