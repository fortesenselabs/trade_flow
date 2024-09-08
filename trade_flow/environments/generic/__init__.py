"""
Provides a Generic Environment
"""


def cli_help():
    return "Generic Environment"


from trade_flow.environments.generic.components.reward_scheme import RewardScheme
from trade_flow.environments.generic.components.action_scheme import ActionScheme
from trade_flow.environments.generic.components.observer import Observer
from trade_flow.environments.generic.components.stopper import Stopper
from trade_flow.environments.generic.components.informer import Informer
from trade_flow.environments.generic.components.renderer import Renderer
from trade_flow.environments.generic.components.venue import Venue

from trade_flow.environments.generic.environment import TradingEnvironment