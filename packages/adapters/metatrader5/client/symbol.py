import functools

from metatrader5.client.common import BaseMixin
from metatrader5.common import MT5Symbol
from metatrader5.common import MT5SymbolDetails


class MetaTrader5ClientSymbolMixin(BaseMixin):
    """
    Handles symbols (instruments) for the MetaTrader5Client.

    This class provides methods to request symbol details, matching symbols. 
    The MetaTrader5InstrumentProvider class uses methods defined in this class to request the data it needs.

    """

    async def get_symbol_details(self, symbol: MT5Symbol) -> list[MT5SymbolDetails] | None:
        """
        Request details for a specific symbol.

        Parameters
        ----------
        symbol : MT5Symbol
            The symbol for which details are requested.

        Returns
        -------
        MT5SymbolDetails | ``None``

        """

        name = str(symbol)
        if not (request := self._requests.get(name=name)):
            req_id = self._next_req_id()
            request = self._requests.add(
                req_id=req_id,
                name=name,
                handle=functools.partial(
                    self._mt5Client.req_symbol_details,
                    req_id=req_id,
                    symbol=symbol.symbol,
                ),
            )
            if not request:
                return None

            request.future.set_result(request.handle())
            return await self._await_request(request, 10)
        else:
            request.future.set_result(request.handle())
            return await self._await_request(request, 10)

    async def get_matching_symbols(self, pattern: str) -> list[MT5Symbol] | None:
        """
        Request symbols matching a specific pattern.

        Parameters
        ----------
        pattern : str
            The pattern to match for symbols.

        Returns
        -------
        list[MT5Symbol] | ``None``

        """
        name = f"MatchingSymbols-{pattern}"
        if not (request := self._requests.get(name=name)):
            req_id = self._next_req_id()
            request = self._requests.add(
                req_id=req_id,
                name=name,
                handle=functools.partial(
                    self._mt5Client.req_matching_symbols,
                    req_id=req_id,
                    pattern=pattern,
                ),
            )
            if not request:
                return None
            request.handle()
            return await self._await_request(request, 20)
        else:
            self._log.info(f"Request already exist for {request}")
            return None

    async def process_symbol_details(
        self,
        *,
        req_id: int,
        symbol_details: MT5SymbolDetails,
    ) -> None:
        """
        Receive the full symbol's info This method will return all
        symbols matching the requested via MT5Client::req_symbol_details.
        """
        if not (request := self._requests.get(req_id=req_id)):
            return
        request.result.append(symbol_details)

    async def process_symbol_details_end(self, *, req_id: int) -> None:
        """
        After all symbols matching the request were returned, this method will mark
        the end of their reception.
        """
        self._end_request(req_id)
