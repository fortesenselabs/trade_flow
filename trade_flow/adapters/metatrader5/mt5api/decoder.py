from decimal import Decimal
from functools import partial
from typing import Any, Callable, Coroutine, Tuple

from trade_flow.adapters.metatrader5.mt5api.common import MarketDataTypeEnum
from trade_flow.adapters.metatrader5.mt5api.symbol import SymbolInfo


class Handler:
    """
    Handler is a base class for handling specific events triggered by messages from the MetaTrader 5 client.

    """

    def submit_to_msg_handler_queue(self, task: Callable[..., Any]) -> None:
        """
        Submit a task to the message handler's queue for processing.

        This method places a callable task into the message handler task queue,
        ensuring it's scheduled for asynchronous execution according to the queue's
        order. The operation is non-blocking and immediately returns after queueing the task.

        Parameters
        ----------
        task : Callable[..., Any]
            The task to be queued. This task should be a callable that matches
            the expected signature for tasks processed by the message handler.

        """
        raise NotImplementedError()

    async def on_connect(self, terminal_info: Any):
        """
        Handles the event when a connection is established with the MetaTrader 5 terminal.

        Args:
            terminal_info (Any): Information about the terminal, such as configuration and status.
        """
        print(terminal_info)

    async def process_market_data_type(
        self, *, req_id: int, market_data_type: MarketDataTypeEnum
    ) -> None:
        """
        Return the market data type (real-time, frozen, delayed)
        of ticker sent by MT5Client::req_market_data_type when Terminal switches from real-time
        to frozen and back and to delayed and back too.
        """
        if market_data_type == MarketDataTypeEnum.REALTIME:
            print(f"Market DataType is {MarketDataTypeEnum.to_str(market_data_type)}")
        else:
            print(f"Market DataType is {MarketDataTypeEnum.to_str(market_data_type)}")

    async def process_next_valid_id(self, *, order_id: int):
        """
        Receive the next valid order id.

        Will be invoked automatically upon successful API client connection,
        or after call to MT5Client::req_ids
        Important: the next valid order ID is only valid at the time it is received.

        """
        raise NotImplementedError()

    async def process_managed_accounts(self, *, accounts: Tuple[str]) -> None:
        """
        Receive a tuple with the managed account ids.

        Occurs automatically on initial API client connection.

        """
        raise NotImplementedError()

    async def process_symbol_details(
        self,
        *,
        req_id: int,
        symbol_info: SymbolInfo,
    ) -> None:
        """
        Receive the full symbol's info This method will return all
        symbols matching the requested via MT5Client::req_symbol_details.
        """
        raise NotImplementedError()

    async def process_symbol_details_end(self, *, req_id: int) -> None:
        """
        After all symbols matching the request were returned, this method will mark
        the end of their reception.
        """
        raise NotImplementedError()

    async def process_tick_by_tick_bid_ask(
        self,
        *,
        req_id: int,
        time: int,
        bid_price: float,
        ask_price: float,
        bid_size: Decimal,
        ask_size: Decimal,
    ):
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
        raise NotImplementedError()

    async def process_realtime_bar(
        self,
        *,
        req_id: int,
        time: int,
        open_: float,
        high: float,
        low: float,
        close: float,
        volume: Decimal,
        spread=int,
        wap: Decimal,
        count: int,
    ) -> None:
        """
        Update real-time 1 minute bars.
        """
        raise NotImplementedError()


class Decoder:
    """
    Decoder is responsible for decoding incoming messages from the MetaTrader 5 client and invoking
    the appropriate methods on the provided Handler instance.

    Attributes:
        handler (Handler): The handler instance that handles decoded messages.

    Methods:
        decode(msg: tuple):
            Decodes incoming messages and routes them to the appropriate method on the client.
    """

    def __init__(self, handler: Handler):
        """
        Initializes the Decoder with a Handler instance.

        Args:
            handler (Handler): The handler instance that will handle the decoded messages.
        """
        self.handler = handler

    def create_task(self, func: Coroutine, **kwargs):
        task = partial(func, **kwargs)
        return task

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

        # TODO: Standardize empty responses
        if response is None or len(response) == 0:
            print("No data available, incoming packets are needed.")
            return

        match fn_name.lower():
            case "connect":
                task = self.create_task(self.handler.on_connect, response)
            case "managed_accounts":
                task = self.create_task(self.handler.process_managed_accounts, accounts=response)
            case "req_ids":
                order_id = response[0]
                task = self.create_task(self.handler.process_next_valid_id, order_id=order_id)
            case "req_market_data_type":
                task = self.create_task(
                    self.handler.process_market_data_type,
                    req_id=req_id,
                    market_data_type=MarketDataTypeEnum(response),
                )
            case "req_symbol_details" | "req_matching_symbols":  # |
                task = self.create_task(
                    self.handler.process_symbol_details, req_id=req_id, symbol_infos=response
                )
            case "req_tick_by_tick_data":
                task = self.create_task(
                    self.handler.process_tick_by_tick_bid_ask,
                    req_id=req_id,
                    time=response.time_msc,
                    bid_price=response.bid,
                    ask_price=response.ask,
                    bid_size=Decimal(response.volume_real),
                    ask_size=Decimal(response.volume_real),
                )
            case "req_real_time_bars":
                bar = response[0]
                task = self.create_task(
                    self.handler.process_realtime_bar,
                    req_id=req_id,
                    time=bar.time,
                    open_=bar.open_,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=Decimal(bar.tick_volume),
                    spread=bar.spread,
                    wap=0,
                    count=bar[7],
                )

        self.handler.submit_to_msg_handler_queue(task)


#
#
#
# bar =>  [(1724530740, 8145., 8145.1, 8144.4, 8144.5, 30, 2, 0)]
#
#
# print(f"Msg received: fn_name => {fn_name}")
#
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
