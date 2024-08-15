"""
Just a thin wrapper around rpyc.
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
from mt5api.errors import CONNECT_FAIL
from mt5api.common import NO_VALID_ID

#TODO: support SSL !!
# TODO: convert socket errors to rpyc errors 

logger = logging.getLogger(__name__)

class Connection:
    def __init__(self, host = 'localhost', port = 18812):
        self.host = host
        self.port = port
        self.rpyc_socket: Optional[rpyc.Connection] = None
        self.eval_result = None
        self.wrapper = None
        self.lock = threading.Lock()

    def connect(self):
        try:
            self.rpyc_socket = rpyc.classic.connect(self.host, self.port)
        except socket.error:
            if self.wrapper:
                self.wrapper.error(NO_VALID_ID, CONNECT_FAIL.code(), CONNECT_FAIL.msg())
        

        try:
            self.rpyc_socket._config['sync_request_timeout'] = 300 # 5 min
            self.rpyc_socket.execute('import MetaTrader5 as mt5')
            self.rpyc_socket.execute('import datetime')
        except AttributeError:
            if self.wrapper:
                self.wrapper.error(NO_VALID_ID, CONNECT_FAIL.code(), CONNECT_FAIL.msg())

    def disconnect(self):
        self.lock.acquire()
        try:
            if self.rpyc_socket is not None:
                logger.debug("disconnecting")
                # self.rpyc_socket.close()
                self.rpyc_socket = None
                logger.debug("disconnected")
                if self.wrapper:
                    self.wrapper.connectionClosed()
        finally:
            self.lock.release()

    def isConnected(self):
        return self.rpyc_socket is not None

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
            self.eval_result = self.rpyc_socket.eval(msg)
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
            # while waiting for self.rpyc_socket.recv() to timeout.
            logger.debug("Socket is broken or closed.")

        return self.eval_result

    def stream_data(self):
        """
            Str
        """
        if not self.isConnected():
            logger.debug("recvMsg attempted while not connected, releasing lock")
            return None
        pass