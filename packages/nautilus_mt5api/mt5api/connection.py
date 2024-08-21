"""
Just a thin wrapper around MetaTrader5 rpyc.
It allows us to keep some other info along with it.
"""

import queue
import socket
import threading
import logging
import sys
from typing import Optional
from datetime import datetime, timezone

from mt5api.errors import TerminalError, CodeMsgPair, SERVER_CONNECT_FAIL, TERMINAL_CONNECT_FAIL
from mt5api.common import NO_VALID_ID
from mt5api.rpyc import metatrader5 as mt

logger = logging.getLogger(__name__)

class Connection:
    def __init__(self, host = 'localhost', port = 18812):
        self.host = host
        self.port = port
        self.mt5_socket: Optional[mt.MetaTrader5] = None
        self.connection_time = None
        self.wrapper = None
        self.msg_queue = queue.Queue()
        self.lock = threading.Lock()

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
            self.mt5_socket = mt.MetaTrader5(self.host, self.port)

            # establish MetaTrader 5 connection to the specified trading account
            if not self.mt5_socket.initialize(path, **kwargs):
                TERMINAL_CONNECT_FAIL = self.get_error()
                self.mt5_socket = None
                raise TerminalError()
            
            self.connection_time = datetime.now(timezone.utc).timestamp()
        except TerminalError as e:
            logger.error(e.__str__())
            if self.wrapper:
                self.wrapper.error(NO_VALID_ID, TERMINAL_CONNECT_FAIL.code(), TERMINAL_CONNECT_FAIL.msg())
        except socket.error as e:
            logger.error(e.__str__())
            if self.wrapper:
                self.wrapper.error(NO_VALID_ID, SERVER_CONNECT_FAIL.code(), SERVER_CONNECT_FAIL.msg())

    def disconnect(self):
        self.lock.acquire()
        try:
            if self.mt5_socket is not None:
                logger.debug("disconnecting")
                self.mt5_socket.shutdown()
                self.mt5_socket = None
                logger.debug("disconnected")
                if self.wrapper:
                    self.wrapper.connectionClosed()
        finally:
            self.lock.release()

    def is_connected(self):
        return self.mt5_socket is not None

    def send_msg(self, msg: str):
        """
        msg in this case is the code to be executed in the rpyc server
        """
        logger.debug("acquiring lock")
        self.lock.acquire()
        logger.debug("acquired lock")
        if not self.is_connected():
            logger.debug("sendMsg attempted while not connected, releasing lock")
            self.lock.release()
            return 0
        try:
            self.msg_queue.put(msg)
            nSent = len(msg)
        except socket.error:
            logger.debug("exception from sendMsg %s", sys.exc_info())
            raise
        finally:
            logger.debug("releasing lock")
            self.lock.release()
            logger.debug("release lock")

        logger.debug("sendMsg: sent: %d", nSent)

        return nSent

    def recv_msg(self):
        if not self.is_connected():
            logger.debug("recvMsg attempted while not connected, releasing lock")
            return None
        
        eval_result = None
        try:
            msg = self.msg_queue.get()
            if "get_connection_time()" in msg:
                eval_result = self.connection_time
            else:
                eval_result = self.mt5_socket.eval(msg)
        except socket.timeout:
            logger.debug("socket timeout from recvMsg %s", sys.exc_info())
        except socket.error:
            logger.debug("socket either closed or broken, disconnecting")
            self.disconnect()
        # except OSError:
        #     # Thrown if the socket was closed (ex: disconnected at end of script) 
        #     # while waiting for self.mt5_socket.recv() to timeout.
        #     logger.debug("Socket is broken or closed.")

        return eval_result
    
    def get_error(self) -> Optional[CodeMsgPair]:
        if not self.is_connected():
            logger.debug("not connected to terminal")
            return None
        
        code, msg = self.mt5_socket.last_error()
        if code == mt.RES_E_INTERNAL_FAIL_INIT:
            return CodeMsgPair(code, f"Terminal initialization failed: {msg}")
        
        return CodeMsgPair(code, msg)
    
    def get_connection_time(self):
        return self.connection_time
