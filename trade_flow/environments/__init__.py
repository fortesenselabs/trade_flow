"""
The following are organized by system environment context:
- **Backtest:** Historical data with simulated venues()
    - Train: For training RL Agents
    - Test: For Testing RL Agents 
- **Sandbox:** Real-time data with simulated venues
- **Live:** Real-time data with live venues (paper trading or real accounts)
"""
from environments.environment import *
from environments.live import *
from environments.sandbox import *
from environments.backtest import *
from environments.train import *
from environments.environment_manager import *