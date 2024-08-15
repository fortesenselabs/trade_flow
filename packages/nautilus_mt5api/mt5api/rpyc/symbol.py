from dataclasses import dataclass, field
from typing import Optional, Dict

@dataclass
class SymbolInfo:
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

    @classmethod
    def from_dict(cls, data: Dict):
        """Create a SymbolInfo instance from a dictionary."""
        return cls(
            custom=data.get('custom', False),
            chart_mode=data.get('chart_mode', 0),
            select=data.get('select', True),
            visible=data.get('visible', True),
            session_deals=data.get('session_deals', 0),
            session_buy_orders=data.get('session_buy_orders', 0),
            session_sell_orders=data.get('session_sell_orders', 0),
            volume=data.get('volume', 0.0),
            volumehigh=data.get('volumehigh', 0.0),
            volumelow=data.get('volumelow', 0.0),
            time=data.get('time', 0),
            digits=data.get('digits', 0),
            spread=data.get('spread', 0),
            spread_float=data.get('spread_float', True),
            ticks_bookdepth=data.get('ticks_bookdepth', 0),
            trade_calc_mode=data.get('trade_calc_mode', 0),
            trade_mode=data.get('trade_mode', 0),
            start_time=data.get('start_time', 0),
            expiration_time=data.get('expiration_time', 0),
            trade_stops_level=data.get('trade_stops_level', 0),
            trade_freeze_level=data.get('trade_freeze_level', 0),
            trade_exemode=data.get('trade_exemode', 1),
            swap_mode=data.get('swap_mode', 1),
            swap_rollover3days=data.get('swap_rollover3days', 0),
            margin_hedged_use_leg=data.get('margin_hedged_use_leg', False),
            expiration_mode=data.get('expiration_mode', 7),
            filling_mode=data.get('filling_mode', 1),
            order_mode=data.get('order_mode', 127),
            order_gtc_mode=data.get('order_gtc_mode', 0),
            option_mode=data.get('option_mode', 0),
            option_right=data.get('option_right', 0),
            bid=data.get('bid', 0.0),
            bidhigh=data.get('bidhigh', 0.0),
            bidlow=data.get('bidlow', 0.0),
            ask=data.get('ask', 0.0),
            askhigh=data.get('askhigh', 0.0),
            asklow=data.get('asklow', 0.0),
            last=data.get('last', 0.0),
            lasthigh=data.get('lasthigh', 0.0),
            lastlow=data.get('lastlow', 0.0),
            volume_real=data.get('volume_real', 0.0),
            volumehigh_real=data.get('volumehigh_real', 0.0),
            volumelow_real=data.get('volumelow_real', 0.0),
            option_strike=data.get('option_strike', 0.0),
            point=data.get('point', 0.0),
            trade_tick_value=data.get('trade_tick_value', 0.0),
            trade_tick_value_profit=data.get('trade_tick_value_profit', 0.0),
            trade_tick_value_loss=data.get('trade_tick_value_loss', 0.0),
            trade_tick_size=data.get('trade_tick_size', 0.0),
            trade_contract_size=data.get('trade_contract_size', 0.0),
            trade_accrued_interest=data.get('trade_accrued_interest', 0.0),
            trade_face_value=data.get('trade_face_value', 0.0),
            trade_liquidity_rate=data.get('trade_liquidity_rate', 0.0),
            volume_min=data.get('volume_min', 0.0),
            volume_max=data.get('volume_max', 0.0),
            volume_step=data.get('volume_step', 0.0),
            volume_limit=data.get('volume_limit', 0.0),
            swap_long=data.get('swap_long', 0.0),
            swap_short=data.get('swap_short', 0.0),
            margin_initial=data.get('margin_initial', 0.0),
            margin_maintenance=data.get('margin_maintenance', 0.0),
            session_volume=data.get('session_volume', 0.0),
            session_turnover=data.get('session_turnover', 0.0),
            session_interest=data.get('session_interest', 0.0),
            session_buy_orders_volume=data.get('session_buy_orders_volume', 0.0),
            session_sell_orders_volume=data.get('session_sell_orders_volume', 0.0),
            session_open=data.get('session_open', 0.0),
            session_close=data.get('session_close', 0.0),
            session_aw=data.get('session_aw', 0.0),
            session_price_settlement=data.get('session_price_settlement', 0.0),
            session_price_limit_min=data.get('session_price_limit_min', 0.0),
            session_price_limit_max=data.get('session_price_limit_max', 0.0),
            margin_hedged=data.get('margin_hedged', 0.0),
            price_change=data.get('price_change', 0.0),
            price_volatility=data.get('price_volatility', 0.0),
            price_theoretical=data.get('price_theoretical', 0.0),
            price_greeks_delta=data.get('price_greeks_delta', 0.0),
            price_greeks_theta=data.get('price_greeks_theta', 0.0),
            price_greeks_gamma=data.get('price_greeks_gamma', 0.0),
            price_greeks_vega=data.get('price_greeks_vega', 0.0),
            price_greeks_rho=data.get('price_greeks_rho', 0.0),
            price_greeks_omega=data.get('price_greeks_omega', 0.0),
            price_sensitivity=data.get('price_sensitivity', 0.0),
            basis=data.get('basis'),
            currency_base=data.get('currency_base', ''),
            currency_profit=data.get('currency_profit', ''),
            currency_margin=data.get('currency_margin', ''),
            bank=data.get('bank'),
            description=data.get('description', ''),
            exchange=data.get('exchange'),
            formula=data.get('formula'),
            isin=data.get('isin'),
            name=data.get('name', ''),
            page=data.get('page'),
            path=data.get('path')
        )

    def as_dict(self) -> Dict:
        """Return a dictionary representation of the SymbolInfo instance."""
        return {
            'custom': self.custom,
            'chart_mode': self.chart_mode,
            'select': self.select,
            'visible': self.visible,
            'session_deals': self.session_deals,
            'session_buy_orders': self.session_buy_orders,
            'session_sell_orders': self.session_sell_orders,
            'volume': self.volume,
            'volumehigh': self.volumehigh,
            'volumelow': self.volumelow,
            'time': self.time,
            'digits': self.digits,
            'spread': self.spread,
            'spread_float': self.spread_float,
            'ticks_bookdepth': self.ticks_bookdepth,
            'trade_calc_mode': self.trade_calc_mode,
            'trade_mode': self.trade_mode,
            'start_time': self.start_time,
            'expiration_time': self.expiration_time,
            'trade_stops_level': self.trade_stops_level,
            'trade_freeze_level': self.trade_freeze_level,
            'trade_exemode': self.trade_exemode,
            'swap_mode': self.swap_mode,
            'swap_rollover3days': self.swap_rollover3days,
            'margin_hedged_use_leg': self.margin_hedged_use_leg,
            'expiration_mode': self.expiration_mode,
            'filling_mode': self.filling_mode,
            'order_mode': self.order_mode,
            'order_gtc_mode': self.order_gtc_mode,
            'option_mode': self.option_mode,
            'option_right': self.option_right,
            'bid': self.bid,
            'bidhigh': self.bidhigh,
            'bidlow': self.bidlow,
            'ask': self.ask,
            'askhigh': self.askhigh,
            'asklow': self.asklow,
            'last': self.last,
            'lasthigh': self.lasthigh,
            'lastlow': self.lastlow,
            'volume_real': self.volume_real,
            'volumehigh_real': self.volumehigh_real,
            'volumelow_real': self.volumelow_real,
            'option_strike': self.option_strike,
            'point': self.point,
            'trade_tick_value': self.trade_tick_value,
            'trade_tick_value_profit': self.trade_tick_value_profit,
            'trade_tick_value_loss': self.trade_tick_value_loss,
            'trade_tick_size': self.trade_tick_size,
            'trade_contract_size': self.trade_contract_size,
            'trade_accrued_interest': self.trade_accrued_interest,
            'trade_face_value': self.trade_face_value,
            'trade_liquidity_rate': self.trade_liquidity_rate,
            'volume_min': self.volume_min,
            'volume_max': self.volume_max,
            'volume_step': self.volume_step,
            'volume_limit': self.volume_limit,
            'swap_long': self.swap_long,
            'swap_short': self.swap_short,
            'margin_initial': self.margin_initial,
            'margin_maintenance': self.margin_maintenance,
            'session_volume': self.session_volume,
            'session_turnover': self.session_turnover,
            'session_interest': self.session_interest,
            'session_buy_orders_volume': self.session_buy_orders_volume,
            'session_sell_orders_volume': self.session_sell_orders_volume,
            'session_open': self.session_open,
            'session_close': self.session_close,
            'session_aw': self.session_aw,
            'session_price_settlement': self.session_price_settlement,
            'session_price_limit_min': self.session_price_limit_min,
            'session_price_limit_max': self.session_price_limit_max,
            'margin_hedged': self.margin_hedged,
            'price_change': self.price_change,
            'price_volatility': self.price_volatility,
            'price_theoretical': self.price_theoretical,
            'price_greeks_delta': self.price_greeks_delta,
            'price_greeks_theta': self.price_greeks_theta,
            'price_greeks_gamma': self.price_greeks_gamma,
            'price_greeks_vega': self.price_greeks_vega,
            'price_greeks_rho': self.price_greeks_rho,
            'price_greeks_omega': self.price_greeks_omega,
            'price_sensitivity': self.price_sensitivity,
            'basis': self.basis,
            'currency_base': self.currency_base,
            'currency_profit': self.currency_profit,
            'currency_margin': self.currency_margin,
            'bank': self.bank,
            'description': self.description,
            'exchange': self.exchange,
            'formula': self.formula,
            'isin': self.isin,
            'name': self.name,
            'page': self.page,
            'path': self.path
        }

    def __str__(self) -> str:
        """Return a string representation of the SymbolInfo instance."""
        return (f"SymbolInfo(custom={self.custom}, chart_mode={self.chart_mode}, select={self.select}, "
                f"visible={self.visible}, session_deals={self.session_deals}, "
                f"session_buy_orders={self.session_buy_orders}, session_sell_orders={self.session_sell_orders}, "
                f"volume={self.volume}, volumehigh={self.volumehigh}, volumelow={self.volumelow}, "
                f"time={self.time}, digits={self.digits}, spread={self.spread}, "
                f"spread_float={self.spread_float}, ticks_bookdepth={self.ticks_bookdepth}, "
                f"trade_calc_mode={self.trade_calc_mode}, trade_mode={self.trade_mode}, "
                f"start_time={self.start_time}, expiration_time={self.expiration_time}, "
                f"trade_stops_level={self.trade_stops_level}, trade_freeze_level={self.trade_freeze_level}, "
                f"trade_exemode={self.trade_exemode}, swap_mode={self.swap_mode}, "
                f"swap_rollover3days={self.swap_rollover3days}, margin_hedged_use_leg={self.margin_hedged_use_leg}, "
                f"expiration_mode={self.expiration_mode}, filling_mode={self.filling_mode}, "
                f"order_mode={self.order_mode}, order_gtc_mode={self.order_gtc_mode}, "
                f"option_mode={self.option_mode}, option_right={self.option_right}, bid={self.bid}, "
                f"bidhigh={self.bidhigh}, bidlow={self.bidlow}, ask={self.ask}, askhigh={self.askhigh}, "
                f"asklow={self.asklow}, last={self.last}, lasthigh={self.lasthigh}, lastlow={self.lastlow}, "
                f"volume_real={self.volume_real}, volumehigh_real={self.volumehigh_real}, "
                f"volumelow_real={self.volumelow_real}, option_strike={self.option_strike}, "
                f"point={self.point}, trade_tick_value={self.trade_tick_value}, "
                f"trade_tick_value_profit={self.trade_tick_value_profit}, trade_tick_value_loss={self.trade_tick_value_loss}, "
                f"trade_tick_size={self.trade_tick_size}, trade_contract_size={self.trade_contract_size}, "
                f"trade_accrued_interest={self.trade_accrued_interest}, trade_face_value={self.trade_face_value}, "
                f"trade_liquidity_rate={self.trade_liquidity_rate}, volume_min={self.volume_min}, "
                f"volume_max={self.volume_max}, volume_step={self.volume_step}, volume_limit={self.volume_limit}, "
                f"swap_long={self.swap_long}, swap_short={self.swap_short}, margin_initial={self.margin_initial}, "
                f"margin_maintenance={self.margin_maintenance}, session_volume={self.session_volume}, "
                f"session_turnover={self.session_turnover}, session_interest={self.session_interest}, "
                f"session_buy_orders_volume={self.session_buy_orders_volume}, "
                f"session_sell_orders_volume={self.session_sell_orders_volume}, session_open={self.session_open}, "
                f"session_close={self.session_close}, session_aw={self.session_aw}, "
                f"session_price_settlement={self.session_price_settlement}, session_price_limit_min={self.session_price_limit_min}, "
                f"session_price_limit_max={self.session_price_limit_max}, margin_hedged={self.margin_hedged}, "
                f"price_change={self.price_change}, price_volatility={self.price_volatility}, "
                f"price_theoretical={self.price_theoretical}, price_greeks_delta={self.price_greeks_delta}, "
                f"price_greeks_theta={self.price_greeks_theta}, price_greeks_gamma={self.price_greeks_gamma}, "
                f"price_greeks_vega={self.price_greeks_vega}, price_greeks_rho={self.price_greeks_rho}, "
                f"price_greeks_omega={self.price_greeks_omega}, price_sensitivity={self.price_sensitivity}, "
                f"basis={self.basis}, currency_base={self.currency_base}, currency_profit={self.currency_profit}, "
                f"currency_margin={self.currency_margin}, bank={self.bank}, description={self.description}, "
                f"exchange={self.exchange}, formula={self.formula}, isin={self.isin}, name={self.name}, "
                f"page={self.page}, path={self.path})")
