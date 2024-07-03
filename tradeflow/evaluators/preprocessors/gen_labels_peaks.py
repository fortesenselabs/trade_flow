import numpy as np
import pandas as pd


def generate_labels_peaks(df: pd.DataFrame, config: dict):
    """
    use peaks to generate labels

    TODO:
    - make the label binary instead of multiclass
    - take horizon into account, which determines the future window used to compute all or one
    - normalize tolerance (translate tolerance into appropriate disparity level before)

       We use the following conventions and dimensions for generating binary labels:
    - Threshold is used to compare all values of some parameter, for example, 0.5 or 2.0 (sign is determined from the context)
    - Greater or less than the threshold. Note that the threshold has a sign which however is determined from the context
    - High or low column to compare with the threshold. Note that relative deviations from the close are used.
      Hence, high is always positive and low is always negative.
    - horizon which determines the future window used to compute all or one
    Thus, a general label is computed via the condition: [all or one] [relative high or low] [>= or <=] threshold
    However, we do not need all combinations of parameters but rather only some of them which are grouped as follows:
    - high >= large_threshold - at least one higher than threshold: 0.5, 1.0, 1.5, 2.0, 2.5
    - high <= small_threshold - all lower than threshold: 0.1, 0.2, 0.3, 0.4
    - low >= -small_threshold - all higher than threshold: 0.1, 0.2, 0.3, 0.4
    - low <= -large_threshold - at least one lower than (negative) threshold: 0.5, 1.0, 1.5, 2.0, 2.5
    Accordingly, we encode the labels as follows (60 is horizon):
    - high_xx (xx is threshold): for big xx - high_xx means one is larger, for small xx - all are less
    - low_xx (xx is threshold): for big xx - low_xx means one is larger, for small xx - all are less

    """
    init_column_number = len(df.columns)
    horizon = config.get("horizon", 1)

    column_name = config.get("columns", "close")
    if isinstance(column_name, list):
        column_name = column_name[0]

    if column_name not in df.columns:
        raise ValueError(f"Data column '{column_name}' not found in the DataFrame.")

    tolerance = config.get("tolerance", 0.2)  #

    disparity = tolerance

    peaks_max, peaks_min = peaks_detection(
        df[column_name],
        disparity,
    )
    print("peaks_min.shape", peaks_min.shape)
    print("peaks_max.shape", peaks_max.shape)
    print("peaks_max mean: ", np.mean(peaks_max))
    print("peaks_min mean: ", np.mean(peaks_min))

    # Extract indices from ndarray
    min_indices = peaks_min[:, 0].astype(int)
    max_indices = peaks_max[:, 0].astype(int)
    print("min_indices: ", min_indices)
    print("max_indices: ", max_indices)

    # Use numpy.select for conditional labeling
    conditions = [
        df.index.isin(min_indices),  # Condition for min peaks
        df.index.isin(max_indices),  # Condition for max peaks
    ]
    choices = [0, 1]  # Labels: 0 for buy, 1 for sell
    default = 2  # Default label: 2 for neutral
    df["label"] = np.select(conditions, choices, default)

    # Map numeric labels to string labels
    label_map = {0: "buy", 1: "sell", 2: "neutral"}
    df["peaks_" + str(disparity)] = df["label"].map(label_map)

    # Drop the intermediate 'label' column if not needed
    df.drop(columns="label", inplace=True)

    labels = df.columns.to_list()[init_column_number:]
    print("labels: ", labels)

    return df, labels


"""
# Define PEAKS Detection

This function detect peaks with a delta.

Choosing a default delta value for the peakdet function depends on the characteristics of your data and the desired level of peak/valley sensitivity. Here are some considerations:

- Data Scale: If your data values are on a large scale (e.g., stock prices in the thousands), a larger delta might be appropriate to avoid detecting insignificant fluctuations.
- Noise Level: If your data has a high level of noise, a larger delta might be necessary to filter out minor variations and focus on more prominent peaks and valleys.
- Desired Sensitivity: If you want to capture a broad range of peaks and valleys, a smaller delta would be suitable. However, this might also lead to detecting insignificant bumps or dips.

Here are some possible default values based on common scenarios:

- General Case: A reasonable starting point for many applications could be a delta value between 0.01 and 0.1. This range is a relative percentage of the data scale and can capture significant peaks and valleys without being overly sensitive to noise.
- Highly Scaled Data (e.g., Stock Prices): You might consider a delta between 1.0 and 10.0 for data with large values.
- Noisy Data: A delta between 0.05 and 0.2 could be a starting point for data with significant noise.

"""


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
    current_peak = np.inf
    current_valley = -np.inf
    peak_pos = np.nan
    valley_pos = np.nan
    looking_for_peak = True  # Flag to track search direction

    for i, this_value in enumerate(data_array):
        # Update current peak and valley values
        current_peak = max(current_peak, this_value)
        current_valley = min(current_valley, this_value)

        if looking_for_peak:
            if this_value < current_peak - delta:
                if not np.isnan(peak_pos):
                    peaks.append((x[int(peak_pos)], current_peak))
                # peaks.append((x[int(peak_pos)], current_peak))
                current_valley = this_value
                valley_pos = i
                looking_for_peak = False
        else:
            if this_value > current_valley + delta:
                if not np.isnan(valley_pos):
                    valleys.append((x[int(valley_pos)], current_valley))
                # valleys.append((x[int(valley_pos)], current_valley))
                current_peak = this_value
                peak_pos = i
                looking_for_peak = True

    return np.array(peaks), np.array(valleys)


# def generate_labels_peaks(df: pd.DataFrame, config: dict):
#     """
#     use peaks to generate labels
#     """

#     column_name = config.get("columns", "close")
#     if isinstance(column_name, list):
#         column_name = column_name[0]

#     if column_name not in df.columns:
#         raise ValueError(f"Data column '{column_name}' not found in the DataFrame.")

#     disparity = config.get(
#         "tolerance", 0.045
#     )  # 0.025, 0.045, 0.065, 0.075, 0.085, 0.095, 0.1

#     peaks_max, peaks_min = peaks_detection(
#         df[column_name],
#         disparity,
#     )
#     print("peaks_max mean: ", np.mean(peaks_max))
#     print("peaks_min mean: ", np.mean(peaks_min))

#     df["peaks"] = df[column_name]

#     labels = []
#     for i, _ in enumerate(df[column_name]):  # Iterate through data indices
#         if any(idx == i for idx, _ in peaks_min):
#             labels.append(0)  # Buy signal if peak min
#         elif any(idx == i for idx, _ in peaks_max):
#             labels.append(1)  # Sell signal if peak max
#         else:
#             labels.append(2)  # Neutral otherwise

#     print("labels done")

#     label_map = {0: "buy", 1: "sell", 2: "neutral"}
#     labels = [label_map[label] for label in labels]
#     df["peaks"] = labels

#     init_column_number = len(df.columns)
#     labels = df.columns.to_list()[init_column_number:]

#     return df, labels
