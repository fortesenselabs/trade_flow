import datetime
import re
import time
from decimal import Decimal

import pandas as pd
from ibapi.contract import ContractDetails

# fmt: off
from nautilus_trader.adapters.interactive_brokers.common import IBContract
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


from metatrader5.common import MT5Symbol
from metatrader5.common import MT5SymbolDetails


FUTURES_MONTH_TO_CODE: dict[str, str] = {
    "JAN": "F",
    "FEB": "G",
    "MAR": "H",
    "APR": "J",
    "MAY": "K",
    "JUN": "M",
    "JUL": "N",
    "AUG": "Q",
    "SEP": "U",
    "OCT": "V",
    "NOV": "X",
    "DEC": "Z",
}
FUTURES_CODE_TO_MONTH = dict(
    zip(FUTURES_MONTH_TO_CODE.values(), FUTURES_MONTH_TO_CODE.keys(), strict=False),
)

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
    "IBCFD",  # self named, in fact mapping to "SMART" when parsing
]
VENUES_CMDTY = ["IBCMDTY"]  # self named, in fact mapping to "SMART" when parsing

RE_CASH = re.compile(r"^(?P<symbol>[A-Z]{3})\/(?P<currency>[A-Z]{3})$")

RE_CFD_CASH = re.compile(r"^Forex\\(?P<currency>[A-Z]{6})$")
# 'Indexes\\SP500m'

def _extract_isin(details: MT5SymbolDetails) -> int:
    if details.secIdList:
        for tag_value in details.secIdList:
            if tag_value.tag == "ISIN":
                return tag_value.value
    raise ValueError("No ISIN found")


def _tick_size_to_precision(tick_size: float | Decimal) -> int:
    tick_size_str = f"{tick_size:.10f}"
    return len(tick_size_str.partition(".")[2].rstrip("0"))


def sec_type_to_asset_class(sec_type: str) -> AssetClass:
    sec_type =  sec_type if "INDICES" not in sec_type else "INDEXES"
    mapping = {
        "INDEXES": "INDEX",
        "FOREX": "FX",
        "METALS": "COMMODITY"
    }
    return asset_class_from_str(mapping.get(sec_type, sec_type))


def contract_details_to_mt5_symbol_info_details(details: ContractDetails) -> MT5SymbolDetails:
    details.contract = IBContract(**details.contract.__dict__)
    details = MT5SymbolDetails(**details.__dict__)
    return details


def parse_instrument(
    symbol_details: MT5SymbolDetails,
    strict_symbology: bool = False,
) -> Instrument:
    instrument_id = mt5_symbol_to_instrument_id(
        symbol=symbol_details.symbol,
        strict_symbology=strict_symbology,
    )

    return parse_cfd_contract(details=symbol_details, instrument_id=instrument_id)


def contract_details_to_dict(details: MT5SymbolDetails) -> dict:
    dict_details = details.dict().copy()
    dict_details["symbol"] = details.symbol.dict().copy()
    return dict_details


def parse_cfd_contract(
    details: MT5SymbolDetails,
    instrument_id: InstrumentId,
) -> Cfd:
    price_precision: int = details.digits
    size_precision: int = _tick_size_to_precision(details.volume_step)
    timestamp = details.time # time.time_ns()

    # TODO: add other types of CFDs here too
    if RE_CFD_CASH.match(details.path):
        return Cfd(
            instrument_id=instrument_id,
            raw_symbol=Symbol(details.symbol.symbol),
            asset_class=sec_type_to_asset_class(details.underSecType),
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
            info=contract_details_to_dict(details),
        )
    else:
        return Cfd(
            instrument_id=instrument_id,
            raw_symbol=Symbol(details.symbol.symbol),
            asset_class=sec_type_to_asset_class(details.underSecType),
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
            info=contract_details_to_dict(details),
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


def decade_digit(last_digit: str, contract: IBContract) -> int:
    if year := contract.lastTradeDateOrContractMonth[:4]:
        return int(year[2:3])
    elif int(last_digit) > int(repr(datetime.datetime.now().year)[-1]):
        return int(repr(datetime.datetime.now().year)[-2]) - 1
    else:
        return int(repr(datetime.datetime.now().year)[-2])


def mt5_symbol_to_instrument_id(
    symbol: MT5Symbol,
    strict_symbology: bool = False,
) -> InstrumentId:
    PyCondition.type(symbol, MT5Symbol, "MT5Symbol")

    if strict_symbology:
        return mt5_symbol_to_instrument_id_strict_symbology(symbol)
    else:
        return mt5_symbol_to_instrument_id_simplified_symbology(symbol)


def mt5_symbol_to_instrument_id_strict_symbology(symbol: MT5Symbol) -> InstrumentId:
    if symbol.secType == "CFD":
        symbol = f"{symbol.localSymbol}={symbol.secType}"
        venue = "IBCFD"
    elif symbol.secType == "CMDTY":
        symbol = f"{symbol.localSymbol}={symbol.secType}"
        venue = "IBCMDTY"
    else:
        symbol = f"{symbol.localSymbol}={symbol.secType}"
        venue = (symbol.primaryExchange or symbol.exchange).replace(".", "/")
    return InstrumentId.from_str(f"{symbol}.{venue}")


def mt5_symbol_to_instrument_id_simplified_symbology(  # noqa: C901 (too complex)
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


def instrument_id_to_ib_contract_strict_symbology(instrument_id: InstrumentId) -> IBContract:
    local_symbol, security_type = instrument_id.symbol.value.rsplit("=", 1)
    exchange = instrument_id.venue.value.replace("/", ".")
    if security_type == "STK":
        return IBContract(
            secType=security_type,
            exchange="SMART",
            primaryExchange=exchange,
            localSymbol=local_symbol,
        )
    elif security_type == "CFD":
        return IBContract(
            secType=security_type,
            exchange="SMART",
            localSymbol=local_symbol,  # by IB is a cfd's local symbol of STK with a "n" as tail, e.g. "NVDAn". "
        )
    elif security_type == "CMDTY":
        return IBContract(
            secType=security_type,
            exchange="SMART",
            localSymbol=local_symbol,
        )
    elif security_type == "IND":
        return IBContract(
            secType=security_type,
            exchange=exchange,
            localSymbol=local_symbol,
        )
    else:
        return IBContract(
            secType=security_type,
            exchange=exchange,
            localSymbol=local_symbol,
        )


def instrument_id_to_ib_contract_simplified_symbology(  # noqa: C901 (too complex)
    instrument_id: InstrumentId,
) -> IBContract:
    if instrument_id.venue.value in VENUES_CASH and (
        m := RE_CASH.match(instrument_id.symbol.value)
    ):
        return IBContract(
            secType="CASH",
            exchange=instrument_id.venue.value,
            localSymbol=f"{m['symbol']}.{m['currency']}",
        )
    elif instrument_id.venue.value in VENUES_CRYPTO and (
        m := RE_CRYPTO.match(instrument_id.symbol.value)
    ):
        return IBContract(
            secType="CRYPTO",
            exchange=instrument_id.venue.value,
            localSymbol=f"{m['symbol']}.{m['currency']}",
        )
    elif instrument_id.venue.value in VENUES_OPT and (
        m := RE_OPT.match(instrument_id.symbol.value)
    ):
        return IBContract(
            secType="OPT",
            exchange=instrument_id.venue.value,
            localSymbol=f"{m['symbol'].ljust(6)}{m['expiry']}{m['right']}{m['strike']}{m['decimal']}",
        )
    elif instrument_id.venue.value in VENUES_FUT:
        if m := RE_FUT.match(instrument_id.symbol.value):
            return IBContract(
                secType="FUT",
                exchange=instrument_id.venue.value,
                localSymbol=f"{m['symbol']}{m['month']}{m['year'][-1]}",
            )
        elif m := RE_FUT_UNDERLYING.match(instrument_id.symbol.value):
            return IBContract(
                secType="CONTFUT",
                exchange=instrument_id.venue.value,
                symbol=m["symbol"],
            )
        elif m := RE_FOP.match(instrument_id.symbol.value):
            return IBContract(
                secType="FOP",
                exchange=instrument_id.venue.value,
                localSymbol=f"{m['symbol']}{m['month']}{m['year'][-1]} {m['right']}{m['strike']}",
            )
        else:
            raise ValueError(f"Cannot parse {instrument_id}, use 2-digit year for FUT and FOP")
    elif instrument_id.venue.value in VENUES_CFD:
        if m := RE_CASH.match(instrument_id.symbol.value):
            return IBContract(
                secType="CFD",
                exchange="SMART",
                symbol=m["symbol"],
                localSymbol=f"{m['symbol']}.{m['currency']}",
            )
        else:
            return IBContract(
                secType="CFD",
                exchange="SMART",
                symbol=f"{instrument_id.symbol.value}".replace("-", " "),
            )
    elif instrument_id.venue.value in VENUES_CMDTY:
        return IBContract(
            secType="CMDTY",
            exchange="SMART",
            symbol=f"{instrument_id.symbol.value}".replace("-", " "),
        )
    elif str(instrument_id.symbol).startswith("^"):
        return IBContract(
            secType="IND",
            exchange=instrument_id.venue.value,
            localSymbol=instrument_id.symbol.value[1:],
        )

    # Default to Stock
    return IBContract(
        secType="STK",
        exchange="SMART",
        primaryExchange=instrument_id.venue.value,
        localSymbol=f"{instrument_id.symbol.value}".replace("-", " "),
    )
