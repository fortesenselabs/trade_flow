from commons.logging import Logger


class TradeFlowEngine:

    def __init__(self) -> None:
        self.logger = Logger(name=__class__.__name__)
        pass

    def run(self):
        pass


"""
    Check if objective_function is a file OR a str

    if it is a file, it is a custom objective function
    if it is a str, it would check pre-defined objective functions 
"""

# This can also be thought of as a strategy the agent needs to optimize for   