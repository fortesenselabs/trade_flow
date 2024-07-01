import asyncio
import async_channel.consumer as consumer
import async_channel.producer as producer
import async_channel.channels as channels
import async_channel.util as util

TEST_CHANNEL = "Awesome"


class AwesomeProducer(producer.Producer):
    pass


class AwesomeConsumer(consumer.Consumer):
    pass


class AwesomeChannel(channels.Channel):
    PRODUCER_CLASS = AwesomeProducer
    CONSUMER_CLASS = AwesomeConsumer


async def callback(data):
    print("Consumer called!")
    print("Received: ", data)
    assert data == "test"
    await channels.get_chan(TEST_CHANNEL).stop()


async def main():
    channels.del_chan(TEST_CHANNEL)

    # Creates the channel
    await util.create_channel_instance(AwesomeChannel, channels.set_chan)

    # Add a new consumer to the channel
    await channels.get_chan(TEST_CHANNEL).new_consumer(callback)

    # Creates a producer that send data to the consumer through the channel
    producer = AwesomeProducer(channels.get_chan(TEST_CHANNEL))
    await producer.run()
    await producer.send({"data": "test"})

    # Stops the channel with all its producers and consumers
    # await channels.Channels.get_chan(TEST_CHANNEL).stop()


# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())


# https://www.octobot.cloud/en/guides/octobot-developers-environment/setup-your-environment
# https://www.octobot.cloud/en/guides/octobot-developers-environment/architecture#philosophy
