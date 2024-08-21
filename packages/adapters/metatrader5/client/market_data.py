import functools
from collections.abc import Callable
from decimal import Decimal
from inspect import iscoroutinefunction
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import pytz
from metatrader5.mt5api.common import MarketDataTypeEnum 
# from ibapi.common import BarData
# from ibapi.common import HistoricalTickLast
# from ibapi.common import MarketDataTypeEnum
# from ibapi.common import TickAttribBidAsk
# from ibapi.common import TickAttribLast

from nautilus_trader.core.data import Data
from nautilus_trader.model.data import Bar
from nautilus_trader.model.data import BarType
from nautilus_trader.model.data import QuoteTick
from nautilus_trader.model.data import TradeTick
from nautilus_trader.model.enums import AggressorSide
from nautilus_trader.model.identifiers import InstrumentId


from metatrader5.common import MT5Symbol
from metatrader5.client.common import BaseMixin, Subscription
from metatrader5.parsing.data import bar_spec_to_bar_size
from metatrader5.parsing.data import generate_trade_id
from metatrader5.parsing.data import timedelta_to_duration_str
from metatrader5.parsing.data import what_to_show
from metatrader5.parsing.instruments import mt5_symbol_to_instrument_id


class MetaTrader5ClientMarketDataMixin(BaseMixin):
    """
    Handles market data requests, subscriptions and data processing for the
    MetaTrader5Client.

    This class handles real-time and historical market data subscription management,
    including subscribing and unsubscribing to ticks, bars, and other market data types.
    It processes and formats the received data to be compatible with the Nautilus
    Trader.

    """

    async def set_market_data_type(self, market_data_type: MarketDataTypeEnum) -> None:
        """
        Set the market data type for data subscriptions. This method configures the type
        of market data (live, delayed, etc.) to be used for subsequent data requests.

        Parameters
        ----------
        market_data_type : MarketDataTypeEnum
            The market data type to be set

        """
        self._log.info(f"Setting Market DataType to {MarketDataTypeEnum.to_str(market_data_type)}")
        self._mt5Client.req_market_data_type(market_data_type)


    async def _subscribe(
        self,
        name: str | tuple,
        subscription_method: Callable | functools.partial,
        cancellation_method: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Subscription | None:
        """
        Manage the subscription and un-subscription process for market data. This
        internal method is responsible for handling the logic to subscribe or
        unsubscribe to different market data types (ticks, bars, etc.). It uses the
        provided subscription and cancellation methods to control the data flow.

        Parameters
        ----------
        name : Any
            A unique identifier for the subscription.
        subscription_method : Callable
            The method to call for subscribing to market data.
        cancellation_method : Callable
            The method to call for unsubscribing from market data.
        *args
            Variable length argument list for the subscription method.
        **kwargs
            Arbitrary keyword arguments for the subscription method.

        Returns
        -------
        Subscription | ``None``

        """
        if not (subscription := self._subscriptions.get(name=name)):
            req_id = self._next_req_id()
            if subscription_method == self.subscribe_historical_bars:
                handle_func = functools.partial(
                    subscription_method,
                    *args,
                    **kwargs,
                )
            else:
                handle_func = functools.partial(subscription_method, req_id, *args, **kwargs)
            subscription = self._subscriptions.add(
                req_id=req_id,
                name=name,
                handle=handle_func,
                cancel=functools.partial(cancellation_method, req_id),
            )
            if not subscription:
                return None
            if iscoroutinefunction(subscription.handle):
                await subscription.handle()
            else:
                subscription.handle()

            return subscription
        else:
            self._log.info(f"Subscription already exists for {subscription}")
            return None

    async def _unsubscribe(
        self,
        name: str | tuple,
        cancellation_method: Callable,
    ) -> None:
        """
        Manage the un-subscription process for market data. This internal method is
        responsible for handling the logic to unsubscribe to different market data types
        (ticks, bars, etc.). It uses the provided cancellation method to control the
        data flow.

        Parameters
        ----------
        cancellation_method : Callable
            The method to call for unsubscribing from market data.
        name : Any
            A unique identifier for the subscription.

        """
        if subscription := self._subscriptions.get(name=name):
            self._subscriptions.remove(subscription.req_id)
            cancellation_method(reqId=subscription.req_id)
            self._log.debug(f"Unsubscribed from {subscription}")
        else:
            self._log.debug(f"Subscription doesn't exist for {name}")

    async def subscribe_ticks(
        self,
        instrument_id: InstrumentId,
        symbol: MT5Symbol,
        tick_type: str,
        ignore_size: bool,
    ) -> None:
        """
        Subscribe to tick data for a specified instrument.

        Parameters
        ----------
        instrument_id : InstrumentId
            The identifier of the instrument for which to subscribe.
        symbol : MT5Symbol
            The symbol details for the instrument.
        tick_type : str
            The type of tick data to subscribe to.
        ignore_size : bool
            Omit updates that reflect only changes in size, and not price.
            Applicable to Bid_Ask data requests.

        """ 

        name = (str(instrument_id), tick_type)
        await self._subscribe(
            name,
            self._mt5Client.req_tick_by_tick_data,
            self._mt5Client.cancel_tick_by_tick_data,
            symbol,
            tick_type,
            0,
            ignore_size,
        )

    async def unsubscribe_ticks(self, instrument_id: InstrumentId, tick_type: str) -> None:
        """
        Unsubscribes from tick data for a specified instrument.

        Parameters
        ----------
        instrument_id : InstrumentId
            The identifier of the instrument for which to unsubscribe.
        tick_type : str
            The type of tick data to unsubscribe from.

        """
        name = (str(instrument_id), tick_type)
        await self._unsubscribe(name, self._mt5Client._cancel_tick_by_tick_data)


    async def subscribe_historical_bars(
        self,
        bar_type: BarType,
        symbol: MT5Symbol,
        use_rth: bool,
        handle_revised_bars: bool,
    ) -> None:
        """
        Subscribe to historical bar data for a specified bar type and contract. It
        allows configuration for regular trading hours and handling of revised bars.

        Parameters
        ----------
        bar_type : BarType
            The type of bar to subscribe to.
        symbol : MT5Symbol
            The Interactive Brokers contract details for the instrument.
        use_rth : bool
            Whether to use regular trading hours (RTH) only.
        handle_revised_bars : bool
            Whether to handle revised bars or not.

        """
        name = str(bar_type)
        subscription = await self._subscribe(
            name,
            self.subscribe_historical_bars,
            self._mt5Client.cancel_historical_data,
            bar_type=bar_type,
            symbol=symbol,
            use_rth=use_rth,
            handle_revised_bars=handle_revised_bars,
        )
        if not subscription:
            return

        # Check and download the gaps or approx 300 bars whichever is less
        last_bar: Bar = self._cache.bar(bar_type)
        if last_bar is None:
            duration = pd.Timedelta(bar_type.spec.timedelta.total_seconds() * 300, "sec")
        else:
            duration = pd.Timedelta(self._clock.timestamp_ns() - last_bar.ts_event, "ns")
        bar_size_setting: str = bar_spec_to_bar_size(bar_type.spec)

        self._mt5Client.req_historical_data(
            req_id=subscription.req_id,
            symbol=symbol,
            endDateTime="",
            durationStr=timedelta_to_duration_str(duration),
            barSizeSetting=bar_size_setting,
            whatToShow=what_to_show(bar_type),
            useRTH=use_rth,
            formatDate=2,
            keepUpToDate=True,
            chartOptions=[],
        )

    async def unsubscribe_historical_bars(self, bar_type: BarType) -> None:
        """
        Unsubscribe from historical bar data for a specified bar type.

        Parameters
        ----------
        bar_type : BarType
            The type of bar to unsubscribe from.

        """
        name = str(bar_type)
        await self._unsubscribe(name, self._mt5Client.cancel_historical_data)

    # 
    # Send data to message bus
    # 
    async def _handle_data(self, data: Data) -> None:
        """
        Handle and forward processed data to the appropriate destination. This method is
        a generic data handler that forwards processed market data, such as bars or
        ticks, to the DataEngine.process message bus endpoint.

        Parameters
        ----------
        data : Data
            The processed market data ready to be forwarded.

        """
        self._msgbus.send(endpoint="DataEngine.process", msg=data)


    # 
    # misc. 
    # 
    async def _convert_mt5_timestamp_to_pandas_timestamp(self, timestamp: float) -> pd.Timestamp:
        """
        Converts a MetaTrader 5 timestamp (in milliseconds since the Unix epoch) to a Pandas Timestamp object.

        Args:
            timestamp (float): The MetaTrader 5 timestamp in milliseconds.

        Returns:
            pd.Timestamp: The converted Pandas Timestamp object.
        """

        try:
            # Attempt to convert directly to a Pandas Timestamp
            ts = pd.Timestamp.fromtimestamp(timestamp / 1000, tz=pytz.utc)
        except ValueError:
            # If the conversion fails, try handling potential date format issues
            try:
                # Handle YYYYMMDD format (if applicable)
                timestamp_str = str(int(timestamp))
                ts = pd.to_datetime(timestamp_str, format='%Y%m%d', tz=pytz.utc)
            except ValueError:
                # If both conversions fail, raise a custom exception or handle the error appropriately
                raise ValueError(f"Invalid timestamp: {timestamp}")

        return ts.value
    
    # 
    # 
    # Data Processors
    # 
    async def process_tick_by_tick_bid_ask(
        self,
        *,
        req_id: int,
        time: int,
        bid_price: float,
        ask_price: float,
        bid_size: Decimal,
        ask_size: Decimal,
        # tick_attrib_bid_ask: TickAttribBidAsk,
    ) -> None:
        """
        Return "BidAsk" tick-by-tick real-time tick data.
        """
        if not (subscription := self._subscriptions.get(req_id=req_id)):
            return

        instrument_id = InstrumentId.from_str(subscription.name[0])
        instrument = self._cache.instrument(instrument_id)
        ts_event = await self._convert_mt5_timestamp_to_pandas_timestamp(time)

        quote_tick = QuoteTick(
            instrument_id=instrument_id,
            bid_price=instrument.make_price(bid_price),
            ask_price=instrument.make_price(ask_price),
            bid_size=instrument.make_qty(bid_size),
            ask_size=instrument.make_qty(ask_size),
            ts_event=ts_event,
            ts_init=max(self._clock.timestamp_ns(), ts_event),  # `ts_event` <= `ts_init`
        )

        await self._handle_data(quote_tick)