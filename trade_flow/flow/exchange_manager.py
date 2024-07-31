from typing import Optional

class DataClient:
    pass

class ExecutionClient:
    pass

class ExchangeManager:
    def __init__(self) -> None:
        self.data_manager: Optional[DataClient] = None
        self.execution_manager: Optional[ExecutionClient] = None
    pass