# pylint: disable=E0203
#  This file was adapted from OctoBot (https://github.com/Drakkar-Software/OctoBot)
import async_channel.constants as channel_constants
import async_channel.channels as channels
import async_channel.consumer as consumers
import async_channel.producer as producers

from tradeflow.commons.logger import Logger


class TradeFlowChannelConsumer(consumers.Consumer):
    """
    Consumer adapted for TradeFlowChannel
    """


class TradeFlowChannelProducer(producers.Producer):
    """
    Producer adapted for TradeFlowChannel
    """

    async def run(self) -> None:
        """
        Register the producer and call producer.start()
        """
        await self.channel.register_producer(self)
        await self.start()

    async def send(self, bot_id, subject, action, data=None):
        for consumer in self.channel.get_filtered_consumers(
            bot_id=bot_id, subject=subject, action=action
        ):
            await consumer.queue.put(
                {"bot_id": bot_id, "subject": subject, "action": action, "data": data}
            )


class TradeFlowChannel(channels.Channel):
    """
    Channel used to communicate high level events
    """

    PRODUCER_CLASS = TradeFlowChannelProducer
    CONSUMER_CLASS = TradeFlowChannelConsumer
    DEFAULT_PRIORITY_LEVEL = 1

    BOT_ID_KEY = "bot_id"
    SUBJECT_KEY = "subject"
    ACTION_KEY = "action"

    def __init__(self, bot_id):
        super().__init__()
        self.chan_id = bot_id
        self.is_synchronized = True
        self.logger = Logger(name=self.__class__.__name__)

    async def new_consumer(
        self,
        callback: object = None,
        size: int = 0,
        priority_level: int = DEFAULT_PRIORITY_LEVEL,
        bot_id: object = channel_constants.CHANNEL_WILDCARD,
        subject: object = channel_constants.CHANNEL_WILDCARD,
        action: object = channel_constants.CHANNEL_WILDCARD,
    ) -> TradeFlowChannelConsumer:
        """
        Creates a new Channel consumer
        :param callback: the consumer callback
        :param size: the consumer queue size
        :param priority_level: the consumer priority level
        :param bot_id: the consumer bot id filtering
        :param subject: the consumer subject filtering
        :param action: the consumer action filtering
        :return: the consumer instance created
        """
        consumer = TradeFlowChannelConsumer(
            callback, size=size, priority_level=priority_level
        )
        await self._add_new_consumer_and_run(
            consumer, bot_id=bot_id, subject=subject, action=action
        )
        self.logger.debug(
            f"Consumer started for subject: {subject} action: {action} [{consumer}]"
        )
        return consumer

    def get_filtered_consumers(
        self,
        bot_id: str,
        subject: str = channel_constants.CHANNEL_WILDCARD,
        action: str = channel_constants.CHANNEL_WILDCARD,
    ):
        """
        Returns the consumer that matches criteria
        :param subject: the subject criteria
        :param bot_id: the bot id criteria
        :param action: the action criteria
        :return: the matched consumers list
        """
        return self.get_consumer_from_filters(
            {
                self.BOT_ID_KEY: bot_id,
                self.SUBJECT_KEY: subject,
                self.ACTION_KEY: action,
            }
        )

    async def _add_new_consumer_and_run(
        self,
        consumer,
        bot_id: object = channel_constants.CHANNEL_WILDCARD,
        subject: object = channel_constants.CHANNEL_WILDCARD,
        action: object = channel_constants.CHANNEL_WILDCARD,
    ):
        """
        Add and run a created channel consumer
        :param consumer: the consumer instance to run
        :param bot_id: the bot id filter
        :param subject: the consumer subject filters
        :param action: the consumer action filters
        """
        consumer_filters: dict = {
            self.BOT_ID_KEY: bot_id,
            self.SUBJECT_KEY: subject,
            self.ACTION_KEY: action,
        }

        self.add_new_consumer(consumer, consumer_filters)
        await consumer.run()
