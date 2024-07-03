import numpy as np
import pandas as pd


def generate_labels_peaks(df: pd.DataFrame, config: dict):
    """
    Use peaks to generate binary labels based on horizon and normalized tolerance.

    Parameters:
    df (pd.DataFrame): DataFrame containing the data.
    config (dict): Configuration dictionary containing:
        - "horizon" (int): Horizon value to consider.
        - "columns" (str): Column name to use for peaks detection.
        - "tolerance" (float): Tolerance value for peaks detection.

    Returns:
    pd.DataFrame: DataFrame with added binary labels based on peaks detection.
    list: List of label column names added to the DataFrame.
    """
    init_column_number = len(df.columns)
    horizon = config.get("horizon", 1)

    column_name = config.get("columns", "close")
    if isinstance(column_name, list):
        column_name = column_name[0]

    if column_name not in df.columns:
        raise ValueError(f"Data column '{column_name}' not found in the DataFrame.")

    tolerance = config.get("tolerance", 0.2)

    # Normalize tolerance based on horizon
    normalized_disparity = (tolerance * horizon) / 10

    peaks_max, peaks_min = peaks_detection(df[column_name], normalized_disparity)

    print("peaks_min.shape", peaks_min.shape)
    print("peaks_max.shape", peaks_max.shape)
    print("peaks_max mean: ", np.mean(peaks_max))
    print("peaks_min mean: ", np.mean(peaks_min))

    # Extract indices from ndarray
    min_indices = peaks_min[:, 0].astype(int)
    max_indices = peaks_max[:, 0].astype(int)
    print("min_indices: ", min_indices)
    print("max_indices: ", max_indices)

    # Define thresholds
    large_thresholds = [0.5, 1.0, 1.5, 2.0, 2.5]
    small_thresholds = [0.1, 0.2, 0.3, 0.4]

    # Create binary labels based on thresholds and horizon
    for threshold in large_thresholds:
        df[f"high_{threshold}"] = (
            df[column_name].rolling(window=horizon).max()
            >= df[column_name] * (1 + threshold)
        ).astype(int)

    for threshold in small_thresholds:
        df[f"high_{threshold}"] = (
            df[column_name].rolling(window=horizon).max()
            <= df[column_name] * (1 + threshold)
        ).astype(int)

    for threshold in small_thresholds:
        df[f"low_{threshold}"] = (
            df[column_name].rolling(window=horizon).min()
            >= df[column_name] * (1 - threshold)
        ).astype(int)

    for threshold in large_thresholds:
        df[f"low_{threshold}"] = (
            df[column_name].rolling(window=horizon).min()
            <= df[column_name] * (1 - threshold)
        ).astype(int)

    labels = df.columns.to_list()[init_column_number:]
    print("labels: ", labels)

    return df, labels


def peaks_detection(
    data: list[float], delta: float = 0.01, x: list[float] = None
) -> tuple[np.ndarray, np.ndarray]:
    """
    Finds peaks and valleys in a data series.

    Args:
        data (list[float]): The data series.
        delta (float): The threshold for a peak or valley.
        x (list[float], optional): The x-axis values (optional). Defaults to None.

    Returns:
        tuple[np.ndarray, np.ndarray]: Two numpy arrays, the first containing the indices and values of the peaks,
               the second containing the indices and values of the valleys.
    """

    data_array = np.asarray(data)  # Ensure NumPy array for efficiency

    if x is None:
        x = np.arange(len(data_array))  # Create x-axis if not provided

    peaks: list[tuple[float, float]] = []
    valleys: list[tuple[float, float]] = []
    current_peak = -np.inf
    current_valley = np.inf
    peak_pos = np.nan
    valley_pos = np.nan
    looking_for_peak = True  # Flag to track search direction

    for i, this_value in enumerate(data_array):
        # Update current peak and valley values
        if looking_for_peak:
            if this_value > current_peak:
                current_peak = this_value
                peak_pos = i
            if this_value < current_peak - delta:
                if not np.isnan(peak_pos):
                    peaks.append((x[int(peak_pos)], current_peak))
                current_valley = this_value
                valley_pos = i
                looking_for_peak = False
        else:
            if this_value < current_valley:
                current_valley = this_value
                valley_pos = i
            if this_value > current_valley + delta:
                if not np.isnan(valley_pos):
                    valleys.append((x[int(valley_pos)], current_valley))
                current_peak = this_value
                peak_pos = i
                looking_for_peak = True

    return np.array(peaks), np.array(valleys)


# Example usage:
# df = pd.read_csv('your_data.csv')
# config = {"horizon": 5, "columns": "close", "tolerance": 0.05}
# df, labels = generate_labels_peaks(df, config)
