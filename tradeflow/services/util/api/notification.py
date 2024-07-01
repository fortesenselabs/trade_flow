import async_channel.channels as channel

import tradeflow.commons.enums as common_enums

import tradeflow.services.channel as channels
import tradeflow.services.notification as notifications
import tradeflow.services.notifier as notifiers
import tradeflow.services.enums as enums

MAX_PENDING_NOTIFICATION = 10
pending_notifications = []


def create_notifier_factory(config) -> notifiers.NotifierFactory:
    return notifiers.NotifierFactory(config)


def create_notification(
    text: str,
    title="",
    markdown_text="",
    sound=enums.NotificationSound.NO_SOUND,
    markdown_format: common_enums.MarkdownFormat = common_enums.MarkdownFormat.IGNORE,
    level: enums.NotificationLevel = enums.NotificationLevel.INFO,
    category: enums.NotificationCategory = enums.NotificationCategory.GLOBAL_INFO,
    linked_notification=None,
) -> notifications.Notification:
    return notifications.Notification(
        text,
        title,
        markdown_text,
        sound,
        markdown_format,
        level,
        category,
        linked_notification,
    )


async def send_notification(notification: notifications.Notification) -> None:
    try:
        # send notification only if is a notification channel is running
        channel.get_chan(channels.NotificationChannel.get_name())
        await channels.NotificationChannelProducer.instance().send(
            {"notification": notification}
        )
    except KeyError:
        if len(pending_notifications) < MAX_PENDING_NOTIFICATION:
            pending_notifications.append(notification)


async def process_pending_notifications():
    for notification in pending_notifications:
        await channels.NotificationChannelProducer.instance().send(
            {"notification": notification}
        )
    pending_notifications.clear()


def is_enabled_in_config(notifier_class, config) -> bool:
    return notifier_class.is_enabled(config)


def get_enable_notifier(notifier) -> bool:
    return notifier.enabled


def set_enable_notifier(notifier, enabled) -> None:
    notifier.enabled = enabled


def is_notifier_relevant(config, notifier_class, backtesting_enabled):
    return (
        is_enabled_in_config(notifier_class, config)
        and all(
            service.get_is_enabled(config)
            for service in notifier_class.REQUIRED_SERVICES
        )
        and not backtesting_enabled
    )
