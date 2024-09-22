from decimal import Decimal

from trade_flow.core.correctness import Condition
from trade_flow.core.model import AssetClass
from trade_flow.core.model import CurrencyType
from trade_flow.core.model import InstrumentClass
from trade_flow.model.identifiers import InstrumentId
from trade_flow.model.identifiers import Symbol
from trade_flow.model.instruments.base import Instrument
from trade_flow.model.objects import Currency
from trade_flow.model.objects import Money
from trade_flow.model.objects import Price
from trade_flow.model.objects import Quantity


class CurrencyPair(Instrument):
    """
    Represents a generic currency pair instrument in a spot/cash market.

    Can represent both Fiat FX and Cryptocurrency pairs.

    Parameters
    ----------
    instrument_id : InstrumentId
        The instrument ID for the instrument.
    raw_symbol : Symbol
        The raw/local/native symbol for the instrument, assigned by the venue.
    base_currency : Currency
        The base currency.
    quote_currency : Currency
        The quote currency.
    price_precision : int
        The price decimal precision.
    size_precision : int
        The trading size decimal precision.
    price_increment : Price
        The minimum price increment (tick size).
    size_increment : Quantity
        The minimum size increment.
    margin_init : Decimal
        The initial (order) margin requirement in percentage of order value.
    margin_maint : Decimal
        The maintenance (position) margin in percentage of position value.
    maker_fee : Decimal
        The fee rate for liquidity makers as a percentage of order value.
    taker_fee : Decimal
        The fee rate for liquidity takers as a percentage of order value.
    ts_event : uint64_t
        UNIX timestamp (nanoseconds) when the data event occurred.
    ts_init : uint64_t
        UNIX timestamp (nanoseconds) when the data object was initialized.
    lot_size : Quantity, optional
        The rounded lot unit size.
    max_quantity : Quantity, optional
        The maximum allowable order quantity.
    min_quantity : Quantity, optional
        The minimum allowable order quantity.
    max_notional : Money, optional
        The maximum allowable order notional value.
    min_notional : Money, optional
        The minimum allowable order notional value.
    max_price : Price, optional
        The maximum allowable quoted price.
    min_price : Price, optional
        The minimum allowable quoted price.
    tick_scheme_name : str, optional
        The name of the tick scheme.
    info : dict[str, object], optional
        The additional instrument information.

    Raises
    ------
    ValueError
        If `tick_scheme_name` is not a valid string.
    ValueError
        If `price_precision` is negative (< 0).
    ValueError
        If `size_precision` is negative (< 0).
    ValueError
        If `price_increment` is not positive (> 0).
    ValueError
        If `size_increment` is not positive (> 0).
    ValueError
        If `price_precision` is not equal to price_increment.precision.
    ValueError
        If `size_increment` is not equal to size_increment.precision.
    ValueError
        If `lot_size` is not positive (> 0).
    ValueError
        If `max_quantity` is not positive (> 0).
    ValueError
        If `min_quantity` is negative (< 0).
    ValueError
        If `max_notional` is not positive (> 0).
    ValueError
        If `min_notional` is negative (< 0).
    ValueError
        If `max_price` is not positive (> 0).
    ValueError
        If `min_price` is negative (< 0).
    """

    def __init__(
        self,
        instrument_id: InstrumentId,
        raw_symbol: Symbol,
        base_currency: Currency,
        quote_currency: Currency,
        price_precision: int,
        size_precision: int,
        price_increment: Price,
        size_increment: Quantity,
        margin_init: Decimal,
        margin_maint: Decimal,
        maker_fee: Decimal,
        taker_fee: Decimal,
        ts_event: int,
        ts_init: int,
        lot_size: Quantity | None = None,
        max_quantity: Quantity | None = None,
        min_quantity: Quantity | None = None,
        max_notional: Money | None = None,
        min_notional: Money | None = None,
        max_price: Price | None = None,
        min_price: Price | None = None,
        tick_scheme_name: str = None,
        info: dict = None,
    ):
        # Determine asset class
        if (
            base_currency.currency_type == CurrencyType.CRYPTO
            or quote_currency.currency_type == CurrencyType.CRYPTO
        ):
            asset_class = AssetClass.CRYPTOCURRENCY
        else:
            asset_class = AssetClass.FX
        super().__init__(
            instrument_id=instrument_id,
            raw_symbol=raw_symbol,
            asset_class=asset_class,
            instrument_class=InstrumentClass.SPOT,
            quote_currency=quote_currency,
            is_inverse=False,
            price_precision=price_precision,
            size_precision=size_precision,
            price_increment=price_increment,
            size_increment=size_increment,
            multiplier=Quantity.from_int_c(1),
            lot_size=lot_size,
            max_quantity=max_quantity,
            min_quantity=min_quantity,
            max_notional=max_notional,
            min_notional=min_notional,
            max_price=max_price,
            min_price=min_price,
            margin_init=margin_init,
            margin_maint=margin_maint,
            maker_fee=maker_fee,
            taker_fee=taker_fee,
            tick_scheme_name=tick_scheme_name,
            ts_event=ts_event,
            ts_init=ts_init,
            info=info,
        )

        self.base_currency = base_currency

    def get_base_currency(self) -> Currency:
        """
        Return the instruments base currency.

        Returns
        -------
        Currency

        """
        return self.base_currency

    @staticmethod
    def from_dict_c(values: dict) -> "CurrencyPair":
        Condition.not_none(values, "values")
        lot_s: str = values["lot_size"]
        max_q: str = values["max_quantity"]
        min_q: str = values["min_quantity"]
        max_n: str = values["max_notional"]
        min_n: str = values["min_notional"]
        max_p: str = values["max_price"]
        min_p: str = values["min_price"]
        return CurrencyPair(
            instrument_id=InstrumentId.from_str_c(values["id"]),
            raw_symbol=Symbol(values["raw_symbol"]),
            base_currency=Currency.from_str_c(values["base_currency"]),
            quote_currency=Currency.from_str_c(values["quote_currency"]),
            price_precision=values["price_precision"],
            size_precision=values["size_precision"],
            price_increment=Price.from_str_c(values["price_increment"]),
            size_increment=Quantity.from_str_c(values["size_increment"]),
            lot_size=Quantity.from_str_c(lot_s) if lot_s is not None else None,
            max_quantity=Quantity.from_str_c(max_q) if max_q is not None else None,
            min_quantity=Quantity.from_str_c(min_q) if min_q is not None else None,
            max_notional=Money.from_str_c(max_n) if max_n is not None else None,
            min_notional=Money.from_str_c(min_n) if min_n is not None else None,
            max_price=Price.from_str_c(max_p) if max_p is not None else None,
            min_price=Price.from_str_c(min_p) if min_p is not None else None,
            margin_init=Decimal(values["margin_init"]),
            margin_maint=Decimal(values["margin_maint"]),
            maker_fee=Decimal(values["maker_fee"]),
            taker_fee=Decimal(values["taker_fee"]),
            ts_event=values["ts_event"],
            ts_init=values["ts_init"],
            info=values["info"],
        )

    @staticmethod
    def to_dict_c(obj: "CurrencyPair") -> dict:
        Condition.not_none(obj, "obj")
        return {
            "type": "CurrencyPair",
            "id": obj.id.to_str(),
            "raw_symbol": obj.raw_symbol.to_str(),
            "base_currency": obj.base_currency.code,
            "quote_currency": obj.quote_currency.code,
            "price_precision": obj.price_precision,
            "price_increment": str(obj.price_increment),
            "size_precision": obj.size_precision,
            "size_increment": str(obj.size_increment),
            "lot_size": str(obj.lot_size) if obj.lot_size is not None else None,
            "max_quantity": str(obj.max_quantity) if obj.max_quantity is not None else None,
            "min_quantity": str(obj.min_quantity) if obj.min_quantity is not None else None,
            "max_notional": str(obj.max_notional) if obj.max_notional is not None else None,
            "min_notional": str(obj.min_notional) if obj.min_notional is not None else None,
            "max_price": str(obj.max_price) if obj.max_price is not None else None,
            "min_price": str(obj.min_price) if obj.min_price is not None else None,
            "margin_init": str(obj.margin_init),
            "margin_maint": str(obj.margin_maint),
            "maker_fee": str(obj.maker_fee),
            "taker_fee": str(obj.taker_fee),
            "ts_event": obj.ts_event,
            "ts_init": obj.ts_init,
            "info": obj.info,
        }

    @staticmethod
    def from_dict(values: dict) -> "CurrencyPair":
        """
        Return an instrument from the given initialization values.

        Parameters
        ----------
        values : dict[str, object]
            The values to initialize the instrument with.

        Returns
        -------
        CurrencyPair

        """
        return CurrencyPair.from_dict_c(values)

    @staticmethod
    def to_dict(obj: "CurrencyPair") -> dict[str, object]:
        """
        Return a dictionary representation of this object.

        Returns
        -------
        dict[str, object]

        """
        return CurrencyPair.to_dict_c(obj)
