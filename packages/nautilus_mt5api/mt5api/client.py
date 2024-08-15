"""
    The main class to use from API user's point of view.
    It takes care of almost everything:
    - implementing the requests
    - creating the answer decoder
    - creating the connection to Terminal

The user just needs to override EWrapper methods to receive the answers.
"""

from datetime import datetime, timezone
import logging
import queue
import socket
from typing import Dict, Optional

import pytz

from mt5api import (reader, comm)
from mt5api.connection import Connection
# from mt5api.message import OUT
from mt5api.common import * # @UnusedWildImport
from mt5api.contract import Contract
# from mt5api.order import Order, COMPETE_AGAINST_BEST_OFFSET_UP_TO_MID
# from mt5api.execution import ExecutionFilter
# from mt5api.scanner import ScannerSubscription
from mt5api.utils import (current_fn_name, BadMessage)
from mt5api.errors import * #@UnusedWildImport
from mt5api.server_versions import * # @UnusedWildImport
from mt5api.utils import ClientException

# TODO: use pylint

logger = logging.getLogger(__name__)


class MT5Client(object):
    (DISCONNECTED, CONNECTING, CONNECTED, REDIRECT) = range(4)

    def __init__(self, wrapper):
        self.msg_queue = queue.Queue()
        self.wrapper = wrapper
        self.decoder = None
        self.market_book: Optional[Dict[TickerId, str]] = None
        self.reset()

    def reset(self):
        self.nKeybIntHard = 0
        self.conn = None
        self.host = None
        self.port = None
        self.extraAuth = False
        self.clientId = None
        self.serverVersion_ = None
        self.connTime = None
        self.connState = None
        self.optCapab = ""
        self.asynchronous = False
        self.reader = None
        self.decode = None
        self.market_book = None
        self.setConnState(MT5Client.DISCONNECTED)
        self.connectionOptions = None


    def setConnState(self, connState):
        previous_connState = self.connState
        self.connState = connState
        logger.debug("%s connState: %s -> %s" % (id(self), previous_connState,
                                                 self.connState))

    def sendMsg(self, method: str, *args, **kwargs):
        full_msg = comm.make_msg(method, *args, **kwargs)
        logger.info("%s %s %s", "SENDING", current_fn_name(1), full_msg)
        self.conn.sendMsg(full_msg)

    def logRequest(self, fnName, fnParams):
        if logger.isEnabledFor(logging.INFO):
            if 'self' in fnParams:
                prms = dict(fnParams)
                del prms['self']
            else:
                prms = fnParams
            logger.info("REQUEST %s %s" % (fnName, prms))

    def startApi(self):
        """  Initiates the message exchange between the client application and
        the MT5 Terminal. """

        self.logRequest(current_fn_name(), vars())

        if not self.isConnected():
            self.wrapper.error(NO_VALID_ID, NOT_CONNECTED.code(),
                               NOT_CONNECTED.msg())
            return

        try: 
            if self.serverVersion() < MIN_CLIENT_VER:
                self.sendMsg("mt5.version()")
        except ClientException as ex:
            self.wrapper.error(NO_VALID_ID, ex.code, ex.msg + ex.text)
            return
        

    def connect(self, host: str = "localhost", port: int = 18812, clientId: int = 1):
        """This function must be called before any other. There is no
        feedback for a successful connection, but a subsequent attempt to
        connect will return the message \"Already connected.\"

        host:str - The host name or IP address of the machine where Terminal is
            running. Leave blank to connect to the local host.
        port:int - Must match the port specified in rpyc server.
        clientId:int - A number used to identify this client connection. All
            orders placed/modified from this client will be associated with
            this client identifier.

            Note: Each client MUST connect with a unique clientId."""

        try:
            self.host = host
            self.port = port
            self.clientId = clientId
            logger.debug("Connecting to %s:%d w/ id:%d", self.host, self.port, self.clientId)

            self.conn = Connection(self.host, self.port)

            self.conn.connect()
            self.setConnState(MT5Client.CONNECTING)

            # TODO: support async mode
            # Set connection options
            args = ()
            kwargs = {}
            if self.connectionOptions:
                args, kwargs = self.connectionOptions
            
            msg = comm.make_msg("initialize", *args, **kwargs)
            logger.debug("REQUEST %s", msg)
            self.conn.sendMsg(msg)

            response = self.conn.recvMsg()
            if not self.conn.isConnected() and response:
                logger.warning('Disconnected; resetting connection')
                self.reset()
            logger.debug("ANSWER %s", response)

            msg = comm.make_msg("version")
            logger.debug("REQUEST %s", msg)
            self.conn.sendMsg(msg)

            response = self.conn.recvMsg()
            (server_version, build, build_release_date) = response
            conn_time = datetime.now(timezone.utc)
            server_version = int(server_version)
            logger.debug("ANSWER Version:%d time:%s", server_version, conn_time)
            self.connTime = conn_time
            self.serverVersion_ = server_version

            self.setConnState(MT5Client.CONNECTED)

            self.reader = reader.MT5Reader(self.conn, self.msg_queue)
            self.reader.start()   # start thread

            logger.info("sent startApi")
            self.startApi()

            self.wrapper.connectAck()
        except socket.error:
            if self.wrapper:
                self.wrapper.error(NO_VALID_ID, CONNECT_FAIL.code(), CONNECT_FAIL.msg())

            logger.info("could not connect")
            self.disconnect()


    def disconnect(self):
        """Call this function to terminate the connections with TWS.
        Calling this function does not cancel orders that have already been
        sent."""

        self.setConnState(MT5Client.DISCONNECTED)
        if self.conn is not None:
            logger.info("disconnecting")
            self.conn.disconnect()
            self.wrapper.connectionClosed()
            self.reset()


    def isConnected(self):
        """Call this function to check if there is a connection with TWS"""

        connConnected = self.conn and self.conn.isConnected()
        logger.debug("%s isConn: %s, connConnected: %s" % (id(self),
            self.connState, str(connConnected)))
        return MT5Client.CONNECTED == self.connState and connConnected

    def keyboardInterrupt(self):
        #intended to be overloaded
        pass

    def keyboardInterruptHard(self):
        self.nKeybIntHard += 1
        if self.nKeybIntHard > 5:
            raise SystemExit()

    def setConnectionOptions(self, opts):
        self.connectionOptions = opts

    def msgLoopTmo( self ):
        #intended to be overloaded
        pass

    def msgLoopRec( self ):
        #intended to be overloaded
        pass

    def run(self):
        """This is the function that has the message loop."""

        try:
            while self.isConnected() or not self.msg_queue.empty():
                try:
                    try:
                        response = self.msg_queue.get(block=True, timeout=0.2)
                        if len(response) > MAX_MSG_LEN:
                            self.wrapper.error(NO_VALID_ID, BAD_LENGTH.code(),
                                "%s:%d:%s" % (BAD_LENGTH.msg(), len(str(response)), response))
                            break
                    except queue.Empty:
                        logger.debug("queue.get: empty")
                        self.msgLoopTmo()
                    else:
                        # response
                        # TODO: is this block necessary? since response is no longer bytes
                        fields = comm.read_fields(text)
                        logger.debug("fields %s", fields)
                        self.decoder.interpret(fields)

                        self.msgLoopRec()
                except (KeyboardInterrupt, SystemExit):
                    logger.info("detected KeyboardInterrupt, SystemExit")
                    self.keyboardInterrupt()
                    self.keyboardInterruptHard()
                except BadMessage:
                    logger.info("BadMessage")

                logger.debug("conn:%d queue.sz:%d",
                             self.isConnected(),
                             self.msg_queue.qsize())
        finally:
            self.disconnect()

    def serverVersion(self):
        """Returns the version of the Terminal instance to which the API
        application is connected."""

        return self.serverVersion_
    
    def terminalConnectionTime(self):
        """Returns the time the API application made a connection to Terminal."""

        return self.connTime

    def setServerLogLevel(self, logLevel: int):
        """The default detail level is ERROR. For more details, see API
        Logging."""

        self.logRequest(current_fn_name(), vars())

        if not self.isConnected():
            self.wrapper.error(NO_VALID_ID, NOT_CONNECTED.code(),
                               NOT_CONNECTED.msg())
            return

        self.serverLogLevel = logLevel

    def reqCurrentTime(self):
        """Asks the current system time on the server side."""

        self.logRequest(current_fn_name(), vars())

        if not self.isConnected():
            self.wrapper.error(NO_VALID_ID, NOT_CONNECTED.code(),
                               NOT_CONNECTED.msg())
            return

        conn_time = datetime.now(timezone.utc)
        self.conn.eval_result = conn_time

    ##########################################################################
    ################## Market Data
    ##########################################################################


    def reqMktData(self, reqId: TickerId, contract: Contract, snapshot: bool = False):
        """Call this function to request market data. The market data
        will be returned by the tickPrice and tickSize events.

        reqId: TickerId - The ticker id. Must be a unique value. When the
            market data returns, it will be identified by this tag. This is
            also used when canceling the market data.
        contract: Contract - This structure contains a description of the
            Contract for which market data is being requested.
        snapshot: bool - Check to return a single snapshot of Market data and
            have the market data subscription cancel.
        """

        self.logRequest(current_fn_name(), vars())

        if not self.isConnected():
            self.wrapper.error(reqId, NOT_CONNECTED.code(),
                               NOT_CONNECTED.msg())
            return

        if self.serverVersion() < MIN_CLIENT_VER:
            if contract.symbol:
                self.wrapper.error(reqId, UPDATE_TWS.code(),
                    UPDATE_TWS.msg() + "  It does not support market book.")
                return

        try:
            # send market_book_add msg with contract symbol
            msg = comm.make_msg("market_book_add", contract.symbol)
            self.sendMsg(msg)
            self.market_book[reqId] = contract.symbol
            msg = comm.make_msg("market_book_get", contract.symbol)
            self.sendMsg(msg)

            if snapshot:
                msg = comm.make_msg("market_book_release", contract.symbol)
                self.sendMsg(msg)
                del self.market_book[reqId]
        except ClientException as ex:
            self.wrapper.error(reqId, ex.code, ex.msg + ex.text)
            return
        
    def cancelMktData(self, reqId: TickerId):
        """After calling this function, market data for the specified id
        will stop flowing.

        reqId: TickerId - The ID that was specified in the call to
            reqMktData(). 
        """

        self.logRequest(current_fn_name(), vars())

        if not self.isConnected():
            self.wrapper.error(reqId, NOT_CONNECTED.code(), NOT_CONNECTED.msg())
            return
        
        # send market_book_release msg
        if self.market_book is not None:
            if reqId in list(self.market_book.keys()):
                symbol = self.market_book[reqId]
                msg = comm.make_msg("market_book_release", symbol)
                self.sendMsg(msg)

    def reqTickByTickData(self, reqId: int, contract: Contract, 
                          numberOfTicks: int, ignoreSize: bool = False, flags: str = "COPY_TICKS_ALL"):
        self.logRequest(current_fn_name(), vars())

        if not self.isConnected():
            self.wrapper.error(NO_VALID_ID, NOT_CONNECTED.code(), NOT_CONNECTED.msg())
            return

        if self.serverVersion() < MIN_CLIENT_VER:
            self.wrapper.error(NO_VALID_ID, UPDATE_TWS.code(), UPDATE_TWS.msg() +
                               " It does not support tick-by-tick data requests.")
            return

        try:
            msg = comm.make_msg("symbol_info_tick", contract.symbol)
            self.sendMsg(msg)

            if numberOfTicks > 0:
                #  get the number of ticks required 
                # calculate utc_from from the numberOf Ticks 
                # that is back ward
                # set time zone to UTC
                timezone = pytz.timezone("Etc/UTC")
                # create 'datetime' object in UTC time zone to avoid the implementation of a local time zone offset
                utc_from = datetime(2020, 1, 10, tzinfo=timezone)
                # request 100 000 EURUSD ticks starting from 10.01.2019 in UTC time zone
                ticks = mt5.copy_ticks_from("EURUSD", utc_from, 100000, mt5.COPY_TICKS_ALL)
                pass

            
            msg = make_field(OUT.REQ_TICK_BY_TICK_DATA)\
                + make_field(reqId) \
                + make_field(contract.conId) \
                + make_field(contract.symbol) \
                + make_field(contract.secType) \
                + make_field(contract.lastTradeDateOrContractMonth) \
                + make_field(contract.strike) \
                + make_field(contract.right) \
                + make_field(contract.multiplier) \
                + make_field(contract.exchange) \
                + make_field(contract.primaryExchange) \
                + make_field(contract.currency) \
                + make_field(contract.localSymbol) \
                + make_field(contract.tradingClass) \
                + make_field(tickType)
    
            if self.serverVersion() >= MIN_SERVER_VER_TICK_BY_TICK_IGNORE_SIZE:
                msg += make_field(numberOfTicks) \
                    + make_field(ignoreSize)

        except ClientException as ex:
            self.wrapper.error(reqId, ex.code, ex.msg + ex.text)
            return

        self.sendMsg(msg)

    def cancelTickByTickData(self, reqId: int):
        self.logRequest(current_fn_name(), vars())

        if not self.isConnected():
            self.wrapper.error(NO_VALID_ID, NOT_CONNECTED.code(), NOT_CONNECTED.msg())
            return

        if self.serverVersion() < MIN_CLIENT_VER:
            self.wrapper.error(NO_VALID_ID, UPDATE_TWS.code(), UPDATE_TWS.msg() +
                               " It does not support tick-by-tick data requests.")
            return

        msg = make_field(OUT.CANCEL_TICK_BY_TICK_DATA) \
            + make_field(reqId)
        
        del self.market_book[reqId]
        self.sendMsg(msg)



