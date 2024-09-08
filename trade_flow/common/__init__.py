"""
The `common` subpackage provides generic/common parts for assembling the frameworks
various components.

More domain specific concepts are introduced above the `core` base layer. The
ID cache is implemented, a base `Clock` with `Test` and `Live`
implementations which can control many `Timer` instances.

Trading domain specific components for generating `Order` and `Identifier` objects,
common logging components, a high performance `Queue` and `UUID4` factory.

"""

from enum import Enum
from enum import unique
from trade_flow.common.logging import *
from trade_flow.common.types import *
from trade_flow.common.utils import *


@unique
class Environment(Enum):
    """
    Represents the environment context for a Nautilus system.
    """

    TRAIN = "train"
    BACKTEST = "backtest"
    SANDBOX = "sandbox"
    LIVE = "live"