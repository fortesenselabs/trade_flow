import numba
import numpy as np
import pandas as pd
import pandas_ta as ta
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer


@numba.njit
def features_engineering(
    df: pd.DataFrame, add_ta: bool = False, compress_features: bool = True
) -> dict:
    """
    This function creates the necessary datasets for algorithms
    by performing feature engineering, scaling, and PCA.

    Args:
        df (DataFrame): The input dataframe containing price data (including 'close', 'high', 'low').
        add_ta (bool): Whether to add technical analysis features. Defaults to False.
        compress_features (bool): Whether to apply PCA for dimensionality reduction. Defaults to True.

    Returns:
        dict: A dictionary containing the train, test, validation sets,
              along with their scaled and PCA-transformed versions.
    """

    original_df = df.copy()

    # Define the feature columns
    feature_columns = [
        "returns t-1",
        "mean returns 15",
        "mean returns 60",
        "volatility returns 15",
        "volatility returns 60",
    ]

    # Create new columns for returns and other features

    # Ensure returns column is in the dataframe
    df["returns"] = (df["close"] - df["close"].shift(1)) / df["close"].shift(1)
    df["sLow"] = (df["low"] - df["close"].shift(1)) / df["close"].shift(1)
    df["sHigh"] = (df["high"] - df["close"].shift(1)) / df["close"].shift(1)

    # Feature engineering
    df["returns t-1"] = df["returns"].shift(1)
    df["mean returns 15"] = df["returns"].rolling(15).mean().shift(1)
    df["mean returns 60"] = df["returns"].rolling(60).mean().shift(1)
    df["volatility returns 15"] = df["returns"].rolling(15).std().shift(1)
    df["volatility returns 60"] = df["returns"].rolling(60).std().shift(1)

    # Add technical analysis features if specified
    if add_ta:
        df = add_ta_features(df)
        feature_columns = df.columns.to_list()

    # Impute missing values using IterativeImputer (Multiple Imputation by Chained Equations)
    imputer = IterativeImputer(random_state=0)
    df[feature_columns + ["returns"]] = imputer.fit_transform(df[feature_columns + ["returns"]])
    print(df)

    # Splitting data into train, test, and validation sets
    split_train_test = int(0.70 * len(df))
    split_test_valid = int(0.90 * len(df))

    # Train set creation
    X_train = df[feature_columns].iloc[:split_train_test]
    y_train_reg = df["returns"].iloc[:split_train_test]
    y_train_cla = np.round(df["returns"].iloc[:split_train_test] + 0.5)

    # Test set creation
    X_test = df[feature_columns].iloc[split_train_test:split_test_valid]
    y_test_reg = df["returns"].iloc[split_train_test:split_test_valid]

    # Validation set creation
    X_val = df[feature_columns].iloc[split_test_valid:]
    y_val_reg = df["returns"].iloc[split_test_valid:]

    # Standardize the data
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    X_val_scaled = scaler.transform(X_val)

    # Use the Normalizer for scaling
    # normalizer = Normalizer(data=[{"name": "X_train", "data": X_train}])
    # normalizer.fit("StandardScale", feature_columns)
    # # norm.fit(settings["normalization_fit_type"], settings["features_name"], settings["normalization_fit_target"])]

    # # Get normalized data
    # X_train_scaled = normalizer.get_normalized_data(0)  # Get the scaled data
    # X_test_scaled = normalizer.get_normalized_data(1)  # Get scaled test data
    # X_val_scaled = normalizer.get_normalized_data(2)  # Get scaled validation data

    # Prepare the features dictionary
    features_dict = {
        "df": original_df,
        "processed_df": df,
        "feature_columns": feature_columns,
        "X_train": X_train,
        "X_test": X_test,
        "y_train_reg": y_train_reg,
        "y_train_cla": y_train_cla,
        "X_train_scaled": X_train_scaled,
        "split_train_test": split_train_test,
        "split_test_valid": split_test_valid,
        "X_test_scaled": X_test_scaled,
        "y_test_reg": y_test_reg,
        "X_val": X_val,
        "X_val_scaled": X_val_scaled,
        "y_val_reg": y_val_reg,
    }

    # Apply PCA if specified
    if compress_features:
        pca = PCA(n_components=3)
        X_train_pca = pca.fit_transform(X_train_scaled)
        X_test_pca = pca.transform(X_test_scaled)
        X_val_pca = pca.transform(X_val_scaled)

        features_dict["X_train_pca"] = X_train_pca
        features_dict["X_test_pca"] = X_test_pca
        features_dict["X_val_pca"] = X_val_pca

    # Return all relevant datasets as a dictionary for clarity and organization
    return features_dict


def add_ta_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds various technical analysis (TA) features to the provided DataFrame.

    This function calculates several technical indicators, including momentum,
    volatility, statistics, trend, volume, overlap, and performance indicators.
    The input DataFrame must include a "date" column for setting the index to
    a DatetimeIndex.

    References:
    - https://github.com/twopirllc/pandas-ta/blob/main/examples/AIExample.ipynb
    """

    # Create a copy of the DataFrame to avoid modifying the original
    features_df = df.copy()

    # VWAP requires the DataFrame index to be a DatetimeIndex.
    # Replace "datetime" with the appropriate column from your DataFrame

    features_df.set_index(pd.DatetimeIndex(features_df.index), inplace=True)
    try:
        features_df.drop(columns=[features_df.index.name], inplace=True)
    except KeyError:
        print(f"Column '{features_df.index.name}' does not exist in the DataFrame.")
    except Exception as e:
        print(f"An error occurred while dropping the column: {e}")

    # Calculate Returns and append to the features_df DataFrame
    # features_df.ta.log_return(cumulative=True, append=True)
    # features_df.ta.percent_return(cumulative=True, append=True)

    """ 
        Add TA Indicators
    """

    # Adding momentum indicators
    features_df.ta.mom(append=True)
    features_df.ta.rsi(append=True)
    features_df.ta.tsi(append=True)
    features_df.ta.er(append=True)
    features_df.ta.fisher(append=True)

    # Adding volatility indicators
    features_df.ta.true_range(append=True)
    features_df.ta.rvi(append=True)
    features_df.ta.bbands(append=True)
    features_df.ta.pdist(append=True)

    # Adding statistics indicators
    features_df.ta.skew(append=True)
    features_df.ta.kurtosis(append=True)
    features_df.ta.mad(append=True)
    features_df.ta.zscore(append=True)
    features_df.ta.entropy(append=True)

    # Adding trend indicators
    features_df.ta.adx(append=True)
    features_df.ta.dpo(lookahead=False, append=True)
    features_df.ta.psar(append=True)
    features_df.ta.long_run(append=True)
    features_df.ta.short_run(append=True)
    features_df.ta.qstick(append=True)

    # Adding volume indicators
    # features_df.ta.obv(append=True)

    # Adding overlap indicators
    features_df.ta.linreg(append=True)
    features_df.ta.supertrend(append=True)
    features_df.ta.hilo(append=True)
    features_df.ta.hlc3(append=True)
    features_df.ta.ohlc4(append=True)

    # Adding Simple Moving Averages (SMA)
    sma_windows = [2, 10, 15, 60]
    for ma_window in sma_windows:
        features_df.ta.sma(length=ma_window, sma=False, append=True)

    # Adding Exponential Moving Averages (EMA)
    ema_windows = [8, 21, 50]
    for ma_window in ema_windows:
        features_df.ta.ema(length=ma_window, sma=False, append=True)

    # Adding performance indicators
    # features_df.ta.percent_return(append=True)

    print("TA Columns Added")

    """ 
    #### Modify RSI (Relative Strength Index) Indicator

        - The RSI provides technical traders with signals about bullish and bearish price momentum, 
        and it is often plotted beneath the graph of an asset’s price.

        - An asset is usually considered overbought when the RSI is above 70 and oversold when it is below 30.

        - The RSI line crossing below the overbought line or above the oversold line is often seen by traders 
        as a signal to buy or sell.

        - The RSI works best in trading ranges rather than trending markets.
    """
    features_df["RSI_14"] = features_df[
        "RSI_14"
    ].round()  # Rounding RSI values to the nearest integer

    # Add Candle Stick Patterns
    features_df.ta.cdl_pattern(name="all", append=True)

    return features_df
