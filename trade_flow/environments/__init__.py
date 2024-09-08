# This module for everything related to environments and their exchanges/brokers.
#
# This module was heavily lifted from https://github.com/tensortrade-org/tensortrade
#
# The following are organized by system environment context:
# - Train: Historical data with simulated venues For training RL Agents
# - **Backtest:** Historical data with simulated venues for testing RL Agents
# - **Sandbox:** Real-time data with simulated venues
# - **Live:** Real-time data with live venues (paper trading or real accounts)

from trade_flow.environments import generic
from trade_flow.environments import default
