"""
The following are organized by system environment context:
- **Backtest:** Historical data with simulated venues()
    - Train: For training RL Agents
    - Test: For Testing RL Agents 
- **Sandbox:** Real-time data with simulated venues
- **Live:** Real-time data with live venues (paper trading or real accounts)
"""
from trade_flow.environments.environment import *
from trade_flow.environments.live import *
from trade_flow.environments.sandbox import *
from trade_flow.environments.backtest import *
from trade_flow.environments.train import *
from trade_flow.environments.environment_manager import *