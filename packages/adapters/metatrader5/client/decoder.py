from decimal import Decimal

class Decoder:
    def __init__(self, _client):
        self._client = _client

    async def decode(self, msg: tuple):
        """
        Decodes incoming messages from the MetaTrader 5 client.

        Args:
            msg (tuple): The message received from the MetaTrader 5 client.

        """

        # print(f"Msg received: {msg}")

        req_id = msg[0]
        fn_name = msg[1]
        response = msg[-1]

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

        # Handle different message types based on function name
        if fn_name == 'req_tick_by_tick_data':
            await self._client.process_tick_by_tick_bid_ask(req_id=req_id, 
                                                    time=response.time_msc,
                                                    bid_price=response.bid,
                                                    ask_price=response.ask,
                                                    bid_size=Decimal(response.volume_real),
                                                    ask_size=Decimal(response.volume_real))
        elif fn_name == 'connect':
            # Handle connection messages (if needed)
            pass
        else:
            pass
            # # Handle other message types (optional)
            # if req_id != 0:
            #     request = self._requests.get(req_id=req_id)
            #     if request is None:
            #         return False
            #     request.future.set_result(response)

 
