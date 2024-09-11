import re
from decimal import Decimal

import pandas as pd

from nautilus_trader.core.correctness import PyCondition
from nautilus_trader.model.enums import AssetClass
from nautilus_trader.model.enums import asset_class_from_str
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import Symbol
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.instruments import Cfd
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.objects import Currency
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity


from trade_flow.adapters.metatrader5.common import MT5Symbol
from trade_flow.adapters.metatrader5.common import MT5SymbolDetails
from trade_flow.adapters.metatrader5.mt5api.symbol import SymbolInfo


VENUES_CASH = ["IDEALPRO"]
VENUES_CRYPTO = ["PAXOS"]
VENUES_OPT = ["SMART"]
VENUES_FUT = [
    "CBOT",  # US
    "CME",  # US
    "COMEX",  # US
    "KCBT",  # US
    "MGE",  # US
    "NYMEX",  # US
    "NYBOT",  # US
    "SNFE",  # AU
]
VENUES_CFD = [
    "MT5CFD",  # self named, in fact mapping to "SMART" when parsing
]
VENUES_CMDTY = ["MT5CMDTY"]  # self named, in fact mapping to "SMART" when parsing

RE_CASH = re.compile(r"^(?P<symbol>[A-Z]{3})\/(?P<currency>[A-Z]{3})$")

RE_CFD_CASH = re.compile(r"^Forex\\(?P<currency>[A-Z]{6})$")
# 'Indexes\\SP500m'


def _tick_size_to_precision(tick_size: float | Decimal) -> int:
    tick_size_str = f"{tick_size:.10f}"
    return len(tick_size_str.partition(".")[2].rstrip("0"))


def sec_type_to_asset_class(sec_type: str) -> AssetClass:
    sec_type = sec_type if "INDICES" not in sec_type else "INDEXES"
    mapping = {"INDEXES": "INDEX", "FOREX": "FX", "METALS": "COMMODITY"}
    return asset_class_from_str(mapping.get(sec_type, sec_type))


def parse_instrument(
    symbol_details: MT5SymbolDetails,
    strict_symbology: bool = False,
) -> Instrument:
    instrument_id = mt5_symbol_to_instrument_id(
        symbol=symbol_details.symbol,
        strict_symbology=strict_symbology,
    )

    return parse_cfd_contract(details=symbol_details, instrument_id=instrument_id)


def symbol_details_to_dict(details: MT5SymbolDetails) -> dict:
    dict_details = details.dict().copy()
    dict_details["symbol"] = details.symbol.dict().copy()
    return dict_details


def parse_cfd_contract(
    details: MT5SymbolDetails,
    instrument_id: InstrumentId,
) -> Cfd:
    price_precision: int = details.digits
    size_precision: int = _tick_size_to_precision(details.volume_step)
    timestamp = details.time  # time.time_ns()

    # TODO: add other types of CFDs here too
    if RE_CFD_CASH.match(details.path):
        return Cfd(
            instrument_id=instrument_id,
            raw_symbol=Symbol(details.symbol.symbol),
            asset_class=sec_type_to_asset_class(details.under_sec_type),
            base_currency=Currency.from_str(details.currency_base),
            quote_currency=Currency.from_str(details.currency_profit),
            price_precision=price_precision,
            size_precision=size_precision,
            price_increment=Price(details.trade_tick_size, price_precision),
            size_increment=Quantity(details.volume_step, size_precision),
            lot_size=None,
            max_quantity=Quantity(details.volume_max, size_precision),
            min_quantity=Quantity(details.volume_min, size_precision),
            max_notional=None,
            min_notional=None,
            max_price=None,
            min_price=None,
            margin_init=Decimal(0),
            margin_maint=Decimal(0),
            maker_fee=Decimal(0),
            taker_fee=Decimal(0),
            ts_event=timestamp,
            ts_init=timestamp,
            info=symbol_details_to_dict(details),
        )
    else:
        return Cfd(
            instrument_id=instrument_id,
            raw_symbol=Symbol(details.symbol.symbol),
            asset_class=sec_type_to_asset_class(details.under_sec_type),
            quote_currency=Currency.from_str(details.currency_profit),
            price_precision=price_precision,
            size_precision=size_precision,
            price_increment=Price(details.trade_tick_size, price_precision),
            size_increment=Quantity(details.volume_step, size_precision),
            lot_size=None,
            max_quantity=Quantity(details.volume_max, size_precision),
            min_quantity=Quantity(details.volume_min, size_precision),
            max_notional=None,
            min_notional=None,
            max_price=None,
            min_price=None,
            margin_init=Decimal(0),
            margin_maint=Decimal(0),
            maker_fee=Decimal(0),
            taker_fee=Decimal(0),
            ts_event=timestamp,
            ts_init=timestamp,
            info=symbol_details_to_dict(details),
        )


def expiry_timestring_to_datetime(expiry: str) -> pd.Timestamp:
    """
    Most contract expirations are %Y%m%d format some exchanges have expirations in
    %Y%m%d %H:%M:%S %Z.
    """
    if len(expiry) == 8:
        return pd.Timestamp(expiry, tz="UTC")
    else:
        dt, tz = expiry.rsplit(" ", 1)
        ts = pd.Timestamp(dt, tz=tz)
        return ts.tz_convert("UTC")


def mt5_symbol_to_instrument_id(
    symbol: MT5Symbol,
    strict_symbology: bool = False,
) -> InstrumentId:
    PyCondition.type(symbol, MT5Symbol, "MT5Symbol")

    # if strict_symbology:
    #     return mt5_symbol_to_instrument_id_strict_symbology(symbol)
    # else:
    return mt5_symbol_to_instrument_id_simplified_symbology(symbol)


def mt5_symbol_to_instrument_id_simplified_symbology(
    mt5_symbol: MT5Symbol,
) -> InstrumentId:
    if len(mt5_symbol.symbol) > 0:
        symbol = mt5_symbol.symbol
        venue = mt5_symbol.broker
    else:
        symbol = None
        venue = None

    if symbol and venue:
        return InstrumentId(Symbol(symbol), Venue(venue))
    raise ValueError(f"Unknown {symbol=}")


def instrument_id_to_mt5_symbol(
    instrument_id: InstrumentId,
    strict_symbology: bool = False,
) -> MT5Symbol:
    PyCondition.type(instrument_id, InstrumentId, "InstrumentId")

    # if strict_symbology:
    #     return instrument_id_to_ib_contract_strict_symbology(instrument_id)
    # else:
    #     return instrument_id_to_ib_contract_simplified_symbology(instrument_id)
    mt_symbol = instrument_id.symbol.value.replace("/", "")
    mt_broker = instrument_id.venue.value.replace("/", ".")
    return MT5Symbol(symbol=mt_symbol, broker=mt_broker)


def convert_symbol_info_to_mt5_symbol_details(symbol_info: SymbolInfo) -> MT5SymbolDetails:
    return MT5SymbolDetails(
        under_sec_type=symbol_info.under_sec_type,
        symbol=MT5Symbol(
            symbol=symbol_info.symbol.symbol,
            broker=symbol_info.symbol.broker,
            sec_type=symbol_info.symbol.sec_type,
        ),
        custom=symbol_info.custom,
        chart_mode=symbol_info.chart_mode,
        select=symbol_info.select,
        visible=symbol_info.visible,
        session_deals=symbol_info.session_deals,
        session_buy_orders=symbol_info.session_buy_orders,
        session_sell_orders=symbol_info.session_sell_orders,
        volume=symbol_info.volume,
        volumehigh=symbol_info.volumehigh,
        volumelow=symbol_info.volumelow,
        time=symbol_info.time,
        digits=symbol_info.digits,
        spread=symbol_info.spread,
        spread_float=symbol_info.spread_float,
        ticks_bookdepth=symbol_info.ticks_bookdepth,
        trade_calc_mode=symbol_info.trade_calc_mode,
        trade_mode=symbol_info.trade_mode,
        start_time=symbol_info.start_time,
        expiration_time=symbol_info.expiration_time,
        trade_stops_level=symbol_info.trade_stops_level,
        trade_freeze_level=symbol_info.trade_freeze_level,
        trade_exemode=symbol_info.trade_exemode,
        swap_mode=symbol_info.swap_mode,
        swap_rollover3days=symbol_info.swap_rollover3days,
        margin_hedged_use_leg=symbol_info.margin_hedged_use_leg,
        expiration_mode=symbol_info.expiration_mode,
        filling_mode=symbol_info.filling_mode,
        order_mode=symbol_info.order_mode,
        order_gtc_mode=symbol_info.order_gtc_mode,
        option_mode=symbol_info.option_mode,
        option_right=symbol_info.option_right,
        bid=symbol_info.bid,
        bidhigh=symbol_info.bidhigh,
        bidlow=symbol_info.bidlow,
        ask=symbol_info.ask,
        askhigh=symbol_info.askhigh,
        asklow=symbol_info.asklow,
        last=symbol_info.last,
        lasthigh=symbol_info.lasthigh,
        lastlow=symbol_info.lastlow,
        volume_real=symbol_info.volume_real,
        volumehigh_real=symbol_info.volumehigh_real,
        volumelow_real=symbol_info.volumelow_real,
        option_strike=symbol_info.option_strike,
        point=symbol_info.point,
        trade_tick_value=symbol_info.trade_tick_value,
        trade_tick_value_profit=symbol_info.trade_tick_value_profit,
        trade_tick_value_loss=symbol_info.trade_tick_value_loss,
        trade_tick_size=symbol_info.trade_tick_size,
        trade_contract_size=symbol_info.trade_contract_size,
        trade_accrued_interest=symbol_info.trade_accrued_interest,
        trade_face_value=symbol_info.trade_face_value,
        trade_liquidity_rate=symbol_info.trade_liquidity_rate,
        volume_min=symbol_info.volume_min,
        volume_max=symbol_info.volume_max,
        volume_step=symbol_info.volume_step,
        volume_limit=symbol_info.volume_limit,
        swap_long=symbol_info.swap_long,
        swap_short=symbol_info.swap_short,
        margin_initial=symbol_info.margin_initial,
        margin_maintenance=symbol_info.margin_maintenance,
        session_volume=symbol_info.session_volume,
        session_turnover=symbol_info.session_turnover,
        session_interest=symbol_info.session_interest,
        session_buy_orders_volume=symbol_info.session_buy_orders_volume,
        session_sell_orders_volume=symbol_info.session_sell_orders_volume,
        session_open=symbol_info.session_open,
        session_close=symbol_info.session_close,
        session_aw=symbol_info.session_aw,
        session_price_settlement=symbol_info.session_price_settlement,
        session_price_limit_min=symbol_info.session_price_limit_min,
        session_price_limit_max=symbol_info.session_price_limit_max,
        margin_hedged=symbol_info.margin_hedged,
        price_change=symbol_info.price_change,
        price_volatility=symbol_info.price_volatility,
        price_theoretical=symbol_info.price_theoretical,
        price_greeks_delta=symbol_info.price_greeks_delta,
        price_greeks_theta=symbol_info.price_greeks_theta,
        price_greeks_gamma=symbol_info.price_greeks_gamma,
        price_greeks_vega=symbol_info.price_greeks_vega,
        price_greeks_rho=symbol_info.price_greeks_rho,
        price_greeks_omega=symbol_info.price_greeks_omega,
        price_sensitivity=symbol_info.price_sensitivity,
        basis=symbol_info.basis,
        currency_base=symbol_info.currency_base,
        currency_profit=symbol_info.currency_profit,
        currency_margin=symbol_info.currency_margin,
        bank=symbol_info.bank,
        description=symbol_info.description,
        exchange=symbol_info.exchange,
        formula=symbol_info.formula,
        isin=symbol_info.isin,
        name=symbol_info.name,
        page=symbol_info.page,
        path=symbol_info.path,
    )
