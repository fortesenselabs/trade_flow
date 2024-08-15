"""
Just a thin wrapper around MetaTrader5 rpyc.
It allows us to keep some other info along with it.
"""

import socket
from typing import Optional
import rpyc
import threading
import logging
import sys

import rpyc.utils
import rpyc.utils.server
from mt5api.errors import TerminalError, SERVER_CONNECT_FAIL, TERMINAL_CONNECT_FAIL
from mt5api.common import NO_VALID_ID
from mt5api.rpyc.metatrader5 import MetaTrader5

logger = logging.getLogger(__name__)

class Connection:
    def __init__(self, host = 'localhost', port = 18812):
        self.host = host
        self.port = port
        self.mt5_socket: Optional[MetaTrader5] = None
        self.eval_result = None
        self.wrapper = None
        self.lock = threading.Lock()

    def connect(self, path: str = "", **kwargs):
        """
            **kwargs are to pass the trading account path and parameters. e.g:
               path,                     => path to the MetaTrader 5 terminal EXE file
               login=LOGIN,              => account number
               password="PASSWORD",      => password
               server="SERVER",          => server name as it is specified in the terminal
               timeout=TIMEOUT,          => timeout
               portable=False            => portable mode
        """
        try:
            self.mt5_socket = MetaTrader5(self.host, self.port)

            # establish MetaTrader 5 connection to the specified trading account
            if not self.mt5_socket.initialize(path, **kwargs):
                TERMINAL_CONNECT_FAIL.errorCode, TERMINAL_CONNECT_FAIL.errorMsg = self.mt5_socket.last_error()
                raise TerminalError(TERMINAL_CONNECT_FAIL)
        except TerminalError as e:
            logger.error(e.__str__())
            if self.wrapper:
                self.wrapper.error(NO_VALID_ID, TERMINAL_CONNECT_FAIL.code(), TERMINAL_CONNECT_FAIL.msg())
        except socket.error as e:
            logger.error(e)
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

    def isConnected(self):
        return self.mt5_socket is not None

    def sendMsg(self, msg: str):
        """
        msg in this case is the code to be executed in the rpyc server
        """
        logger.debug("acquiring lock")
        self.lock.acquire()
        logger.debug("acquired lock")
        if not self.isConnected():
            logger.debug("sendMsg attempted while not connected, releasing lock")
            self.lock.release()
            return 0
        try:
            self.eval_result = self.mt5_socket.eval(msg)
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

    def recvMsg(self):
        if not self.isConnected():
            logger.debug("recvMsg attempted while not connected, releasing lock")
            return None
        try:
            # receiving 0 bytes outside a timeout means the connection is either
            # closed or broken
            if self.eval_result is None or (self.eval_result is not None and len(str(self.eval_result)) == 0):
                logger.debug("socket either closed or broken, disconnecting")
                self.disconnect()
        except socket.timeout:
            logger.debug("socket timeout from recvMsg %s", sys.exc_info())
            self.eval_result = None
        except socket.error:
            logger.debug("socket broken, disconnecting")
            self.disconnect()
            self.eval_result = None
        except OSError:
            # Thrown if the socket was closed (ex: disconnected at end of script) 
            # while waiting for self.mt5_socket.recv() to timeout.
            logger.debug("Socket is broken or closed.")

        return self.eval_result
