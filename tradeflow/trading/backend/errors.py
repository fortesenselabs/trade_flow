#  This file was adapted from trading-backend (https://github.com/Drakkar-Software/trading-backend)
class TimeSyncError(RuntimeError):
    pass


class ExchangeAuthError(RuntimeError):
    pass


class APIKeyPermissionsError(RuntimeError):
    pass
