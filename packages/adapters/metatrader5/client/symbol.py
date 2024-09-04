import functools
from typing import List

from metatrader5.mt5api.symbol import SymbolInfo

from metatrader5.client.common import BaseMixin
from metatrader5.common import MT5Symbol, MT5SymbolDetails
from metatrader5.parsing.instruments import convert_symbol_info_to_mt5_symbol_details


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
            
            request.handle()
            
            return await self._await_request(request, 20)
        else:
            return await self._await_request(request, 20)

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
        symbol_infos: List[SymbolInfo],
    ) -> None:
        """
        Receive the full symbol's info This method will return all
        symbols matching the requested via MT5Client::req_symbol_details.
        """
        
        if not (request := self._requests.get(req_id=req_id)):
            return
        
        symbol_details = []
        for symbol_info in symbol_infos:
            symbol_details.append(convert_symbol_info_to_mt5_symbol_details(symbol_info))
        
        # request.result.append(symbol_details)
        request.future.set_result(symbol_details)

        await self.process_symbol_details_end(req_id=req_id)

    async def process_symbol_details_end(self, *, req_id: int) -> None:
        """
        After all symbols matching the request were returned, this method will mark
        the end of their reception.
        """
        self._end_request(req_id)
