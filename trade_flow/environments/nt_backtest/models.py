from typing import Tuple
from nautilus_trader.core.data import Data
from trade_flow.agents.sb3_agent import SB3Agent


class ModelUpdate(Data):
    def __init__(
        self,
        model: SB3Agent,
        hedge_ratio: float,
        std_action: Tuple,
        ts_init: int,
    ):
        super().__init__(ts_init=ts_init, ts_event=ts_init)
        self.model = model
        self.hedge_ratio = hedge_ratio
        self.std_action = std_action


class Action(Data):
    def __init__(
        self,
        instrument_id: str,
        action: Tuple,
        ts_init: int,
    ):
        super().__init__(ts_init=ts_init, ts_event=ts_init)
        self.instrument_id = instrument_id
        self.action = action


class RepeatedEventComplete(Exception):
    pass
