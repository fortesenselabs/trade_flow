from decimal import Decimal
from typing import Any


class DClient:
    """
    DClient is a base class for handling specific events triggered by messages from the MetaTrader 5 client.

    """

    async def on_connect(self, terminal_info: Any):
        """
        Handles the event when a connection is established with the MetaTrader 5 terminal.

        Args:
            terminal_info (Any): Information about the terminal, such as configuration and status.
        """
        pass

    async def process_tick_by_tick_bid_ask(self, 
                                           *,         
                                           req_id: int,
                                           time: int,
                                           bid_price: float,
                                           ask_price: float,
                                           bid_size: Decimal,
                                           ask_size: Decimal):
        """
        Processes tick-by-tick bid and ask data received from the MetaTrader 5 client.

        Args:
            req_id (int): The request ID associated with the tick-by-tick data.
            time (int): The timestamp of the tick data in milliseconds.
            bid_price (float): The bid price.
            ask_price (float): The ask price.
            bid_size (Decimal): The size of the bid.
            ask_size (Decimal): The size of the ask.
        """
        pass


class Decoder:
    """
    Decoder is responsible for decoding incoming messages from the MetaTrader 5 client and invoking
    the appropriate methods on the provided DClient instance.

    Attributes:
        client (DClient): The client instance that handles decoded messages.
    
    Methods:
        decode(msg: tuple):
            Decodes incoming messages and routes them to the appropriate method on the client.
    """

    def __init__(self, client: DClient):
        """
        Initializes the Decoder with a DClient instance.

        Args:
            client (DClient): The client instance that will handle the decoded messages.
        """
        self.client = client

    async def decode(self, msg: tuple):
        """
        Decodes incoming messages from the MetaTrader 5 client and routes them to the appropriate
        method on the DClient instance.

        Args:
            msg (tuple): The message received from the MetaTrader 5 client. The structure of this
                         tuple is expected to include a request ID, a function name, and a response object.
        """
        req_id = msg[0]
        fn_name = str(msg[1])
        response = msg[-1]

        if response is None or len(response) == 0:
            print("No data available, incoming packets are needed.")
            return

        if len(fn_name) > 0:
            match fn_name.lower():
                case "connect":
                    await self.client.on_connect(response)
                case "req_tick_by_tick_data":
                    await self.client.process_tick_by_tick_bid_ask(
                        req_id=req_id, 
                        time=response.time_msc,
                        bid_price=response.bid,
                        ask_price=response.ask,
                        bid_size=Decimal(response.volume_real),
                        ask_size=Decimal(response.volume_real)
                    )


# print(f"Msg received: fn_name => {fn_name}")

# The decoder identifies the message type based on its payload (e.g., open
# order, process real-time ticks, etc.) and then calls the corresponding
# method from the EWrapper. Many of those methods are overridden in the client
# manager and handler classes to support custom processing required for Nautilus.
# await asyncio.to_thread(self._eclient.decoder.interpret, fields)

# Solution(what is been done at the core of eclient.decoder.interpret):
# 
# Call the assigned or recommended methods in the wrapper 
# method = getattr(self.wrapper, handleInfo.wrapperMeth.__name__)
# logger.debug("calling %s with %s %s", method, self.wrapper, args)
# method(*args)
# 
# if not isinstance(msg, tuple):
#     return False


# if fn_name != 'connect':
#     request = self._requests.get(req_id=req_id)
#     print("self._requests => ", request)
#     if request is None:
#         return False
            
#     request.future.set_result(response)
# Tick(time=1723912321, bid=8113.4, ask=8113.6, last=0.0, volume=0, time_msc=1723912321103, flags=6, volume_real=0.0)

