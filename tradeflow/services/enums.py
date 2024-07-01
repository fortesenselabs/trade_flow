import enum


class NotificationLevel(enum.Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"


class NotificationCategory(enum.Enum):
    GLOBAL_INFO = "global-info"
    PRICE_ALERTS = "price-alerts"
    TRADES = "trades"
    TRADING_SCRIPT_ALERTS = "trading-script-alerts"
    OTHER = "other"


class NotificationSound(enum.Enum):
    NO_SOUND = None
    FINISHED_PROCESSING = "finished_processing.mp3"
