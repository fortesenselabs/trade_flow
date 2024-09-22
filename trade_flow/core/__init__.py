#
# This module was heavily lifted from https://github.com/nautechsystems/nautilus_trader and https://github.com/tensortrade-org/tensortrade
#
#

"""Responsible for the basic classes in the project.

The `core` subpackage groups core constants, functions and low-level components used
throughout the framework.

The main focus here is on efficiency and re-usability as this forms the base
layer of the entire framework. Message passing is a core design philosophy and
the base massage types are contained here.

A generic `FiniteStateMachine` operates with C-level enums, ensuring correct
state transitions for both domain entities and more complex components.

Attributes
----------
global_clock : `Clock`
    A clock that provides a global reference for all objects that share a
    timeline.

"""

from trade_flow.core.clock import *
from trade_flow.core.uuid import *
from trade_flow.core.component import *
from trade_flow.core.context import *
from trade_flow.core.exceptions import *
from trade_flow.core.registry import *
from trade_flow.core.data import *
