
"""
The MTReader runs in a separate threads and is responsible for receiving the
incoming messages.
It will read the packets from the wire, use the low level IB messaging to
remove the size prefix and put the rest in a Queue.
"""

import logging
from threading import Thread

logger = logging.getLogger(__name__)


class MT5Reader(Thread):
    def __init__(self, conn, msg_queue):
        super().__init__()
        self.conn = conn
        self.msg_queue = msg_queue

    def run(self):
        try:
            logger.debug("MT5Reader thread started")
            buf = b""
            while self.conn.isConnected():

                response = self.conn.recvMsg()
                logger.debug("reader loop, received size %d", len(str(response)))

                if response:
                    self.msg_queue.put(response)

            logger.debug("MT5Reader thread finished")
        except:
            logger.exception('unhandled exception in MT5Reader thread')

