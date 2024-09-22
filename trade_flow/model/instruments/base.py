from decimal import Decimal
import math
from trade_flow.core.data import Data
from trade_flow.core.correctness import Condition
from trade_flow.core.model import AssetClass, InstrumentClass
from trade_flow.model.functions import (
    asset_class_from_str,
    asset_class_to_str,
    instrument_class_from_str,
    instrument_class_to_str,
)
from trade_flow.model.identifiers import InstrumentId
from trade_flow.model.objects import Currency, Quantity, Price
from trade_flow.model.tick_scheme.base import TICK_SCHEMES, get_tick_scheme


EXPIRING_INSTRUMENT_TYPES = {
    InstrumentClass.FUTURE,
    InstrumentClass.FUTURE_SPREAD,
    InstrumentClass.OPTION,
    InstrumentClass.OPTION_SPREAD,
}

registry = {}


class Instrument(Data):
    """
    The base class for all instruments.

    Represents a tradable instrument. This class can be used to
    define an instrument, or act as a parent class for more specific instruments.

    Parameters
    ----------
    instrument_id : InstrumentId
        The instrument ID for the instrument.
    raw_symbol : Symbol
        The raw/local/native symbol for the instrument, assigned by the venue. The symbol used on an exchange/broker for a particular instrument.
        (e.g. AAPL, BTC, TSLA)
    asset_class : AssetClass
        The instrument asset class.
    instrument_class : InstrumentClass
        The instrument class.
    quote_currency : Currency
        The quote currency.
    is_inverse : bool
        If the instrument costing is inverse (quantity expressed in quote currency units).
    price_precision : int
        The price decimal precision. The precision the amount of the instrument is denoted with: BTC=8, AAPL=1
    size_precision : int
        The trading size decimal precision.
    size_increment : Price
        The minimum size increment.
    multiplier : Decimal
        The contract value multiplier (determines tick value).
    lot_size : Quantity, optional
        The rounded lot unit size (standard/board).
    margin_init : Decimal
        The initial (order) margin requirement in percentage of order value.
    margin_maint : Decimal
        The maintenance (position) margin in percentage of position value.
    maker_fee : Decimal
        The fee rate for liquidity makers as a percentage of order value (where 1.0 is 100%).
    taker_fee : Decimal
        The fee rate for liquidity takers as a percentage of order value (where 1.0 is 100%).
    ts_event : uint64_t
        UNIX timestamp (nanoseconds) when the data event occurred.
    ts_init : uint64_t
        UNIX timestamp (nanoseconds) when the data object was initialized.
    price_increment : Price, optional
        The minimum price increment (tick size).
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
        If `multiplier` is not positive (> 0).
    ValueError
        If `lot size` is not positive (> 0).
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
        raw_symbol: str,
        asset_class: AssetClass,
        instrument_class: InstrumentClass,
        quote_currency: Currency,
        is_inverse: bool,
        price_precision: int,
        size_precision: int,
        size_increment: Quantity,
        multiplier: Decimal,
        margin_init: Decimal,
        margin_maint: Decimal,
        maker_fee: Decimal,
        taker_fee: Decimal,
        ts_event: int,
        ts_init: int,
        price_increment: Price = None,
        lot_size: Quantity = None,
        max_quantity: Quantity = None,
        min_quantity: Quantity = None,
        max_notional: Decimal = None,
        min_notional: Decimal = None,
        max_price: Price = None,
        min_price: Price = None,
        tick_scheme_name: str = None,
        info: dict = None,
    ):
        Condition.not_negative_int(price_precision, "price_precision")
        Condition.not_negative_int(size_precision, "size_precision")
        Condition.positive(size_increment, "size_increment")
        Condition.equal(
            size_precision, size_increment.precision, "size_precision", "size_increment.precision"
        )
        Condition.positive(multiplier, "multiplier")

        if tick_scheme_name is not None:
            Condition.valid_string(tick_scheme_name, "tick_scheme_name")
            Condition.is_in(tick_scheme_name, TICK_SCHEMES, "tick_scheme_name", "TICK_SCHEMES")
        if price_increment is not None:
            Condition.positive(price_increment, "price_increment")
        if price_precision is not None and price_increment is not None:
            Condition.equal(
                price_precision,
                price_increment.precision,
                "price_precision",
                "price_increment.precision",
            )
        if lot_size is not None:
            Condition.positive(lot_size, "lot_size")
        if max_quantity is not None:
            Condition.positive(max_quantity, "max_quantity")
        if min_quantity is not None:
            Condition.not_negative(min_quantity, "min_quantity")
        if max_notional is not None:
            Condition.positive(max_notional, "max_notional")
        if min_notional is not None:
            Condition.not_negative(min_notional, "min_notional")
        if max_price is not None:
            Condition.positive(max_price, "max_price")
        if min_price is not None:
            Condition.not_negative(min_price, "min_price")
        Condition.type(margin_init, Decimal, "margin_init")
        Condition.not_negative(margin_init, "margin_init")
        Condition.type(margin_maint, Decimal, "margin_maint")
        Condition.not_negative(margin_maint, "margin_maint")
        Condition.type(maker_fee, Decimal, "maker_fee")
        Condition.type(taker_fee, Decimal, "taker_fee")

        self.id: InstrumentId = instrument_id
        self.raw_symbol: str = raw_symbol
        self.asset_class: AssetClass = asset_class
        self.instrument_class: InstrumentClass = instrument_class
        self.quote_currency: Currency = quote_currency
        self.is_inverse: bool = is_inverse
        self.price_precision: int = price_precision
        self.price_increment: Price = price_increment or Price(
            math.pow(10.0, -price_precision), price_precision
        )
        self.tick_scheme_name: str = tick_scheme_name
        self.size_precision: int = size_precision
        self.size_increment: Quantity = size_increment
        self.multiplier: Decimal = multiplier
        self.lot_size: Quantity = lot_size
        self.max_quantity: Quantity = max_quantity
        self.min_quantity: Quantity = min_quantity
        self.max_notional: Decimal = max_notional
        self.min_notional: Decimal = min_notional
        self.max_price: Price = max_price
        self.min_price: Price = min_price
        self.margin_init: Decimal = margin_init
        self.margin_maint: Decimal = margin_maint
        self.maker_fee: Decimal = maker_fee
        self.taker_fee: Decimal = taker_fee
        self.info: dict = info
        self.ts_event: int = ts_event
        self.ts_init: int = ts_init

        # Assign tick scheme if named
        if self.tick_scheme_name is not None:
            self._tick_scheme = get_tick_scheme(self.tick_scheme_name)

        registry[raw_symbol] = self

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Instrument) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:  # TODO: tick_scheme_name pending
        return (
            f"{type(self).__name__}"
            f"(id={self.id.to_str()}, "
            f"raw_symbol={self.raw_symbol}, "
            f"asset_class={asset_class_to_str(self.asset_class)}, "
            f"instrument_class={instrument_class_to_str(self.instrument_class)}, "
            f"quote_currency={self.quote_currency}, "
            f"is_inverse={self.is_inverse}, "
            f"price_precision={self.price_precision}, "
            f"price_increment={self.price_increment}, "
            f"size_precision={self.size_precision}, "
            f"size_increment={self.size_increment}, "
            f"multiplier={self.multiplier}, "
            f"lot_size={self.lot_size}, "
            f"margin_init={self.margin_init}, "
            f"margin_maint={self.margin_maint}, "
            f"maker_fee={self.maker_fee}, "
            f"taker_fee={self.taker_fee}, "
            f"info={self.info})"
        )

    @staticmethod
    def base_from_dict_c(values: dict) -> "Instrument":
        lot_s: str = values["lot_size"]
        max_q: str = values["max_quantity"]
        min_q: str = values["min_quantity"]
        max_n: str = values["max_notional"]
        min_n: str = values["min_notional"]
        max_p: str = values["max_price"]
        min_p: str = values["min_price"]
        return Instrument(
            instrument_id=InstrumentId.from_str_c(values["id"]),
            raw_symbol=Symbol(values["raw_symbol"]),
            asset_class=asset_class_from_str(values["asset_class"]),
            instrument_class=instrument_class_from_str(values["instrument_class"]),
            quote_currency=Currency.from_str_c(values["quote_currency"]),
            is_inverse=values["is_inverse"],
            price_precision=values["price_precision"],
            size_precision=values["size_precision"],
            price_increment=Price.from_str_c(values["price_increment"]),
            size_increment=Quantity.from_str_c(values["size_increment"]),
            multiplier=Quantity.from_str_c(values["multiplier"]),
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
    def base_to_dict_c(obj: "Instrument") -> dict:
        return {
            "type": "Instrument",
            "id": obj.id.to_str(),
            "raw_symbol": obj.raw_symbol.to_str(),
            "asset_class": asset_class_to_str(obj.asset_class),
            "instrument_class": instrument_class_to_str(obj.instrument_class),
            "quote_currency": obj.quote_currency.code,
            "is_inverse": obj.is_inverse,
            "price_precision": obj.price_precision,
            "price_increment": str(obj.price_increment),
            "size_precision": obj.size_precision,
            "size_increment": str(obj.size_increment),
            "multiplier": str(obj.multiplier),
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
    def base_from_dict(values: dict) -> "Instrument":
        """
        Return an instrument from the given initialization values.

        Parameters
        ----------
        values : dict[str, object]
            The values to initialize the instrument with.

        Returns
        -------
        Instrument

        """
        return Instrument.base_from_dict_c(values)

    @staticmethod
    def base_to_dict(obj: "Instrument"):
        """
        Return a dictionary representation of this object.

        Returns
        -------
        dict[str, object]

        """
        return Instrument.base_to_dict_c(obj)

    @property
    def symbol(self):
        """
        Return the instruments ticker symbol.

        Returns
        -------
        Symbol

        """
        return self.id.symbol

    @property
    def venue(self):
        """
        Return the instruments trading venue.

        Returns
        -------
        Venue

        """
        return self.id.venue

    def get_base_currency(self) -> Currency:
        """
        Return the instruments base currency (if applicable).

        Returns
        -------
        Currency or ``None``

        """
        return None

    def get_settlement_currency(self) -> Currency:
        """
        Return the currency used to settle a trade of the instrument.

        - Standard linear instruments = quote_currency
        - Inverse instruments = base_currency
        - Quanto instruments = settlement_currency

        Returns
        -------
        Currency

        """
        if self.is_inverse:
            return self.base_currency
        else:
            return self.quote_currency

    def make_price(self, value) -> Price:
        """
        Return a new price from the given value using the instruments price
        precision.

        Parameters
        ----------
        value : integer, float, str or Decimal
            The value of the price.

        Returns
        -------
        Price

        """
        rounded_value: float = round(float(value), self._min_price_increment_precision)
        return Price(rounded_value, precision=self.price_precision)

    def next_bid_price(self, value: float, num_ticks: int = 0) -> Price:
        """
        Return the price `n` bid ticks away from value.

        If a given price is between two ticks, n=0 will find the nearest bid tick.

        Parameters
        ----------
        value : float
            The reference value.
        num_ticks : int, default 0
            The number of ticks to move.

        Returns
        -------
        Price

        Raises
        ------
        ValueError
            If a tick scheme is not initialized.

        """
        if self._tick_scheme is None:
            raise ValueError(
                f"No tick scheme for instrument {self.id.to_str()}. "
                "You can specify a tick scheme by passing a `tick_scheme_name` at initialization."
            )

        return self._tick_scheme.next_bid_price(value=value, n=num_ticks)

    def next_ask_price(self, value: float, num_ticks: int = 0) -> Price:
        """
        Return the price `n` ask ticks away from value.

        If a given price is between two ticks, n=0 will find the nearest ask tick.

        Parameters
        ----------
        value : float
            The reference value.
        num_ticks : int, default 0
            The number of ticks to move.

        Returns
        -------
        Price

        Raises
        ------
        ValueError
            If a tick scheme is not initialized.

        """
        if self._tick_scheme is None:
            raise ValueError(
                f"No tick scheme for instrument {self.id.to_str()}. "
                "You can specify a tick scheme by passing a `tick_scheme_name` at initialization."
            )

        return self._tick_scheme.next_ask_price(value=value, n=num_ticks)

    def make_qty(self, value) -> Quantity:
        """
        Return a new quantity from the given value using the instruments size
        precision.

        Parameters
        ----------
        value : integer, float, str or Decimal
            The value of the quantity.

        Returns
        -------
        Quantity

        Raises
        ------
        ValueError
            If a non zero `value` is rounded to zero due to the instruments size increment or size precision.

        """

        # Check if original_value is greater than zero and rounded_value is "effectively" zero
        original_value: float = float(value)
        rounded_value: float = round(original_value, self._min_size_increment_precision)
        epsilon: float = 10 ** -(self._min_size_increment_precision + 1)

        if original_value > 0.0 and abs(rounded_value) < epsilon:
            raise ValueError(
                f"Invalid `value` for quantity: {value} was rounded to zero "
                f"due to size increment {self.size_increment} "
                f"and size precision {self.size_precision}",
            )
        return Quantity(rounded_value, precision=self.size_precision)

    def notional_value(
        self,
        quantity: Quantity,
        price: Price,
        use_quote_for_inverse: bool = False,
    ) -> Money:
        """
        Calculate the notional value.

        Result will be in quote currency for standard instruments, or base
        currency for inverse instruments.

        Parameters
        ----------
        quantity : Quantity
            The total quantity.
        price : Price
            The price for the calculation.
        use_quote_for_inverse : bool
            If inverse instrument calculations use quote currency (instead of base).

        Returns
        -------
        Money

        """
        Condition.not_none(quantity, "quantity")
        Condition.not_none(price, "price")

        if self.is_inverse:
            if use_quote_for_inverse:
                # Quantity is notional in quote currency
                return Money(quantity, self.quote_currency)
            return Money(
                quantity.as_f64_c() * float(self.multiplier) * (1.0 / price.as_f64_c()),
                self.base_currency,
            )
        else:
            return Money(
                quantity.as_f64_c() * float(self.multiplier) * price.as_f64_c(), self.quote_currency
            )

    def calculate_base_quantity(
        self,
        quantity: Quantity,
        last_px: Price,
    ) -> Quantity:
        """
        Calculate the base asset quantity from the given quote asset `quantity` and last price.

        Parameters
        ----------
        quantity : Quantity
            The quantity to convert from.
        last_px : Price
            The last price for the instrument.

        Returns
        -------
        Quantity

        """
        Condition.not_none(quantity, "quantity")

        return Quantity(quantity.as_f64_c() * (1.0 / last_px.as_f64_c()), self.size_precision)
