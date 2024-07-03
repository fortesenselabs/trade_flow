#  This file was adapted from trading-backend (https://github.com/Drakkar-Software/trading-backend)
import os

ALLOW_WITHDRAWAL_KEYS = os.getenv("ALLOW_WITHDRAWAL_KEYS", "True").lower() != "false"
