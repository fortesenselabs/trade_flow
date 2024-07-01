import tradeflow.trading.exchange_channel as exchange_channel
import tradeflow.trading.exchange_data as exchange_data
import tradeflow.trading.personal_data as personal_data


async def subscribe_to_ohlcv_channel(callback, exchange_id):
    await _subscribe_to_channel(callback, exchange_id, exchange_data.OHLCVChannel)


async def subscribe_to_trades_channel(callback, exchange_id):
    await _subscribe_to_channel(callback, exchange_id, personal_data.TradesChannel)


async def subscribe_to_order_channel(callback, exchange_id):
    await _subscribe_to_channel(callback, exchange_id, personal_data.OrdersChannel)


async def _subscribe_to_channel(callback, exchange_id, channel):
    channel = exchange_channel.get_chan(channel.get_name(), exchange_id)
    await channel.new_consumer(callback)
