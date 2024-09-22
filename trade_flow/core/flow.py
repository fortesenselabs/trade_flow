from typing import Optional
from trade_flow.common import Logger, gen_config_dir


class Flow:

    def __init__(self, name: str) -> None:
        self.logger = Logger(name=__class__.__name__)
        self.namespace = "trade_flow"

        # Initialize VenueManager
        # self.venue_manager: Optional[VenueManager] = None

        # Initialize EnvironmentManager for training mode
        # self.env_manager: Optional[EnvironmentManager] = None

    @classmethod
    def from_file(cls, flow_name):
        config_dir = gen_config_dir(flow_name)
        self = cls(config_dir, flow_name)
        return self

    def run(self):
        # Initialize VenueManager
        # self.venue_manager = VenueManager()

        # Initialize EnvironmentManager for training mode
        # self.env_manager = EnvironmentManager(EnvironmentMode.TRAIN, self.venue_manager)
        self.logger.info("EnvironmentManager initialized and process started.")

    def parse_objective_function(self):
        """
        should be able to give the agent an objective:
        - The common notion for this is profit but profit is the ultimate goal for any trader.
           This represents an abstract concept from profit
            e.g for example a trader might be comfortable seeing short term trades than long term trades
           this can decide how long an agent holds a trade among other factors.
        """
        return

    def run(self):
        return


"""
    Check if objective_function is a file OR a str

    if it is a file, it is a custom objective function
    if it is a str, it would check pre-defined objective functions 
"""

# This can also be thought of as a strategy the agent needs to optimize for
#
# Also add task_manager to this
