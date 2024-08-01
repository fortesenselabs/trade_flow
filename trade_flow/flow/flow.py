from pathlib import Path
from flow.kubernetes_backend import KubernetesBackend
from commons.logging import Logger
from commons.utils import gen_config_dir


class Flow:

    def __init__(self, config_dir, network_name: str) -> None:
        self.logger = Logger(name=__class__.__name__)
        
        self.config_dir: Path = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.container_interface = KubernetesBackend(config_dir, network_name)
        self.namespace = "trade_flow"

    @classmethod
    def from_file(cls, flow_name):
        config_dir = gen_config_dir(flow_name)
        self = cls(config_dir, flow_name)
        return self
    
    def start_process(self):
        return
    
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