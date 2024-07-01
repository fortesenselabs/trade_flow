import enum
import async_channel.channels as channels
import tradeflow.commons.channels_name as channels_name
import tradeflow.commons.logging as logging
import tradeflow.commons.enums as enums

import tradeflow.services.api as api
import tradeflow.services.managers as managers

TRADEFLOW_CHANNEL_SERVICE_CONSUMER_LOGGER_TAG = "TradeFlowChannelServiceConsumer"


class TradeFlowChannelServiceActions(enum.Enum):
    """
    TradeFlow Channel consumer supported actions
    """

    INTERFACE = "interface"
    NOTIFICATION = "notification"
    SERVICE_FEED = "service_feed"
    START_SERVICE_FEED = "start_service_feed"
    EXCHANGE_REGISTRATION = "exchange_registration"


class TradeFlowChannelServiceDataKeys(enum.Enum):
    """
    TradeFlow Channel consumer supported data keys
    """

    EXCHANGE_ID = "exchange_id"
    BOT_ID = "bot_id"
    EDITED_CONFIG = "edited_config"
    BACKTESTING_ENABLED = "backtesting_enabled"
    INSTANCE = "instance"
    SUCCESSFUL_OPERATION = "successful_operation"
    CLASS = "class"
    FACTORY = "factory"
    EXECUTORS = "executors"


async def tradeflow_channel_callback(bot_id, subject, action, data) -> None:
    """
    TradeFlow channel consumer callback
    :param bot_id: the callback bot id
    :param subject: the callback subject
    :param action: the callback action
    :param data: the callback data
    """
    if subject == enums.TradeFlowChannelSubjects.CREATION.value:
        await _handle_creation(bot_id, action, data)
    elif subject == enums.TradeFlowChannelSubjects.UPDATE.value:
        if action == TradeFlowChannelServiceActions.EXCHANGE_REGISTRATION.value:
            await _handle_exchange_notification(data)
        elif action == TradeFlowChannelServiceActions.START_SERVICE_FEED.value:
            await _handle_service_feed_start_notification(bot_id, action, data)


async def _handle_creation(bot_id, action, data):
    created_instance = None
    edited_config = data[TradeFlowChannelServiceDataKeys.EDITED_CONFIG.value]
    backtesting_enabled = data[
        TradeFlowChannelServiceDataKeys.BACKTESTING_ENABLED.value
    ]
    to_create_class = data[TradeFlowChannelServiceDataKeys.CLASS.value]
    factory = data[TradeFlowChannelServiceDataKeys.FACTORY.value]
    if action == TradeFlowChannelServiceActions.INTERFACE.value:
        created_instance = await _create_and_start_interface(
            factory, to_create_class, edited_config, backtesting_enabled
        )
    if action == TradeFlowChannelServiceActions.NOTIFICATION.value:
        executors = data[TradeFlowChannelServiceDataKeys.EXECUTORS.value]
        created_instance = await _create_notifier(
            factory, to_create_class, edited_config, backtesting_enabled, executors
        )
    if action == TradeFlowChannelServiceActions.SERVICE_FEED.value:
        created_instance = await _create_service_feed(factory, to_create_class)
    await channels.get_chan_at_id(
        channels_name.TradeFlowChannelsName.TRADEFLOW_CHANNEL.value, bot_id
    ).get_internal_producer().send(
        bot_id=bot_id,
        subject=enums.TradeFlowChannelSubjects.NOTIFICATION.value,
        action=action,
        data={TradeFlowChannelServiceDataKeys.INSTANCE.value: created_instance},
    )


async def _create_and_start_interface(
    interface_factory, to_create_class, edited_config, backtesting_enabled
):
    interface_instance = await interface_factory.create_interface(to_create_class)
    await interface_instance.initialize(backtesting_enabled, edited_config)
    return (
        interface_instance
        if await managers.start_interface(interface_instance)
        else None
    )


async def _create_notifier(
    factory, to_create_class, edited_config, backtesting_enabled, executors
):
    notifier_instance = await factory.create_notifier(to_create_class)
    notifier_instance.executors = executors
    await notifier_instance.initialize(backtesting_enabled, edited_config)
    return notifier_instance


async def _create_service_feed(factory, to_create_class):
    return factory.create_service_feed(to_create_class)


async def _handle_exchange_notification(data):
    notifier_or_interface = data[TradeFlowChannelServiceDataKeys.INSTANCE.value]
    exchange_id = data[TradeFlowChannelServiceDataKeys.EXCHANGE_ID.value]
    await notifier_or_interface.register_new_exchange(exchange_id)


async def _handle_service_feed_start_notification(bot_id, action, data):
    service_feed = data[TradeFlowChannelServiceDataKeys.INSTANCE.value]
    edited_config = data[TradeFlowChannelServiceDataKeys.EDITED_CONFIG.value]
    await channels.get_chan_at_id(
        channels_name.TradeFlowChannelsName.TRADEFLOW_CHANNEL.value, bot_id
    ).get_internal_producer().send(
        bot_id=bot_id,
        subject=enums.TradeFlowChannelSubjects.NOTIFICATION.value,
        action=action,
        data={
            TradeFlowChannelServiceDataKeys.SUCCESSFUL_OPERATION.value: await _start_service_feed(
                service_feed, edited_config
            )
        },
    )


async def _start_service_feed(service_feed, edited_config):
    if not await api.start_service_feed(service_feed, False, edited_config):
        logger = logging.Logger(name=TRADEFLOW_CHANNEL_SERVICE_CONSUMER_LOGGER_TAG)
        # log error when the issue is not related to configuration
        if service_feed.has_required_services_configuration():
            logger.error(
                f"Failed to start {service_feed.get_name()}. Evaluators requiring this service feed "
                f"might not work properly."
            )
        else:
            logger.debug(
                f"Impossible to start {service_feed.get_name()}: missing service(s) configuration."
            )
        return False
    return True
