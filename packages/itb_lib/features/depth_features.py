import numpy as np
from .rolling_agg import RollingAggregations


def generate_features_depth(df, use_differences=False):
    """
    Generate derived features from depth data by applying rolling aggregations.
    Original columns include:
    - gap: Difference between best bid and best ask prices.
    - bids_1, asks_1: Bid and ask data at the first level.
    - bids_2, asks_2: Bid and ask data at the second level.
    - bids_5, asks_5: Bid and ask data at the fifth level.
    - bids_10, asks_10: Bid and ask data at the tenth level.
    - bids_20, asks_20: Bid and ask data at the twentieth level.

    This function generates additional derived features by applying moving
    averages over specified windows (2, 5, 10) for the given columns, including:
    - gap: Mean values over the window.
    - bids_x and asks_x: Mean values for bid and ask prices over the window.

    Example of derived features:
    - gap_2, gap_5, gap_10
    - bids_1_2, bids_1_5, bids_1_10, asks_1_2, asks_1_5, asks_1_10
    - bids_2_2, bids_2_5, bids_2_10, asks_2_2, asks_2_5, asks_2_10
    - bids_5_2, bids_5_5, bids_5_10, asks_5_2, asks_5_5, asks_5_10
    - bids_10_2, bids_10_5, bids_10_10, asks_10_2, asks_10_5, asks_10_10
    - bids_20_2, bids_20_5, bids_20_10, asks_20_2, asks_20_5, asks_20_10

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing the depth data, which should include the columns
        'gap', 'bids_1', 'asks_1', 'bids_2', 'asks_2', 'bids_5', 'asks_5',
        'bids_10', 'asks_10', 'bids_20', and 'asks_20'.

    use_differences : bool, optional (default=False)
        If True, the function can be extended to generate features using differences.

    Returns:
    --------
    list of str
        List of new feature column names added to the DataFrame.
    """
    # Define the rolling windows for the aggregations
    windows = [2, 5, 10]
    base_window = 30

    features = []
    to_drop = []

    # Generate features for the 'gap' column
    to_drop += RollingAggregations.add_past_aggregations(
        df, "gap", np.nanmean, base_window, suffix=""
    )  # Base column
    features += RollingAggregations.add_past_aggregations(
        df, "gap", np.nanmean, windows, "", to_drop[-1], 100.0
    )

    # Generate features for bid and ask columns at various levels
    price_levels = [1, 2, 5, 10, 20]

    for level in price_levels:
        bid_col = f"bids_{level}"
        ask_col = f"asks_{level}"

        # Bid features
        to_drop += RollingAggregations.add_past_aggregations(
            df, bid_col, np.nanmean, base_window, suffix=""
        )
        features += RollingAggregations.add_past_aggregations(
            df, bid_col, np.nanmean, windows, "", to_drop[-1], 100.0
        )

        # Ask features
        to_drop += RollingAggregations.add_past_aggregations(
            df, ask_col, np.nanmean, base_window, suffix=""
        )
        features += RollingAggregations.add_past_aggregations(
            df, ask_col, np.nanmean, windows, "", to_drop[-1], 100.0
        )

    # Drop intermediate columns that were used for generating the features
    df.drop(columns=to_drop, inplace=True)

    return features
