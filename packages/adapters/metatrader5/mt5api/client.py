from datetime import datetime, timezone
import logging
import queue
import socket
import sys
import threading
import time
from typing import Callable, Optional
from metatrader5.common import MT5Symbol, MT5SymbolDetails
from metatrader5.mt5api.stream_manager import StreamManager
from metatrader5.mt5api.symbol import convert_symbol_info_to_mt5_symbol_details
from metatrader5.mt5api.errors import TERMINAL_CONNECT_FAIL, SERVER_CONNECT_FAIL, TerminalError,  CodeMsgPair
from metatrader5.mt5api.utils import ClientException, current_fn_name
from metatrader5.mt5api.MetaTrader5 import MetaTrader5 
from metatrader5.mt5api.common import NO_VALID_ID, MarketDataTypeEnum


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
            # self.mt5_conn = MetaTrader5(self.host, self.port) if self.mt5_conn is None else self.mt5_conn
            # establish MetaTrader 5 connection to the specified trading account
            self.connected = super().initialize(path, **kwargs)
            if not self.connected:
                TERMINAL_CONNECT_FAIL = self.get_error()
                raise TerminalError(TERMINAL_CONNECT_FAIL)
            
            self.connection_time = datetime.now(timezone.utc).timestamp()
            self.msg_queue.put((0, current_fn_name(), self.terminal_info()))
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
    
    def send_msg(self, msg: str):
        """
        msg in this case is the code to be executed in the rpyc server
        """
        self.logger.debug("acquiring lock")
        self.lock.acquire()
        self.logger.debug("acquired lock")
        if not self.is_connected():
            self.logger.debug("sendMsg attempted while not connected, releasing lock")
            self.lock.release()
            return 0
        try:
            self.msg_queue.put(msg)
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
        
        account_info = self.account_info()
        self.connected_server = account_info.server
        self.logger.info(f"{self.is_connected()} | {self.connected_server}")

    def req_market_data_type(self, market_data_type: MarketDataTypeEnum):
        self.market_data_type = market_data_type
        # self.msg_queue.put((0, current_fn_name(), market_data_type))
        return
    
    def req_account_summary(self, req_id):
        return 
    
    def cancel_account_summary(self, req_id):
        return
    
    def req_positions(self):
        return
    
    def req_symbol_details(self, req_id, symbol: str) -> list[MT5SymbolDetails] | None:
        if "-" in symbol:
            symbol = symbol.replace("-", " ")
        
        mt5_results = self.symbols_get(symbol)
        if len(mt5_results) > 0:
            converted_mt5_symbol_details: list[MT5SymbolDetails] = []
            for symbol_info in mt5_results:
                if ("*" not in symbol or "!" not in symbol, "," not in symbol) and symbol_info.name == symbol:
                    converted_mt5_symbol_details.append(convert_symbol_info_to_mt5_symbol_details(symbol_info, self.connected_server))

            self.msg_queue.put((req_id, current_fn_name(), converted_mt5_symbol_details))
            return converted_mt5_symbol_details
        
        return None
    
    def req_matching_symbols(self, req_id, pattern: str):
        mt5_results = self.symbols_get(pattern)
        if len(mt5_results) > 0:
            converted_mt5_symbol_details: list[MT5SymbolDetails] = []
            for symbol_info in mt5_results:
                converted_mt5_symbol_details.append(convert_symbol_info_to_mt5_symbol_details(symbol_info, self.connected_server))

            self.msg_queue.put((req_id, current_fn_name(), converted_mt5_symbol_details))
            return converted_mt5_symbol_details
        
        return None
    
    def req_tick_by_tick_data(self, req_id, symbol: MT5Symbol, type: str = "BidAsk", size: int = 1, ignore_size: bool = False):
        # Attempt to enable the display of the symbol in MarketWatch
        if not self.symbol_select(symbol.symbol, True):
            code, msg = self.get_error()
            raise ClientException(code, msg, f"Failed to select {symbol.symbol}")


        _current_fn_name = current_fn_name()
        
        if self.market_data_type == MarketDataTypeEnum.REALTIME:
            def fetch_latest_tick(symbol):
                tick = self.symbol_info_tick(symbol)
                self.msg_queue.put((req_id, _current_fn_name, type, tick))
                return tick
            
            # Start the streaming task in its own thread
            self.stream_manager.create_streaming_task([symbol.symbol], 1, fetch_latest_tick)

        else:
            # TODO: fix this
            # copy_ticks_range(
            # symbol,       # symbol name
            # date_from,    # date the ticks are requested from
            # date_to,      # date, up to which the ticks are requested
            # flags         # combination of flags defining the type of requested ticks
            # )
            ticks = self.copy_ticks_range()

    def cancel_tick_by_tick_data(self, req_id, symbol: MT5Symbol, type: str = "BidAsk", size: int = 1, ignore_size: bool = False):
        self.stream_manager.stop_streaming_task([symbol.symbol])
        print(f"Streaming task for {symbol.symbol} has been stopped.")

    def req_historical_data(self, req_id):
        print("MT5Client.req_historical_data()")
        pass 

    def cancel_historical_data(self, req_id):
        print("MT5Client.cancel_historical_data()")
        pass 

    
