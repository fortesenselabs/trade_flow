from datetime import datetime, timezone
import logging
import queue
import socket
import sys
import threading
import time
import numpy as np
from typing import Any, Callable, List, Optional
from metatrader5.mt5api.stream_manager import StreamManager
from metatrader5.mt5api.symbol import Symbol, SymbolInfo, process_symbol_details
from metatrader5.mt5api.errors import TERMINAL_CONNECT_FAIL, SERVER_CONNECT_FAIL, TerminalError,  CodeMsgPair
from metatrader5.mt5api.utils import ClientException, current_fn_name
from metatrader5.mt5api.MetaTrader5 import MetaTrader5 
from metatrader5.mt5api.common import NO_VALID_ID, BarData, MarketDataTypeEnum, TickerId


# 
# MT5Client 
# 
class MT5Client(MetaTrader5):
    (DISCONNECTED, CONNECTING, CONNECTED, REDIRECT) = range(4)

    def __init__(self, host: str = 'localhost', port: int = 18812,  keep_alive: bool = False, logger: Optional[Callable] = None):
        super().__init__(host, port, keep_alive)
        
        self.logger = logger if logger is not None else logging.getLogger(__class__.__name__)

        self.msg_queue = queue.Queue()
        self.lock = threading.Lock()
        self.stream_manager: StreamManager = StreamManager()
        self.stream_interval: float = 1

        self.enable_stream = False
        self.connected: bool = False
        self.connection_time = None
        self.conn_state = None
        self._terminal_version: Optional[int] = None
        self.client_id: Optional[int] = None
        self.market_data_type: MarketDataTypeEnum = MarketDataTypeEnum.NULL

    # 
    # Connection
    # 

    def connect(self, path: str = "", **kwargs):
        """
            path,                     => path to the MetaTrader 5 terminal EXE file
            login=LOGIN,              => account number
            password="PASSWORD",      => password
            server="SERVER",          => server name as it is specified in the terminal
            timeout=TIMEOUT,          => timeout
            portable=False            => portable mode
        """
        try:
            # establish MetaTrader 5 connection to the specified trading account
            self.connected = super().initialize(path, **kwargs)
            if not self.connected:
                TERMINAL_CONNECT_FAIL = self.get_error()
                raise TerminalError(TERMINAL_CONNECT_FAIL)
            
            self.connection_time = datetime.now(timezone.utc).timestamp()
            self.send_msg((0, current_fn_name(), self.terminal_info()))
        except TerminalError as e:
            if self.logger:
                TERMINAL_CONNECT_FAIL.errorMsg += f" => {e.__str__()}" 
                self.logger.error(NO_VALID_ID, TERMINAL_CONNECT_FAIL.code(), TERMINAL_CONNECT_FAIL.msg())
        except socket.error as e:
            if self.logger:
                SERVER_CONNECT_FAIL.errorMsg += f" => {e.__str__()}" 
                self.logger.error(NO_VALID_ID, SERVER_CONNECT_FAIL.code(), SERVER_CONNECT_FAIL.msg())

    def disconnect(self):
        self.lock.acquire()
        try:
            self.logger.debug("disconnecting")
            self.shutdown()
            self.logger.info("Connection closed")
            self.reset()
        finally:
            self.lock.release()

    def is_connected(self):
        return MT5Client.CONNECTED == self.conn_state and self.connected
    
    def send_msg(self, msg: Any):
        """
        """
        self.logger.debug("acquiring lock")
        self.lock.acquire()
        self.logger.debug("acquired lock")
        if not self.is_connected():
            self.logger.debug("sendMsg attempted while not connected, releasing lock")
            self.lock.release()
            return 0
        try:
            self.msg_queue.put_nowait(msg) # put_nowait
            nSent = len(msg)
        except socket.error:
            self.logger.debug("exception from sendMsg %s", sys.exc_info())
            raise
        finally:
            self.logger.debug("releasing lock")
            self.lock.release()
            self.logger.debug("release lock")

        self.logger.debug("sendMsg: sent: %d", nSent)

        return nSent

    def recv_msg(self):
        if not self.is_connected():
            self.logger.debug("recvMsg attempted while not connected, releasing lock")
            return None
        
        eval_result = None
        try:
            msg = self.msg_queue.get()
            self.logger.debug(f"Received message of type {type(msg).__name__}: {msg}")

            if isinstance(msg, str):
                if "get_connection_time" in msg:
                    eval_result = self.connection_time
                else:
                    eval_result = self.eval(msg)
            else:
                eval_result = msg
            
            self.msg_queue.task_done() # clear queue 
            # raise TypeError("Expected a string, bytes, or code object, but got: {}".format(type(msg).__name__))
        except socket.timeout:
            self.logger.debug("socket timeout from recvMsg %s", sys.exc_info())
        except socket.error:
            self.logger.debug("socket either closed or broken, disconnecting")
            self.disconnect()
        # except OSError:
        #     # Thrown if the socket was closed (ex: disconnected at end of script) 
        #     # while waiting for self.recv() to timeout.
        #     self.logger.debug("Socket is broken or closed.")

        return eval_result

    def get_error(self) -> Optional[CodeMsgPair]:
        if not self.is_connected():
            self.logger.debug("not connected to terminal")
            return None
        
        code, msg = self.last_error()
        if code == MetaTrader5.RES_E_INTERNAL_FAIL_INIT:
            return CodeMsgPair(code, f"Terminal initialization failed: {msg}")
        
        return CodeMsgPair(code, msg)
    
    def get_connection_time(self):
        return self.connection_time

    # 
    # Client
    # 

    def reset(self):
        self.host = None
        self.port = None
        self.connected = False
        self.client_id = None
        self._terminal_version = None
        self.connection_time = None
        self.conn_state = None
        self.enable_stream = False
        self.stream_manager = StreamManager()
        self.msg_queue = queue.Queue()
        self.market_data_type: MarketDataTypeEnum = MarketDataTypeEnum.NULL
        self.set_conn_state(MT5Client.DISCONNECTED)

    def set_conn_state(self, conn_state):
        _conn_state = self.conn_state
        self.conn_state = conn_state
        self.logger.debug("%s conn_state: %s -> %s" % (id(self), _conn_state,
                                                 self.conn_state))
    
    def start_api(self):
        """
            Check the Initialized terminal connection after connecting to rpyc socket.
        """

        if not self.is_connected():
            text = f"MetaTrader5 initialization failed, error = {self.get_error()}"
            self.logger.error(text)
            raise ClientException(TERMINAL_CONNECT_FAIL.code(), TERMINAL_CONNECT_FAIL.msg(), text)
        
        self.req_ids()
        self.managed_accounts()


    def req_ids(self):
        """Call this function to request from Terminal the next valid ID that
        can be used when placing an order.  After calling this function, the
        next_valid_id() event will be triggered, and the id returned is that next
        valid ID. That ID will reflect any autobinding that has occurred (which
        generates new IDs and increments the next valid ID therein).
        """
        ids = np.random.randint(10000, size=1)
        self.send_msg((0, current_fn_name(), ids.tolist()))

    def req_market_data_type(self, market_data_type: MarketDataTypeEnum):
        self.market_data_type = market_data_type
        self.send_msg((0, current_fn_name(), self.market_data_type.value))
        return None
    
    def managed_accounts(self):
        account_info = self.account_info()
        self.connected_server = account_info.server
        self.logger.info(f"{self.is_connected()} | {self.connected_server}")
        accounts = tuple([f"{account_info.login}"])
        self.send_msg((0, current_fn_name(), accounts))
    
    def req_account_summary(self, req_id: TickerId):
        return 
    
    def cancel_account_summary(self, req_id: TickerId):
        return
    
    def req_positions(self):
        return
    
    
    def req_symbol_details(self, req_id: TickerId, symbol: str) -> list[SymbolInfo] | None:
        if symbol == "":
            return None 
        
        if "-" in symbol:
            symbol = symbol.replace("-", " ")
        
        mt5_results = self.symbols_get(symbol)
        if len(mt5_results) > 0:
            symbol_details: List[SymbolInfo] = []
            for symbol_info in mt5_results:
                if ("*" not in symbol or "!" not in symbol, "," not in symbol) and symbol_info.name == symbol:
                    symbol_details.append(process_symbol_details(symbol_info, self.connected_server))
                    break 

            # if self.market_data_type == MarketDataTypeEnum.REALTIME:
            self.send_msg((req_id, current_fn_name(), symbol_details))
            return symbol_details
        
        return None
    
    def req_matching_symbols(self, req_id: TickerId, pattern: str):
        mt5_results = self.symbols_get(pattern)
        if len(mt5_results) > 0:
            symbol_details: List[SymbolInfo] = []
            for symbol_info in mt5_results:
                symbol_details.append(process_symbol_details(symbol_info, self.connected_server))

            # if self.market_data_type == MarketDataTypeEnum.REALTIME:
            self.send_msg((req_id, current_fn_name(), symbol_details))
            return symbol_details
            
        return None
    
    def req_tick_by_tick_data(self, req_id: TickerId, symbol: Symbol, type: str = "BidAsk", size: int = 1, ignore_size: bool = False):
        # Attempt to enable the display of the symbol in MarketWatch
        if not self.symbol_select(symbol.symbol, True):
            code, msg = self.get_error()
            raise ClientException(code, msg, f"Failed to select {symbol.symbol}")


        _current_fn_name = current_fn_name()
        
        if self.market_data_type == MarketDataTypeEnum.REALTIME:
            def fetch_latest_tick(symbol):
                tick = self.symbol_info_tick(symbol)
                self.send_msg((req_id, _current_fn_name, type, tick))
                return tick
            
            # Start the streaming task in its own thread
            self.stream_manager.create_streaming_task(f"TICK-{str(req_id)}", [symbol.symbol], self.stream_interval, fetch_latest_tick)

        else:
            # TODO: fix this
            # copy_ticks_range(
            # symbol,       # symbol name
            # date_from,    # date the ticks are requested from
            # date_to,      # date, up to which the ticks are requested
            # flags         # combination of flags defining the type of requested ticks
            # )
            ticks = self.copy_ticks_range()

    def cancel_tick_by_tick_data(self, req_id: TickerId, symbol: Symbol, type: str = "BidAsk", size: int = 1, ignore_size: bool = False):
        self.stream_manager.stop_streaming_task(f"TICK-{str(req_id)}", [symbol.symbol])
        print(f"Streaming task for {req_id} has been stopped.")

    def req_real_time_bars(self, req_id: TickerId, symbol: Symbol, bar_size: int, what_to_show: str, use_rth: bool):
        _current_fn_name = current_fn_name()
        
        if self.market_data_type == MarketDataTypeEnum.REALTIME:
            def fetch_latest_tick(symbol):
                raw_bars = self.copy_rates_from_pos(symbol, MetaTrader5.TIMEFRAME_M1, 0, 1)

                processed_bars = []
                for raw_bar in raw_bars:
                    processed_bars.append(BarData(
                        time=raw_bar[0],
                        open_=raw_bar[1],
                        high=raw_bar[2],
                        low=raw_bar[3],
                        close=raw_bar[4],
                        tick_volume=raw_bar[5],
                        spread=raw_bar[6],
                        real_volume=raw_bar[7],
                    ))
                
                self.send_msg((req_id, _current_fn_name, processed_bars))
                return processed_bars
            
            # Start the streaming task in its own thread
            self.stream_manager.create_streaming_task(f"BAR-{str(req_id)}", [symbol.symbol], MetaTrader5.TIMEFRAME_M1 * 60, fetch_latest_tick)
        else:
            pass 

        
    def cancel_real_time_bars(self, req_id: TickerId, symbol: Symbol):
        self.stream_manager.stop_streaming_task(f"BAR-{str(req_id)}", [symbol.symbol])
        print(f"Streaming task for {req_id} has been stopped.")

    def req_historical_data(self, req_id: TickerId , symbol: Symbol, end_datetime: str,
                                  duration_str: str, bar_size_setting: str, what_to_show: str,
                                  use_rth:int, format_date: int, keep_up_to_date: bool):
        """Requests symbols' historical data. When requesting historical data, a
        finishing time and date is required along with a duration string.

        req_id: TickerId - The id of the request. Must be a unique value. When the
            market data returns.
        symbol: Symbol - This object contains a description of the symbol for which
            market data is being requested.
        end_datetime: str - Defines a query end date and time at any point during the past 6 mos.
            Valid values include any date/time within the past six months in the format:
            YYYY-MM-dd HH:MM:SS 
        duration_str: str - Set the query duration up to one week, using a time unit
            of minutes, days or weeks. Valid values include any integer followed by a space
            and then M (minutes), D (days) or W (week). If no unit is specified, minutes is used.
        bar_size_setting: str - Specifies the size of the bars that will be returned (within Terminal listimits).
            Valid values include:
            1 sec
            5 secs
            15 secs
            30 secs
            1 min
            2 mins
            3 mins
            5 mins
            15 mins
            30 mins
            1 hour
            1 day
        what_to_show: str - Determines the nature of data being extracted. Valid values include:
            TRADES
            BID_ASK
        use_rth: int - Determines whether to return all data available during the requested time span,
            or only data that falls within regular trading hours. Valid values include:

            0 - all data is returned even where the market in question was outside of its
            regular trading hours.
            1 - only data within the regular trading hours is returned, even if the
            requested time span falls partially or completely outside of the RTH.
        format_date: int - Determines the date format applied to returned bars. Valid values include:
            1 - dates applying to bars returned in the format: yyyymmdd{space}{space}hh:mm:dd
            2 - dates are returned as a long integer specifying the number of seconds since
                1/1/1970 GMT.
        """
        
        _current_fn_name = current_fn_name()
        
        # if self.market_data_type == MarketDataTypeEnum.REALTIME:
        #     def fetch_latest_tick(symbol):
        #         raw_bars = self.copy_rates_from(symbol, MetaTrader5.TIMEFRAME_M1, 0, 1)
                
        #         processed_bars = []
        #         for raw_bar in raw_bars:
        #             processed_bars.append(BarData(
        #                 time=raw_bar[0],
        #                 open_=raw_bar[1],
        #                 high=raw_bar[2],
        #                 low=raw_bar[3],
        #                 close=raw_bar[4],
        #                 tick_volume=raw_bar[5],
        #                 spread=raw_bar[6],
        #                 real_volume=raw_bar[7],
        #             ))
                
        #         self.send_msg((req_id, _current_fn_name, processed_bars))
        #         return processed_bars
            
        #     # Start the streaming task in its own thread
        #     self.stream_manager.create_streaming_task(f"HISTORICAL-BAR-{str(req_id)}", [symbol.symbol], MetaTrader5.TIMEFRAME_M1 * 60, fetch_latest_tick)
        # else:
        #     pass  

    def cancel_historical_data(self, req_id: TickerId, symbol: Symbol):
        self.stream_manager.stop_streaming_task(f"HISTORICAL-BAR-{str(req_id)}", [symbol.symbol])
        print(f"Streaming task for {req_id} has been stopped.")

    
