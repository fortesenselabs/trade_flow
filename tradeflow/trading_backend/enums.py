#  This file was adapted from trading-backend (https://github.com/Drakkar-Software/trading-backend)
import enum


class APIKeyRights(enum.Enum):
    READING = "reading"
    SPOT_TRADING = "spot trading"
    MARGIN_TRADING = "margin trading"
    FUTURES_TRADING = "futures trading"
    CFD_TRADING = "cfd trading"
    HEDGING = "hedging"
    WITHDRAWALS = "withdrawals"
