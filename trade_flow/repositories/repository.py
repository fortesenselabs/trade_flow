from abc import ABC, abstractmethod

class BaseRepository(ABC):
    """Abstract repository for storing models, data, and orders.

        ### Explanation:
        - The `BaseRepository` defines a contract for storing and retrieving models, data, and orders.
        - Specific storage implementations (e.g., database, cloud storage) can inherit from this interface and provide concrete implementations.
        - The methods are designed to be flexible, allowing storage of different data types and formats.
        - Additional methods for search, filtering, and version control can be added as needed.
    """

    @abstractmethod
    def store_model(self, model_name, model_data):
        """Stores a machine learning model.
        
        Args:
            model_name (str): Name of the model.
            model_data (object): Model data in any format (e.g., pickle, joblib).
        """
        pass

    @abstractmethod
    def load_model(self, model_name):
        """Loads a machine learning model.
        
        Args:
            model_name (str): Name of the model.
        
        Returns:
            object: Loaded model data.
        """
        pass

    @abstractmethod
    def store_data(self, data_name, data):
        """Stores data.
        
        Args:
            data_name (str): Name of the data.
            data (object): Data in any format (e.g., pandas DataFrame, numpy array).
        """
        pass

    @abstractmethod
    def load_data(self, data_name):
        """Loads data.
        
        Args:
            data_name (str): Name of the data.
        
        Returns:
            object: Loaded data.
        """
        pass

    @abstractmethod
    def store_order(self, order_id, order_data):
        """Stores an order.
        
        Args:
            order_id (str): Order ID.
            order_data (dict): Order data (e.g., symbol, quantity, price, type).
        """
        pass

    @abstractmethod
    def load_order(self, order_id):
        """Loads an order.
        
        Args:
            order_id (str): Order ID.
        
        Returns:
            dict: Order data.
        """
        pass

    @abstractmethod
    def delete_model(self, model_name):
        """Deletes a model.
        
        Args:
            model_name (str): Name of the model.
        """
        pass

    @abstractmethod
    def delete_data(self, data_name):
        """Deletes data.
        
        Args:
            data_name (str): Name of the data.
        """
        pass

    @abstractmethod
    def delete_order(self, order_id):
        """Deletes an order.
        
        Args:
            order_id (str): Order ID.
        """
        pass
