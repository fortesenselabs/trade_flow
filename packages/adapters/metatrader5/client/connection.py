import asyncio

from metatrader5.mt5api.client import MT5Client

from metatrader5.client.common import BaseMixin
from nautilus_trader.common.enums import LogColor


class MetaTrader5ClientConnectionMixin(BaseMixin):
    """
    Manages the connection to Terminal for the MetaTrader5Client.

    This class is responsible for establishing and maintaining the rpyc connection,
    handling server communication, monitoring the connection's health, and managing
    re-connections. When a connection is established and the client finishes initializing,
    the `_is_mt5_connected` event is set, and if the connection is lost, the
    `_is_mt5_connected` event is cleared.

    """

    async def _connect(self) -> None:
        """
        Establish the rpyc socket connection with Terminal.

        This initializes the connection, connects the rpyc socket, fetches version
        information, and then sets a flag that the connection has been successfully
        established.

        """
        try:
            self._mt5Client = MT5Client(self._host, self._port)
            self._log.info(
                f"Connecting to {self._host}:{self._port} with client id: {self._client_id}",
            )
            await asyncio.to_thread(self._mt5Client.connect)

            self._mt5Client.set_conn_state(MT5Client.CONNECTING)

            await self._fetch_terminal_info()
            self._mt5Client.set_conn_state(MT5Client.CONNECTED)
            self._log.info(
                f"Connected to MetaTrader 5 Terminal (v{self._terminal_version}, {self._build}, {self._build_release_date}) "
                f"at {self._mt5Client.connection_time} from {self._host}:{self._port} "
                f"with client id: {self._client_id}."
            )
            self._is_mt5_connected.set() # TODO: move this to TWrapper managed accounts
        except asyncio.CancelledError:
            self._log.info("Connection cancelled.")
            await self._disconnect()
        except Exception as e:
            self._log.error(f"Connection failed: {e}")
            await self._handle_reconnect()

    async def _disconnect(self) -> None:
        """
        Disconnect from Terminal and clear the `_is_mt5_connected` flag.
        """
        try:
            # shut down connection to the MetaTrader 5 terminal
            self._mt5Client.shutdown()
            if self._is_mt5_connected.is_set():
                self._log.debug("`_is_mt5_connected` unset by `_disconnect`.", LogColor.BLUE)
                self._is_mt5_connected.clear()
            self._log.info("Disconnected from MetaTrader 5 Terminal.")
        except Exception as e:
            self._log.error(f"Disconnection failed: {e}")

    async def _handle_reconnect(self) -> None:
        """
        Attempt to reconnect to Terminal.
        """
        self._reset()
        self._resume()
        # await self._connect()

    async def _fetch_terminal_info(self) -> None:
        """
        Receive and process the terminal version information.

        Waits for the terminal to send its version information.
        Retries receiving this information up to a specified number of attempts.

        Raises
        ------
        ConnectionError
            If the server version information is not received within the allotted retries.

        """
        retries_remaining = 5

        while retries_remaining > 0:
            server_info = await asyncio.to_thread(self._mt5Client.version)
            if isinstance(server_info, tuple) and server_info[0] > 0:
                self._process_terminal_version(server_info)
                break
            else:
                self._log.debug(f"Received empty response. {server_info}")

            retries_remaining -= 1
            self._log.warning(
                "Failed to receive server version information. "
                f"Retries remaining: {retries_remaining}.",
            )
            await asyncio.sleep(1)

        if retries_remaining == 0:
            raise ConnectionError(
                "Max retry attempts reached. Failed to receive server version information.",
            )

    def _process_terminal_version(self, fields: tuple[str]) -> None:
        """
        Process and log the terminal version information.
        """
        terminal_version, build, build_release_date = int(fields[0]), int(fields[1]), fields[2]
        self._terminal_version = terminal_version
        self._build = build
        self._build_release_date = build_release_date

    def process_connection_closed(self) -> None:
        """
        Indicate the connection has closed.

        Following a API <-> Terminal broken socket connection, this function is not called
        automatically but must be triggered by API client code.

        """
        for future in self._requests.get_futures():
            if not future.done():
                future.set_exception(ConnectionError("Terminal disconnected."))
        if self._is_mt5_connected.is_set():
            self._log.debug("`_is_mt5_connected` unset by `connectionClosed`.", LogColor.BLUE)
            self._is_mt5_connected.clear()

