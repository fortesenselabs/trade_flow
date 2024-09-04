"""
This is the interface that will need to be overloaded by the customer so
that his/her code can receive info from the Terminal.
"""

from .MetaTrader5 import MetaTrader5 as mt5


class TerminalError(Exception):
    pass

class SymbolSelectError(Exception):
    pass

class CodeMsgPair:
    def __init__(self, code, msg):
        self.errorCode = code
        self.errorMsg = msg

    def __str__(self):
        return f"code={self.errorCode}, msg={self.errorMsg}"
    
    def code(self):
        return self.errorCode

    def msg(self):
        return self.errorMsg
    



ALREADY_CONNECTED = CodeMsgPair(mt5.RES_S_OK,	"Already connected.")
SERVER_CONNECT_FAIL = CodeMsgPair(-1, "Rpyc Server connection failed")
TERMINAL_CONNECT_FAIL = CodeMsgPair(mt5.RES_E_INTERNAL_FAIL_INIT, "Terminal initialization failed")

UPDATE_TWS = CodeMsgPair(503, "The TWS is out of date and must be upgraded.")

NOT_CONNECTED = CodeMsgPair(504, "Not connected")

UNKNOWN_ID = CodeMsgPair(505, "Fatal Error: Unknown message id.")
UNSUPPORTED_VERSION = CodeMsgPair(506, "Unsupported version")
BAD_LENGTH = CodeMsgPair(507, "Bad message length")
BAD_MESSAGE = CodeMsgPair(508, "Bad message")
SOCKET_EXCEPTION = CodeMsgPair(509, "Exception caught while reading socket - ")
FAIL_CREATE_SOCK = CodeMsgPair(520, "Failed to create socket")
SSL_FAIL = CodeMsgPair(530, "SSL specific error: ")
INVALID_SYMBOL = CodeMsgPair(579, "Invalid symbol in string - ")