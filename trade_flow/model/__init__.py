from dataclasses import dataclass
from trade_flow.model.enums import *
from trade_flow.model.venues import *
from trade_flow.model.instruments import *
from trade_flow.model.orders import *
from trade_flow.model.slippage import *
from trade_flow.model.wallets import *


@dataclass
class TraderId:
    id: str
