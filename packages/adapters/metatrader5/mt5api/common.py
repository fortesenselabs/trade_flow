from enum import Enum
import sys
import math

from decimal import Decimal
from .utils import Object, intMaxString, floatMaxString, decimalMaxString


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


class BarData(Object):
    """
        MT5 Bar Data Structure
    """
    def __init__(self):
        self.date = ""
        self.open = 0.
        self.high = 0.
        self.low = 0.
        self.close = 0.
        self.volume = UNSET_DECIMAL
        self.wap = UNSET_DECIMAL
        self.barCount = 0

    def __str__(self):
        return "Date: %s, Open: %s, High: %s, Low: %s, Close: %s, Volume: %s, WAP: %s, BarCount: %s" % (self.date, floatMaxString(self.open), 
            floatMaxString(self.high), floatMaxString(self.low), floatMaxString(self.close), 
            decimalMaxString(self.volume), decimalMaxString(self.wap), intMaxString(self.barCount))


# class RealTimeBar(Object):
#     def __init__(self, time = 0, endTime = -1, open_ = 0., high = 0., low = 0., close = 0., volume = UNSET_DECIMAL, wap = UNSET_DECIMAL, count = 0):
#         self.time = time
#         self.endTime = endTime
#         self.open_ = open_
#         self.high = high
#         self.low = low
#         self.close = close
#         self.volume = volume
#         self.wap = wap
#         self.count = count

#     def __str__(self):
#         return "Time: %s, Open: %s, High: %s, Low: %s, Close: %s, Volume: %s, WAP: %s, Count: %s" % (intMaxString(self.time), 
#             floatMaxString(self.open), floatMaxString(self.high), floatMaxString(self.low), 
#             floatMaxString(self.close), decimalMaxString(self.volume), decimalMaxString(self.wap), 
#             intMaxString(self.count))

