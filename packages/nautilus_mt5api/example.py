from mt5api.connection import Connection
from mt5api.client import MT5Client

# Raw MT5 RPYC Connection
mt5_conn = Connection()
mt5_conn.connect()

mt5_conn.sendMsg("mt5.version()")
print(mt5_conn.recvMsg())
mt5_conn.sendMsg("mt5.terminal_info()")
print(mt5_conn.recvMsg())
mt5_conn.sendMsg("mt5.account_info()")
print(mt5_conn.recvMsg())
mt5_conn.sendMsg("mt5.market_book_add('Step Index')")
print(mt5_conn.recvMsg())
mt5_conn.sendMsg("mt5.market_book_get('Step Index')")
print(mt5_conn.recvMsg())
mt5_conn.sendMsg("mt5.symbol_select('Step Index', True)")
print(mt5_conn.recvMsg())
mt5_conn.sendMsg("mt5.symbol_info_tick('Step Index')")
print(mt5_conn.recvMsg())
mt5_conn.disconnect()


# if self.rpyc_socket is not None:
#     # establish connection to the MetaTrader 5 terminal
#     self.sendMsg("mt5.initialize()")
#     is_terminal_connected = self.recvMsg()


# 
# MT5Client
# 

class MTWrapper:
    def error(self, id, code, msg):
        print(f"Error: id={id}, code={code}, msg={msg}")

    def connectAck(self):
        print("Connected")
    
    def connectionClosed(self):
        print("Connection Closed")

wrapper = MTWrapper()
client = MT5Client(wrapper)
client.connect()
client.reqCurrentTime()
# client.reqMktData()
client.disconnect()