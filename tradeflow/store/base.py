from abc import abstractmethod
from typing import List, Any, Optional


class Store:
    """
    Store Interface.
    """

    def __init__(self, store_name: str) -> None:
        self.store_name = store_name
        self.connection = None
        self.cursor = None

    @abstractmethod
    def connect(self):
        """Connect to the store."""
        raise NotImplementedError()

    @abstractmethod
    def close(self):
        """Close the store connection."""
        raise NotImplementedError()

    @abstractmethod
    def create(self, table_name: str, schema: str):
        """Create a table with the given schema."""
        raise NotImplementedError()

    @abstractmethod
    def insert(self, table_name: str, columns: str, values: List[Any]):
        """Insert a new record into the table."""
        raise NotImplementedError()

    def update(
        self, table_name: str, set_clause: str, condition: str, values: List[Any]
    ):
        """Update records in the table."""
        raise NotImplementedError()

    def find_by_id(
        self, table_name: str, id_column: str, id_value: Any
    ) -> Optional[Any]:
        """Find a record by ID."""
        raise NotImplementedError()

    def find_all(self, table_name: str) -> List[Any]:
        """Find all records in a table."""
        raise NotImplementedError()

    def delete_by_id(self, table_name: str, id_column: str, id_value: Any):
        """Delete a record by ID."""
        raise NotImplementedError()

    def delete_all(self, table_name: str):
        """Delete all records in a table."""
        raise NotImplementedError()

    def execute_custom_query(
        self, query: str, parameters: Optional[List[Any]] = None
    ) -> Any:
        """Execute a custom query."""
        raise NotImplementedError()
