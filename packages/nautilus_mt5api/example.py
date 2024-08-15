from mt5api.connection import Connection
from mt5api.client import MT5Client

# Raw RPYC Connection
rpyc_conn = Connection()
rpyc_conn.connect()

rpyc_conn.sendMsg("mt5.initialize()")
print(rpyc_conn.recvMsg())
rpyc_conn.sendMsg("mt5.version()")
print(rpyc_conn.recvMsg())
rpyc_conn.sendMsg("mt5.terminal_info()")
print(rpyc_conn.recvMsg())
rpyc_conn.sendMsg("mt5.account_info()")
print(rpyc_conn.recvMsg())
rpyc_conn.sendMsg("mt5.market_book_add('Step Index')")
print(rpyc_conn.recvMsg())
rpyc_conn.sendMsg("mt5.market_book_get('Step Index')")
print(rpyc_conn.recvMsg())
rpyc_conn.disconnect()


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