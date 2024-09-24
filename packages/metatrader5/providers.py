import copy
from typing import Tuple

import pandas as pd
from trade_flow.adapters.metatrader5.mt5api.symbol import SymbolInfo


from nautilus_trader.common.providers import InstrumentProvider
from nautilus_trader.config import resolve_path
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments.base import Instrument

from trade_flow.adapters.metatrader5.client import MetaTrader5Client
from trade_flow.adapters.metatrader5.common import MT5Symbol, MT5SymbolDetails
from trade_flow.adapters.metatrader5.config import MetaTrader5InstrumentProviderConfig
from trade_flow.adapters.metatrader5.parsing.instruments import (
    instrument_id_to_mt5_symbol,
    parse_instrument,
)


class MetaTrader5InstrumentProvider(InstrumentProvider):
    """
    Provides a means of loading `Instrument` objects through MetaTrader 5.
    """

    def __init__(
        self,
        client: MetaTrader5Client,
        config: MetaTrader5InstrumentProviderConfig,
    ) -> None:
        """
        Initialize a new instance of the ``MetaTrader5InstrumentProvider`` class.

        Parameters
        ----------
        client : MetaTrader5Client
            The MetaTrader 5 client.
        config : MetaTrader5InstrumentProviderConfig
            The instrument provider config

        """
        super().__init__(config=config)

        # Settings
        self._load_symbols_on_start = (
            set(config.load_symbols) if config.load_symbols is not None else None
        )
        self._cache_validity_days = config.cache_validity_days
        # TODO: If cache_validity_days > 0 and Catalog is provided

        self._client = client
        self.config = config
        self.symbol_details: dict[str, MT5SymbolDetails] = {}
        self.symbol_id_to_instrument_id: dict[int, InstrumentId] = {}

    async def initialize(self) -> None:
        await super().initialize()
        # Trigger symbol loading only if `load_ids_on_start` is False and `load_symbols_on_start` is True
        if not self._load_ids_on_start and self._load_symbols_on_start:
            self._loaded = False
            self._loading = True
            await self.load_ids_async([])  # Asynchronously load symbols with an empty load_ids
            self._loading = False
            self._loaded = True

    async def load_all_async(self, filters: dict | None = None) -> None:
        await self.load_ids_async([])

    async def load_ids_async(
        self,
        instrument_ids: list[InstrumentId],
        filters: dict | None = None,
    ) -> None:
        # Parse and load InstrumentIds
        if self._load_ids_on_start:
            for instrument_id in [
                (InstrumentId.from_str(i) if isinstance(i, str) else i)
                for i in self._load_ids_on_start
            ]:
                await self.load_async(instrument_id)
        # Load MT5Symbols
        if self._load_symbols_on_start:
            for symbol in [
                (MT5Symbol(**c) if isinstance(c, dict) else c) for c in self._load_symbols_on_start
            ]:
                await self.load_async(symbol)

    async def get_symbol_details(
        self,
        symbol: MT5Symbol,
    ) -> list[MT5SymbolDetails]:
        try:
            details = await self._client.get_symbol_details(symbol=symbol)
            if not details:
                self._log.error(f"No symbol details returned for {symbol}.")
                return []
            [qualified] = details
            self._log.info(
                f"Symbol is {qualified.symbol.symbol}.",
            )
            self._log.debug(f"Got {details=}")
        except ValueError as e:
            self._log.error(f"No symbol details found for the given kwargs {symbol}, {e}")
            return []

        return details

    async def load_async(
        self,
        instrument_id: InstrumentId | MT5Symbol,
        filters: dict | None = None,
    ) -> None:
        """
        Search and load the instrument for the given MT5Symbol. It is important that
        the Symbol shall have enough parameters so only one match is returned.

        Parameters
        ----------
        instrument_id : MT5Symbol
            MetaTrader5's Symbol.
        filters : dict, optional
            Not applicable in this case.

        """
        if isinstance(instrument_id, InstrumentId):
            try:
                symbol = instrument_id_to_mt5_symbol(
                    instrument_id=instrument_id,
                    strict_symbology=self.config.strict_symbology,
                )
            except ValueError as e:
                self._log.error(
                    f"{self.config.strict_symbology=} failed to parse {instrument_id=}, {e}",
                )
                return
        elif isinstance(instrument_id, MT5Symbol):
            symbol = instrument_id
        else:
            self._log.error(f"Expected InstrumentId or MT5Symbol, received {instrument_id}")
            return

        self._log.debug(f"Attempting to find instrument for {symbol=}")
        symbol_details: list[MT5SymbolDetails]
        if not (symbol_details := await self.get_symbol_details(symbol)):
            return

        for details in copy.deepcopy(symbol_details):
            # details.symbol = MT5Symbol(symbol=details.name)
            # details = MT5SymbolDetails(**details.__dict__)
            self._log.debug(f"Attempting to create instrument from {details}")
            try:
                instrument: Instrument = parse_instrument(
                    symbol_details=details,
                    strict_symbology=self.config.strict_symbology,
                )
            except ValueError as e:
                self._log.error(f"{self.config.strict_symbology=} failed to parse {details=}, {e}")
                continue
            if self.config.filter_callable is not None:
                filter_callable = resolve_path(self.config.filter_callable)
                if not filter_callable(instrument):
                    continue
            self._log.info(f"Adding {instrument=} from MetaTrader5InstrumentProvider")
            self.add(instrument)
            self._client._cache.add_instrument(instrument)
            self.symbol_details[instrument.id.value] = details
            self.symbol_id_to_instrument_id[details.symbol.sym_id] = instrument.id

    async def find_with_symbol_id(self, symbol_id: int) -> Instrument:
        instrument_id = self.symbol_id_to_instrument_id.get(symbol_id)
        if not instrument_id:
            await self.load_async(MT5Symbol(sym_id=symbol_id))
            instrument_id = self.symbol_id_to_instrument_id.get(symbol_id)
        instrument = self.find(instrument_id)
        return instrument
