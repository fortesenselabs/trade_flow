from dataclasses import dataclass
from typing import Literal, Optional
from ibapi.common import UNSET_DOUBLE # TODO: remove ibapi dependency 


@dataclass
class Order:
    """
    Class describing an order's definition.

    """
    pass


# TODO: fix this dataclass
class OrderState:
    def __init__(self):
        self.status= ""

        self.initMarginBefore= ""
        self.maintMarginBefore= ""
        self.equityWithLoanBefore= ""
        self.initMarginChange= ""
        self.maintMarginChange= ""
        self.equityWithLoanChange= ""
        self.initMarginAfter= ""
        self.maintMarginAfter= ""
        self.equityWithLoanAfter= ""

        self.commission = UNSET_DOUBLE      # type: float
        self.minCommission = UNSET_DOUBLE   # type: float
        self.maxCommission = UNSET_DOUBLE   # type: float
        self.commissionCurrency = ""
        self.warningText = ""
        self.completedTime = ""
        self.completedStatus = ""
