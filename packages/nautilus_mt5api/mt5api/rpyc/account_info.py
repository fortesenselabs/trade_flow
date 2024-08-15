from dataclasses import dataclass

@dataclass
class AccountInfo:
    login: int
    trade_mode: int
    leverage: int
    limit_orders: int
    margin_so_mode: int
    trade_allowed: bool
    trade_expert: bool
    margin_mode: int
    currency_digits: int
    fifo_close: bool
    balance: float
    credit: float
    profit: float
    equity: float
    margin: float
    margin_free: float
    margin_level: float
    margin_so_call: float
    margin_so_so: float
    margin_initial: float
    margin_maintenance: float
    assets: float
    liabilities: float
    commission_blocked: float
    server: str
    currency: str
    company: str

    @classmethod
    def from_dict(cls, data: dict):
        """Create an AccountInfo instance from a dictionary."""
        return cls(
            login=data.get('login'),
            trade_mode=data.get('trade_mode'),
            leverage=data.get('leverage'),
            limit_orders=data.get('limit_orders'),
            margin_so_mode=data.get('margin_so_mode'),
            trade_allowed=data.get('trade_allowed'),
            trade_expert=data.get('trade_expert'),
            margin_mode=data.get('margin_mode'),
            currency_digits=data.get('currency_digits'),
            fifo_close=data.get('fifo_close'),
            balance=data.get('balance'),
            credit=data.get('credit'),
            profit=data.get('profit'),
            equity=data.get('equity'),
            margin=data.get('margin'),
            margin_free=data.get('margin_free'),
            margin_level=data.get('margin_level'),
            margin_so_call=data.get('margin_so_call'),
            margin_so_so=data.get('margin_so_so'),
            margin_initial=data.get('margin_initial'),
            margin_maintenance=data.get('margin_maintenance'),
            assets=data.get('assets'),
            liabilities=data.get('liabilities'),
            commission_blocked=data.get('commission_blocked'),
            server=data.get('server'),
            currency=data.get('currency'),
            company=data.get('company'),
        )

    def _asdict(self):
        """Return a dictionary representation of the account information."""
        return {
            "login": self.login,
            "trade_mode": self.trade_mode,
            "leverage": self.leverage,
            "limit_orders": self.limit_orders,
            "margin_so_mode": self.margin_so_mode,
            "trade_allowed": self.trade_allowed,
            "trade_expert": self.trade_expert,
            "margin_mode": self.margin_mode,
            "currency_digits": self.currency_digits,
            "fifo_close": self.fifo_close,
            "balance": self.balance,
            "credit": self.credit,
            "profit": self.profit,
            "equity": self.equity,
            "margin": self.margin,
            "margin_free": self.margin_free,
            "margin_level": self.margin_level,
            "margin_so_call": self.margin_so_call,
            "margin_so_so": self.margin_so_so,
            "margin_initial": self.margin_initial,
            "margin_maintenance": self.margin_maintenance,
            "assets": self.assets,
            "liabilities": self.liabilities,
            "commission_blocked": self.commission_blocked,
            "server": self.server,
            "currency": self.currency,
            "company": self.company,
        }

    def __str__(self):
        """Return a string representation of the account information."""
        return (f"AccountInfo(login={self.login}, trade_mode={self.trade_mode}, leverage={self.leverage}, "
                f"limit_orders={self.limit_orders}, margin_so_mode={self.margin_so_mode}, "
                f"trade_allowed={self.trade_allowed}, trade_expert={self.trade_expert}, "
                f"margin_mode={self.margin_mode}, currency_digits={self.currency_digits}, "
                f"fifo_close={self.fifo_close}, balance={self.balance}, credit={self.credit}, "
                f"profit={self.profit}, equity={self.equity}, margin={self.margin}, "
                f"margin_free={self.margin_free}, margin_level={self.margin_level}, "
                f"margin_so_call={self.margin_so_call}, margin_so_so={self.margin_so_so}, "
                f"margin_initial={self.margin_initial}, margin_maintenance={self.margin_maintenance}, "
                f"assets={self.assets}, liabilities={self.liabilities}, "
                f"commission_blocked={self.commission_blocked}, server={self.server}, "
                f"currency={self.currency}, company={self.company})")