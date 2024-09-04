import functools
from collections.abc import Callable
from decimal import Decimal
from inspect import iscoroutinefunction
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import pytz
from metatrader5.mt5api.common import MarketDataTypeEnum 
from metatrader5.mt5api.common import BarData

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
            cancellation_method(req_id=subscription.req_id)
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
        await self._unsubscribe(name, self._mt5Client.cancel_tick_by_tick_data)

    async def subscribe_realtime_bars(
        self,
        bar_type: BarType,
        symbol: MT5Symbol,
        use_rth: bool,
    ) -> None:
        """
        Subscribe to real-time bar data for a specified bar type.

        Parameters
        ----------
        bar_type : BarType
            The type of bar to subscribe to.
        symbol : MT5Symbol
            The MetaTrader 5 symbol details for the instrument.
        use_rth : bool
            Whether to use regular trading hours (RTH) only.

        """
        name = str(bar_type)
        await self._subscribe(
            name,
            self._mt5Client.req_real_time_bars,
            self._mt5Client.cancel_real_time_bars,
            symbol,
            bar_type.spec.step,
            what_to_show(bar_type),
            use_rth,
        )

    async def unsubscribe_realtime_bars(self, bar_type: BarType) -> None:
        """
        Unsubscribes from real-time bar data for a specified bar type.

        Parameters
        ----------
        bar_type : BarType
            The type of bar to unsubscribe from.

        """
        name = str(bar_type)
        await self._unsubscribe(name, self._mt5Client.cancel_real_time_bars)


    async def subscribe_historical_bars(
        self,
        bar_type: BarType,
        symbol: MT5Symbol,
        use_rth: bool,
        handle_revised_bars: bool,
    ) -> None:
        """
        Subscribe to historical bar data for a specified bar type and symbol. It
        allows configuration for regular trading hours and handling of revised bars.

        Parameters
        ----------
        bar_type : BarType
            The type of bar to subscribe to.
        symbol : MT5Symbol
            The MetaTrader 5 symbol details for the instrument.
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

        # self._mt5Client.req_historical_data(
        #     req_id=subscription.req_id,
        #     symbol=symbol,
        #     end_datetime="",
        #     duration_str=timedelta_to_duration_str(duration),
        #     bar_size_setting=bar_size_setting,
        #     what_to_show=what_to_show(bar_type),
        #     use_rth=use_rth,
        #     format_date=2,
        #     keep_up_to_date=True,
        # )
        self._mt5Client.req_real_time_bars(
            req_id=subscription.req_id,
            symbol=symbol,
            bar_size="",
            what_to_show=what_to_show(bar_type),
            use_rth=use_rth
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

    async def get_historical_bars(
        self,
        bar_type: BarType,
        symbol: MT5Symbol,
        use_rth: bool,
        end_date_time: pd.Timestamp,
        duration: str,
        timeout: int = 60,
    ) -> list[Bar]:
        """
        Request and retrieve historical bar data for a specified bar type.

        Parameters
        ----------
        bar_type : BarType
            The type of bar for which historical data is requested.
        symbol : MT5Symbol
            The MetaTrader 5 symbol details for the instrument.
        use_rth : bool
            Whether to use regular trading hours (RTH) only for the data.
        end_date_time : str
            The end time for the historical data request, formatted "%Y%m%d-%H:%M:%S".
        duration : str
            The duration for which historical data is requested, formatted as a string.
        timeout : int, optional
            The maximum time in seconds to wait for the historical data response.

        Returns
        -------
        list[Bar]

        """
        # Ensure the requested `end_date_time` is in UTC and set formatDate=2 to ensure returned dates are in UTC.
        if end_date_time.tzinfo is None:
            end_date_time = end_date_time.replace(tzinfo=ZoneInfo("UTC"))
        else:
            end_date_time = end_date_time.astimezone(ZoneInfo("UTC"))

        name = (bar_type, end_date_time)
        if not (request := self._requests.get(name=name)):
            req_id = self._next_req_id()
            bar_size_setting = bar_spec_to_bar_size(bar_type.spec)
            request = self._requests.add(
                req_id=req_id,
                name=name,
                handle=functools.partial(
                    self._mt5Client.req_historical_data,
                    req_id=req_id,
                    symbol=symbol,
                    end_datetime=end_date_time.strftime("%Y%m%d %H:%M:%S %Z"),
                    duration_str=duration,
                    bar_size_setting=bar_size_setting,
                    what_to_show=what_to_show(bar_type),
                    use_rth=use_rth,
                    format_date=2,
                    keep_up_to_date=False,
                ),
                cancel=functools.partial(self._mt5Client.cancel_historical_data, req_id=req_id),
            )
            if not request:
                return []
            self._log.debug(f"req_historical_data: {request.req_id=}, {symbol=}")
            request.handle()
            return await self._await_request(request, timeout, default_value=[])
        else:
            self._log.info(f"Request already exist for {request}")
            return []
    
    async def get_historical_ticks(
        self,
        symbol: MT5Symbol,
        tick_type: str,
        start_date_time: pd.Timestamp | str = "",
        end_date_time: pd.Timestamp | str = "",
        use_rth: bool = True,
        timeout: int = 60,
    ) -> list[QuoteTick | TradeTick] | None:
        """
        Request and retrieve historical tick data for a specified symbol and tick
        type.

        Parameters
        ----------
        symbol : MT5Symbol
            The MetaTrader 5 symbol details for the instrument.
        tick_type : str
            The type of tick data to request (e.g., 'BID_ASK', 'TRADES').
        start_date_time : pd.Timestamp | str, optional
            The start time for the historical data request. Can be a pandas Timestamp
            or a string formatted as 'YYYYMMDD HH:MM:SS [TZ]'.
        end_date_time : pd.Timestamp | str, optional
            The end time for the historical data request. Same format as start_date_time.
        use_rth : bool, optional
            Whether to use regular trading hours (RTH) only for the data.
        timeout : int, optional
            The maximum time in seconds to wait for the historical data response.

        Returns
        -------
        list[QuoteTick | TradeTick] | ``None``

        """
        if isinstance(start_date_time, pd.Timestamp):
            start_date_time = start_date_time.strftime("%Y%m%d %H:%M:%S %Z")
        if isinstance(end_date_time, pd.Timestamp):
            end_date_time = end_date_time.strftime("%Y%m%d %H:%M:%S %Z")

        name = (str(mt5_symbol_to_instrument_id(symbol)), tick_type)
        if not (request := self._requests.get(name=name)):
            req_id = self._next_req_id()
            request = self._requests.add(
                req_id=req_id,
                name=name,
                handle=functools.partial(
                    self._mt5Client.req_historical_ticks,
                    req_id=req_id,
                    symbol=symbol,
                    start_date_time=start_date_time,
                    end_date_time=end_date_time,
                    number_of_ticks=1000,
                    what_to_show=tick_type,
                    use_rth=use_rth,
                    ignore_size=False,
                ),
                cancel=functools.partial(self._mt5Client.cancel_historical_data, req_id=req_id),
            )
            if not request:
                return None
            request.handle()
            return await self._await_request(request, timeout)
        else:
            self._log.info(f"Request already exist for {request}")
            return None

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
    
    async def _convert_mt5_bar_date_to_unix_nanos(self, bar: BarData, bar_type: BarType) -> int:
        """
        Convert the date from BarData to unix nanoseconds.

        If the bar type's aggregation is 14, the bar date is always returned in the
        YYYYMMDD format from IB. For all other aggregations, the bar date is returned
        in system time.

        Parameters
        ----------
        bar : BarData
            The bar data containing the date to be converted.
        bar_type : BarType
            The bar type that specifies the aggregation level.

        Returns
        -------
        int

        """
        if bar_type.spec.aggregation == 14:
            # Day bars are always returned with bar date in YYYYMMDD format
            ts = pd.to_datetime(bar.date, format="%Y%m%d", utc=True)
        else:
            ts = pd.Timestamp.fromtimestamp(int(bar.date), tz=pytz.utc)

        return ts.value

    async def _mt5_bar_to_ts_init(self, bar: BarData, bar_type: BarType) -> int:
        """
        Calculate the initialization timestamp for a bar.

        This method computes the timestamp at which a bar is initialized, by adjusting
        the provided bar's timestamp based on the bar type's duration. ts_init is set
        to the end of the bar period and not the start.

        Parameters
        ----------
        bar : BarData
            The bar data to be used for the calculation.
        bar_type : BarType
            The type of the bar, which includes information about the bar's duration.

        Returns
        -------
        int

        """
        ts = await self._convert_mt5_bar_date_to_unix_nanos(bar, bar_type)
        return ts + pd.Timedelta(bar_type.spec.timedelta).value

    async def _mt5_bar_to_nautilus_bar(
        self,
        bar_type: BarType,
        bar: BarData,
        ts_init: int,
        is_revision: bool = False,
    ) -> Bar:
        """
        Convert MetaTrader 5 bar data to Nautilus Trader's bar type.

        Parameters
        ----------
        bar_type : BarType
            The type of the bar.
        bar : BarData
            The bar data received from MetaTrader 5.
        ts_init : int
            The unix nanosecond timestamp representing the bar's initialization time.
        is_revision : bool, optional
            Indicates whether the bar is a revision of an existing bar. Defaults to False.

        Returns
        -------
        Bar

        """
        instrument = self._cache.instrument(bar_type.instrument_id)
        if not instrument:
            raise ValueError(f"No cached instrument for {bar_type.instrument_id}")

        ts_event = await self._convert_mt5_bar_date_to_unix_nanos(bar, bar_type)
        return Bar(
            bar_type=bar_type,
            open=instrument.make_price(bar.open),
            high=instrument.make_price(bar.high),
            low=instrument.make_price(bar.low),
            close=instrument.make_price(bar.close),
            volume=instrument.make_qty(0 if bar.volume == -1 else bar.volume),
            ts_event=ts_event,
            ts_init=ts_init,
            is_revision=is_revision,
        )
    
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
    # Data Processors
    # 
    async def _process_bar_data(
        self,
        bar_type_str: str,
        bar: BarData,
        handle_revised_bars: bool,
        historical: bool | None = False,
    ) -> Bar | None:
        """
        Process received bar data and convert it into Nautilus Trader's Bar format. This
        method determines whether the bar is new or a revision of an existing bar and
        converts the bar data to the Nautilus Trader's format.

        Parameters
        ----------
        bar_type_str : str
            The string representation of the bar type.
        bar : BarData
            The bar data received from Interactive Brokers.
        handle_revised_bars : bool
            Indicates whether revised bars should be handled or not.
        historical : bool | None, optional
            Indicates whether the bar data is historical. Defaults to False.

        Returns
        -------
        Bar | ``None``

        """
        previous_bar = self._bar_type_to_last_bar.get(bar_type_str)
        previous_ts = 0 if not previous_bar else int(previous_bar.date)
        current_ts = int(bar.date)

        if current_ts > previous_ts:
            is_new_bar = True
        elif current_ts == previous_ts:
            is_new_bar = False
        else:
            return None  # Out of sync

        self._bar_type_to_last_bar[bar_type_str] = bar
        bar_type: BarType = BarType.from_str(bar_type_str)
        ts_init = self._clock.timestamp_ns()
        if not handle_revised_bars:
            if previous_bar and is_new_bar:
                bar = previous_bar
            else:
                return None  # Wait for bar to close

            if historical:
                ts_init = await self._mt5_bar_to_ts_init(bar, bar_type)
                if ts_init >= self._clock.timestamp_ns():
                    return None  # The bar is incomplete

        # Process the bar
        return await self._mt5_bar_to_nautilus_bar(
            bar_type=bar_type,
            bar=bar,
            ts_init=ts_init,
            is_revision=not is_new_bar,
        )
            
    async def process_market_data_type(self, *, req_id: int, market_data_type: MarketDataTypeEnum) -> None:
        """
        Return the market data type (real-time, frozen, delayed)
        of ticker sent by MT5Client::req_market_data_type when Terminal switches from real-time
        to frozen and back and to delayed and back too.
        """
        if market_data_type == MarketDataTypeEnum.REALTIME:
            self._log.debug(f"Market DataType is {MarketDataTypeEnum.to_str(market_data_type)}")
        else:
            self._log.warning(f"Market DataType is {MarketDataTypeEnum.to_str(market_data_type)}")

    async def process_tick_by_tick_bid_ask(
        self,
        *,
        req_id: int,
        time: int,
        bid_price: float,
        ask_price: float,
        bid_size: Decimal,
        ask_size: Decimal,
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
        Update real-time 60 second bars.

        TODO: Add spread to nautilus bar type
        """
        if not (subscription := self._subscriptions.get(req_id=req_id)):
            return
        bar_type = BarType.from_str(subscription.name)
        instrument = self._cache.instrument(bar_type.instrument_id)

        bar = Bar(
            bar_type=bar_type,
            open=instrument.make_price(open_),
            high=instrument.make_price(high),
            low=instrument.make_price(low),
            close=instrument.make_price(close),
            volume=instrument.make_qty(0 if volume == -1 else volume),
            ts_event=pd.Timestamp.fromtimestamp(time, tz=pytz.utc).value,
            ts_init=self._clock.timestamp_ns(),
            is_revision=False,
        )

        await self._handle_data(bar)

    async def process_historical_data(self, *, req_id: int, bar: BarData) -> None:
        """
        Return the requested historical data bars.
        """
        if request := self._requests.get(req_id=req_id):
            bar_type = request.name[0]
            bar = await self._mt5_bar_to_nautilus_bar(
                bar_type=bar_type,
                bar=bar,
                ts_init=await self._mt5_bar_to_ts_init(bar, bar_type),
            )
            if bar:
                request.result.append(bar)
        elif subscription := self._subscriptions.get(req_id=req_id):
            bar = await self._process_bar_data(
                bar_type_str=str(subscription.name),
                bar=bar,
                handle_revised_bars=False,
                historical=True,
            )
            if bar:
                await self._handle_data(bar)
        else:
            self._log.debug(f"Received {bar=} on {req_id=}")
            return

    async def process_historical_data_end(self, *, req_id: int, start: str, end: str) -> None:
        """
        Mark the end of receiving historical bars.
        """
        self._end_request(req_id)

    async def process_historical_data_update(self, *, req_id: int, bar: BarData) -> None:
        """
        Receive bars in real-time if keepUpToDate is set as True in reqHistoricalData.

        Similar to realTimeBars function, except returned data is a composite of
        historical data and real time data that is equivalent to TWS chart functionality
        to keep charts up to date. Returned bars are successfully updated using real-
        time data.

        """
        if not (subscription := self._subscriptions.get(req_id=req_id)):
            return
        if not isinstance(subscription.handle, functools.partial):
            raise TypeError(f"Expecting partial type subscription method. {subscription=}")
        if bar := await self._process_bar_data(
            bar_type_str=str(subscription.name),
            bar=bar,
            handle_revised_bars=subscription.handle.keywords.get("handle_revised_bars", False),
        ):
            if bar.is_single_price() and bar.open.as_double() == 0:
                self._log.debug(f"Ignoring Zero priced {bar=}")
            else:
                await self._handle_data(bar)

    async def process_historical_ticks_bid_ask(
        self,
        *,
        req_id: int,
        ticks: list,
        done: bool,
    ) -> None:
        """
        Return the requested historic bid/ask ticks.
        """
        if not done:
            return
        if request := self._requests.get(req_id=req_id):
            instrument_id = InstrumentId.from_str(request.name[0])
            instrument = self._cache.instrument(instrument_id)

            for tick in ticks:
                ts_event = pd.Timestamp.fromtimestamp(tick.time, tz=pytz.utc).value
                quote_tick = QuoteTick(
                    instrument_id=instrument_id,
                    bid_price=instrument.make_price(tick.priceBid),
                    ask_price=instrument.make_price(tick.priceAsk),
                    bid_size=instrument.make_qty(tick.sizeBid),
                    ask_size=instrument.make_qty(tick.sizeAsk),
                    ts_event=ts_event,
                    ts_init=ts_event,
                )
                request.result.append(quote_tick)

            self._end_request(req_id)

    async def get_price(self, symbol, tick_type="MidPoint"):
        """
        Request market data for a specific symbol and tick type.

        This method requests market data from Interactive Brokers for the given
        symbol and tick type, waits for the response, and returns the result.

        Parameters
        ----------
        symbol : MT5Symbol
            The symbol details for which market data is requested.
        tick_type : str, optional
            The type of tick data to request (default is "MidPoint").

        Returns
        -------
        Any
            The market data result.

        Raises
        ------
        asyncio.TimeoutError
            If the request times out.

        """
        req_id = self._next_req_id()
        request = self._requests.add(
            req_id=req_id,
            name=f"{symbol.symbol}-{tick_type}",
            handle=functools.partial(
                self._mt5Client.req_mkt_data,
                req_id,
                symbol,
                tick_type,
                False,
                False,
                [],
            ),
            cancel=functools.partial(self._mt5Client.cancel_mkt_data, req_id),
        )
        request.handle()
        return await self._await_request(request, timeout=60)
    
