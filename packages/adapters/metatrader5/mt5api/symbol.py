from dataclasses import dataclass
from typing import Literal, Optional

@dataclass
class Symbol:
    """
    Class describing an symbol's definition.

    Parameters
    ----------
    symbol: str
        Unique Symbol registered in Exchange.

    """
    sec_type: Literal[
        "CFD"
        "",
    ] = ""
    sym_id: int = 0
    symbol: str = ""
    broker: str = ""

@dataclass
class SymbolInfo:
    """
    SymbolInfo class 
    """

    symbol: Symbol | None = None
    under_sec_type: Optional[str] = None
    custom: bool = False
    chart_mode: int = 0
    select: bool = True
    visible: bool = True
    session_deals: int = 0
    session_buy_orders: int = 0
    session_sell_orders: int = 0
    volume: float = 0.0
    volumehigh: float = 0.0
    volumelow: float = 0.0
    time: int = 0
    digits: int = 0
    spread: int = 0
    spread_float: bool = True
    ticks_bookdepth: int = 0
    trade_calc_mode: int = 0
    trade_mode: int = 0
    start_time: int = 0
    expiration_time: int = 0
    trade_stops_level: int = 0
    trade_freeze_level: int = 0
    trade_exemode: int = 1
    swap_mode: int = 1
    swap_rollover3days: int = 0
    margin_hedged_use_leg: bool = False
    expiration_mode: int = 7
    filling_mode: int = 1
    order_mode: int = 127
    order_gtc_mode: int = 0
    option_mode: int = 0
    option_right: int = 0
    bid: float = 0.0
    bidhigh: float = 0.0
    bidlow: float = 0.0
    ask: float = 0.0
    askhigh: float = 0.0
    asklow: float = 0.0
    last: float = 0.0
    lasthigh: float = 0.0
    lastlow: float = 0.0
    volume_real: float = 0.0
    volumehigh_real: float = 0.0
    volumelow_real: float = 0.0
    option_strike: float = 0.0
    point: float = 0.0
    trade_tick_value: float = 0.0
    trade_tick_value_profit: float = 0.0
    trade_tick_value_loss: float = 0.0
    trade_tick_size: float = 0.0
    trade_contract_size: float = 0.0
    trade_accrued_interest: float = 0.0
    trade_face_value: float = 0.0
    trade_liquidity_rate: float = 0.0
    volume_min: float = 0.0
    volume_max: float = 0.0
    volume_step: float = 0.0
    volume_limit: float = 0.0
    swap_long: float = 0.0
    swap_short: float = 0.0
    margin_initial: float = 0.0
    margin_maintenance: float = 0.0
    session_volume: float = 0.0
    session_turnover: float = 0.0
    session_interest: float = 0.0
    session_buy_orders_volume: float = 0.0
    session_sell_orders_volume: float = 0.0
    session_open: float = 0.0
    session_close: float = 0.0
    session_aw: float = 0.0
    session_price_settlement: float = 0.0
    session_price_limit_min: float = 0.0
    session_price_limit_max: float = 0.0
    margin_hedged: float = 0.0
    price_change: float = 0.0
    price_volatility: float = 0.0
    price_theoretical: float = 0.0
    price_greeks_delta: float = 0.0
    price_greeks_theta: float = 0.0
    price_greeks_gamma: float = 0.0
    price_greeks_vega: float = 0.0
    price_greeks_rho: float = 0.0
    price_greeks_omega: float = 0.0
    price_sensitivity: float = 0.0
    basis: Optional[str] = None
    currency_base: str = ''
    currency_profit: str = ''
    currency_margin: str = ''
    bank: Optional[str] = None
    description: str = ''
    exchange: Optional[str] = None
    formula: Optional[str] = None
    isin: Optional[str] = None
    name: str = ''
    page: Optional[str] = None
    path: Optional[str] = None


def process_symbol_details(symbol_info: SymbolInfo, broker_server: str) -> SymbolInfo:
    return SymbolInfo(
        under_sec_type=symbol_info.path.split("\\")[0].upper(),
        symbol=Symbol(symbol=symbol_info.name, broker=broker_server),
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
        path=symbol_info.path
    )