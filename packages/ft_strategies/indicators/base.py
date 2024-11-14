from abc import ABC
import pandas as pd


class Indicator(ABC):
    """
    Base class for technical indicators. This class provides common functionalities like data validation
    and initialization for all derived indicators.

    Attributes:
    -----------
        df (pd.DataFrame): The input DataFrame containing OHLCV data and other relevant columns.
    """

    def __init__(self, df: pd.DataFrame):
        """
        Initialize the BaseIndicator with a DataFrame and perform data validation.

        Parameters:
        -----------
            df (pd.DataFrame): The input DataFrame for indicator calculations. The DataFrame contains 'high', 'low', and 'close' columns, with the date or timestamp as the index.
        """
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Data is not a DataFrame")

        # Basic column checks
        self.required_cols = {"open", "high", "low", "close"}
        if not self.required_cols.issubset(df.columns):
            raise ValueError(f"DataFrame must contain columns: {self.required_cols}")

        # Assign the DataFrame to the instance
        self.df = df

    def get_columns(self):
        """
        Return the columns available in the DataFrame.

        Returns:
            list: List of column names in the DataFrame.
        """
        return self.df.columns.tolist()

    def validate_column(self, column):
        """
        Validate if a column exists in the DataFrame.

        Parameters:
            column (str): Column name to check.

        Raises:
            ValueError: If the column is not in the DataFrame.
        """
        if column not in self.df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame.")

    def get_data_slice(self, columns):
        """
        Get a slice of the DataFrame with specified columns.

        Parameters:
            columns (list): List of columns to retrieve.

        Returns:
            pd.DataFrame: DataFrame with the specified columns.
        """
        self.validate_column_list(columns)
        return self.df[columns]

    def validate_column_list(self, columns):
        """
        Validate if a list of columns exists in the DataFrame.

        Parameters:
            columns (list): List of column names to check.

        Raises:
            ValueError: If any of the columns are not in the DataFrame.
        """
        for col in columns:
            self.validate_column(col)
