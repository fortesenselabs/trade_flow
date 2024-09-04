from enum import Enum
import sys
import math

from decimal import Decimal
from dataclasses import dataclass



NO_VALID_ID = -1
MAX_MSG_LEN = 0xFFFFFF # 16Mb - 1byte

UNSET_INTEGER = 2 ** 31 - 1
UNSET_DOUBLE = sys.float_info.max
UNSET_LONG = 2 ** 63 - 1
UNSET_DECIMAL = Decimal(2 ** 127 - 1)
DOUBLE_INFINITY = math.inf

INFINITY_STR = "Infinity"

TickerId = int
OrderId  = int
TagValueList = list

FaDataType = int
# FaDataTypeEnum = Enum("N/A", "GROUPS", "PROFILES", "ALIASES")

# MarketDataType = int
class MarketDataTypeEnum(Enum):
    NULL = "N/A"
    REALTIME = "REALTIME"
    FROZEN = "FROZEN"
    DELAYED = "DELAYED"

    def to_str(self) -> str:
        """Returns the string representation of the enum value."""
        return self.value


Liquidities = int
# LiquiditiesEnum = Enum("None", "Added", "Remove", "RoudedOut")

SetOfString = set
SetOfFloat = set
ListOfOrder = list
ListOfFamilyCode = list
ListOfContractDescription = list
ListOfDepthExchanges = list
ListOfNewsProviders = list
SmartComponentMap = dict
HistogramDataList = list
ListOfPriceIncrements = list
ListOfHistoricalTick = list
ListOfHistoricalTickBidAsk = list
ListOfHistoricalTickLast = list
ListOfHistoricalSessions = list



@dataclass
class BarData:
    time: int
    open_: float
    high: float
    low: float
    close: float
    tick_volume: float
    spread: float
    real_volume: float


@dataclass
class CommissionReport:
    """
    Class describing an commission report's definition.

    """
    execId = ""
    commission = 0. 
    currency = ""
    realizedPNL =  0.
    yield_ = 0.
    yieldRedemptionDate = 0  # YYYYMMDD format