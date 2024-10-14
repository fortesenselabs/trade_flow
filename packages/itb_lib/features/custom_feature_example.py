from pathlib import Path
from typing import Dict, List, Tuple, Union
import pandas as pd


"""
Example of a feature
"""


def custom_feature_example(
    df: pd.DataFrame, config: Dict[str, Union[str, float, int]]
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Generates a new feature by either adding or multiplying a numeric parameter to a specified column in the DataFrame.

    Parameters:
        df (pd.DataFrame): The input DataFrame containing the data.
        config (dict): A dictionary containing the configuration for the feature generation. It must include:
            - 'columns' (str): The name of the column to operate on.
            - 'function' (str): The operation to perform ('add' or 'mul').
            - 'parameter' (int or float): The numeric parameter to add or multiply.
            - 'names' (str, optional): The name of the output feature. If not provided, a default name will be generated.

    Raises:
        ValueError: If any of the required parameters are missing, of the wrong type, or if the specified column does not exist in the DataFrame.

    Returns:
        Tuple[pd.DataFrame, List[str]]: A tuple containing the modified DataFrame and a list of the names of the generated features.
    """

    column_name = config.get("columns")
    if not column_name:
        raise ValueError("The 'columns' parameter must be a non-empty string.")
    if not isinstance(column_name, str):
        raise ValueError(f"Wrong type for 'columns' parameter: {type(column_name)}. Expected str.")
    if column_name not in df.columns:
        raise ValueError(
            f"Column '{column_name}' does not exist in the input data. Existing columns: {df.columns.tolist()}"
        )

    function = config.get("function")
    if not isinstance(function, str):
        raise ValueError(f"Wrong type for 'function' parameter: {type(function)}. Expected str.")
    if function not in ["add", "mul"]:
        raise ValueError(f"Unknown function name '{function}'. Only 'add' or 'mul' are supported.")

    parameter = config.get("parameter")
    if not isinstance(parameter, (float, int)):
        raise ValueError(
            f"Wrong 'parameter' type: {type(parameter)}. Only numeric types are supported."
        )

    names = config.get("names", f"{column_name}_{function}")  # Default name generation

    # Perform the operation based on the specified function
    if function == "add":
        df[names] = df[column_name] + parameter
    elif function == "mul":
        df[names] = df[column_name] * parameter

    print(f"Finished computing feature '{names}'")

    return df, [names]
