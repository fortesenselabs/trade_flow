#
# This module was heavily lifted from https://github.com/nautechsystems/nautilus_trader and https://github.com/tensortrade-org/tensortrade
#
#

"""
The `core` subpackage groups core constants, functions and low-level components used
throughout the framework.

The main focus here is on efficiency and re-usability as this forms the base
layer of the entire framework. Message passing is a core design philosophy and
the base massage types are contained here.

A generic `FiniteStateMachine` operates with C-level enums, ensuring correct
state transitions for both domain entities and more complex components.

"""

from trade_flow.core.clock import *
from trade_flow.core.base import *
from trade_flow.core.component import *
from trade_flow.core.context import *
from trade_flow.core.exceptions import *
