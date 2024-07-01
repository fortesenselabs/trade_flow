from tradeflow.services.api import services
from tradeflow.services.api import interfaces
from tradeflow.services.api import service_feeds
from tradeflow.services.api import notification

from tradeflow.services.api.services import (
    get_available_services,
    get_service,
    create_service_factory,
    stop_services,
)
from tradeflow.services.api.interfaces import (
    initialize_global_project_data,
    create_interface_factory,
    is_enabled,
    is_enabled_in_backtesting,
    is_interface_relevant,
    disable_interfaces,
    send_user_command,
    start_interfaces,
    stop_interfaces,
)
from tradeflow.services.api.service_feeds import (
    create_service_feed_factory,
    get_service_feed,
    start_service_feed,
    stop_service_feed,
    clear_bot_id_feeds,
)
from tradeflow.services.api.notification import (
    create_notifier_factory,
    create_notification,
    is_enabled_in_config,
    get_enable_notifier,
    set_enable_notifier,
    is_notifier_relevant,
    send_notification,
    process_pending_notifications,
)


LOGGER_TAG = "ServicesApi"

__all__ = [
    "get_available_services",
    "get_service",
    "create_service_factory",
    "stop_services",
    "initialize_global_project_data",
    "create_interface_factory",
    "is_enabled",
    "is_enabled_in_backtesting",
    "is_interface_relevant",
    "disable_interfaces",
    "send_user_command",
    "start_interfaces",
    "stop_interfaces",
    "create_service_feed_factory",
    "get_service_feed",
    "start_service_feed",
    "stop_service_feed",
    "clear_bot_id_feeds",
    "create_notifier_factory",
    "create_notification",
    "is_enabled_in_config",
    "get_enable_notifier",
    "set_enable_notifier",
    "is_notifier_relevant",
    "send_notification",
    "process_pending_notifications",
]
