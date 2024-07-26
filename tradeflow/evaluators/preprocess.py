import pandas as pd
import pandas_ta as ta
from sklearn.preprocessing import StandardScaler, MinMaxScaler


from typing import List

# Checkout the following: https://gist.github.com/niquedegraaff/8c2f45dc73519458afeae14b0096d719
# https://github.com/joshyattridge/smart-money-concepts
# git@github.com:rabichawila/smart-money-py.git

def get_data(markets_target: list, data: List[pd.DataFrame]):
    result = []

    for i, value in enumerate(data):
        if "date" not in value.columns:
            value["date"] = value.index

        value["date"] = pd.to_datetime(value["date"], format="%Y-%m-%d %H:%M:%S")
        value.set_index("date", inplace=True)

        result.append({"name": markets_target[i], "data": value})

    return result


def add_ta_features(df: pd.DataFrame) -> pd.DataFrame:
    features_df = df.copy()

    # VWAP requires the DataFrame index to be a DatetimeIndex.
    # Replace "datetime" with the appropriate column from your DataFrame
    features_df.set_index(pd.DatetimeIndex(features_df["date"]), inplace=True)
    features_df.drop(columns=["date"], inplace=True)

    # Calculate Returns and append to the features_df DataFrame
    # features_df.ta.log_return(cumulative=True, append=True)
    # features_df.ta.percent_return(cumulative=True, append=True)

    # https://twopirllc.github.io/pandas-ta/#momentum-41
    #
    # momentum indicators
    features_df.ta.mom(append=True)
    features_df.ta.rsi(append=True)
    features_df.ta.tsi(append=True)
    features_df.ta.er(append=True)
    features_df.ta.fisher(append=True)

    # volatility indicators
    features_df.ta.true_range(append=True)
    features_df.ta.rvi(append=True)
    features_df.ta.bbands(append=True)
    features_df.ta.pdist(append=True)

    # statistics indicators
    features_df.ta.skew(append=True)
    features_df.ta.kurtosis(append=True)
    features_df.ta.mad(append=True)
    features_df.ta.zscore(append=True)
    features_df.ta.entropy(append=True)

    # trend indicators
    features_df.ta.adx(append=True)
    features_df.ta.dpo(lookahead=False, append=True)
    features_df.ta.psar(append=True)
    features_df.ta.long_run(append=True)
    features_df.ta.short_run(append=True)
    features_df.ta.qstick(append=True)

    # volume indicators
    # features_df.ta.obv(append=True)

    # overlap indicators
    features_df.ta.linreg(append=True)
    features_df.ta.supertrend(append=True)
    features_df.ta.hilo(append=True)
    features_df.ta.hlc3(append=True)
    features_df.ta.ohlc4(append=True)

    # sma_windows = [1, 5, 10, 15, 60]
    sma_windows = [2, 10, 15, 60]
    for ma_window in sma_windows:
        features_df.ta.sma(length=ma_window, sma=False, append=True)

    ema_windows = [8, 21, 50]
    for ma_window in ema_windows:
        features_df.ta.ema(length=ma_window, sma=False, append=True)

    # performance indicators
    features_df.ta.percent_return(append=True)

    features_df["RSI_14"] = features_df["RSI_14"].round()  # 2

    features_df.ta.cdl_pattern(name="all", append=True)

    print("TA Columns Added")
    return features_df


class Normalizer:
    """
    A class for normalizing market data while preserving the original data.
    """

    def __init__(self, data):
        """
        Initializes the Normalizer class with market data.

        Args:
            data (list[dict]): A list of dictionaries, where each dictionary represents a market
                               with keys like "name" and "data" (containing market data).
        """
        self.__market_names = [e["name"] for e in data]
        self.__original_data = [
            e["data"] for e in data
        ]  # TODO: Deep copy to preserve original data
        self.__normalized_data = None  # Stores normalized data after fit is called

    def __normalize(self, target, numerical_data, scaler_func):
        """
        Normalizes data using the provided scaler function for specific target markets.

        Args:
            target (str): The target market(s) to normalize ("all" or a list of market names).
            numerical_data (list[pd.DataFrame]): A list of DataFrames containing numerical data for each market.
            scaler_func (callable): A function that performs data scaling (e.g., MinMaxScaler.fit_transform).
        """
        normalized_markets = []
        if target == "all":
            for market in numerical_data:
                columns = market.columns
                market_scaled = scaler_func(market)
                market_scaled = pd.DataFrame(market_scaled, columns=columns)
                normalized_markets.append(market_scaled)
        else:
            for market_name, market in zip(self.__market_names, numerical_data):
                if market_name in target:
                    columns = market.columns
                    market_scaled = scaler_func(market)
                    market_scaled = pd.DataFrame(market_scaled, columns=columns)
                    normalized_markets.append(market_scaled)

        return normalized_markets

    def fit(self, norm_type, features_list, target="all"):
        """
        Performs data normalization based on the specified type, features, and target market(s).

        Args:
            norm_type (str): The type of normalization to perform ("MinMax", "StandarScale", "Normalizer_l1", or "Normalizer_l2").
            features_list (list): A list of feature names to consider for normalization.
            target (str, optional): The target market(s) to normalize ("all" or a list of market names). Defaults to "all".

        Raises:
            ValueError: If an invalid normalization type is provided.
        """
        # Extract numerical data for the specified features
        numerical_data = [
            market[features_list]._get_numeric_data() for market in self.__original_data
        ]

        if norm_type == "MinMax":
            print(f"Performing MinMax Normalization on {target}.")
            scaler_func = MinMaxScaler().fit_transform
            self.__normalized_data = self.__normalize(
                target, numerical_data, scaler_func
            )
        elif norm_type == "StandarScale":
            print(f"Performing StandarScale Normalization on {target}.")
            scaler_func = StandardScaler().fit_transform
            self.__normalized_data = self.__normalize(
                target, numerical_data, scaler_func
            )
        elif norm_type.startswith("Normalizer"):
            norm_value = norm_type.split("_")[
                -1
            ]  # Extract l1 or l2 from "Normalizer_l1" or "Normalizer_l2"
            if norm_value not in ("l1", "l2"):
                raise ValueError(
                    "Invalid norm type for Normalizer. Must be 'l1' or 'l2'."
                )
            print(f"Performing Normalizer (norm={norm_value}) on {target}.")
            scaler_func = Normalizer(norm=norm_value).fit_transform
            self.__normalized_data = self.__normalize(
                target, numerical_data, scaler_func
            )
        else:
            raise ValueError(f"Invalid normalization type: {norm_type}")

    def get_normalized_data(self, idx: int = 0):
        """
        Returns the normalized data if normalization has been performed, otherwise raises an error.

        Args:
            idx (int): The location/index of the normalized data.

        Raises:
            RuntimeError: If data has not been normalized yet.
            IndexError: If the index is out of range.
        """
        if self.__normalized_data is None:
            raise RuntimeError(
                "Data has not been normalized yet. Please call 'fit' first."
            )

        if idx < 0 or idx >= len(self.__normalized_data):
            raise IndexError("Index out of range.")

        if idx is None:
            return self.__normalized_data

        return self.__normalized_data[idx]

    def get_original_data(self):
        """
        Returns the original, un-normalized data.
        """
        return self.__original_data.copy


class MarketLabeler:
    """
    A class for labeling market data with buy, sell, or neutral signals based on peak information.
    """

    def __init__(self, peaks_max, peaks_min):
        """
        Initializes the MarketLabeler with peak data.

        Args:
            peaks_max (list): A list of tuples representing peak maxima (index, value).
            peaks_min (list): A list of tuples representing peak minima (index, value).
        """
        self.peaks_max = peaks_max
        self.peaks_min = peaks_min

    def label_data(self, data):
        """
        Labels each data point with a buy, sell, or neutral signal based on peaks.

        Args:
            data (list): A list representing the market data (e.g., prices).

        Returns:
            list: A list of labels (0 for neutral, 1 for sell, 2 for buy) corresponding to each data point.
        """
        labels = []
        for i, _ in enumerate(data):  # Iterate through data indices
            if any(idx == i for idx, _ in self.peaks_min):
                labels.append(0)  # Buy signal if peak min
            elif any(idx == i for idx, _ in self.peaks_max):
                labels.append(1)  # Sell signal if peak max
            else:
                labels.append(2)  # Neutral otherwise
        return labels

    def label_dataframe(self, frame_base: pd.DataFrame, data_column: str = "close"):
        """
        Labels a DataFrame with buy, sell, and neutral columns based on peak information.

        Args:
            frame_base (pd.DataFrame): The DataFrame containing the market data.
            data_column (str, optional): The name of the column containing the data to be labeled. Defaults to "close".

        Returns:
            pd.DataFrame: The updated DataFrame with added "buy", "sell", and "neutral" columns.
        """
        if data_column not in frame_base.columns:
            raise ValueError(f"Data column '{data_column}' not found in the DataFrame.")

        labels = self.label_data(frame_base[data_column])

        frame_base["buy"] = [1 if label == 0 else 0 for label in labels]
        frame_base["sell"] = [1 if label == 1 else 0 for label in labels]
        frame_base["neutral"] = [1 if label == 2 else 0 for label in labels]

        return frame_base


class DataGenerator:
    """
    A class that generates data for training and testing.

    Args:
        dataset (pd.DataFrame): The input dataset.
        timestep (int): The number of timesteps to consider for each sample.
        xcols (List[str]): The column names to be used as input features.
        ycols (List[str]): The column names to be used as output labels.

    Methods:
        generate_data: Generates the input-output pairs for training and testing.
        balance_labelization: Balances the label distribution by removing excess neutral labels.
        train_test_split: Splits the data into training and testing sets.

    """

    def __init__(
        self, dataset: pd.DataFrame, timestep: int, xcols: List[str], ycols: List[str]
    ):
        self.dataset = dataset
        self.timestep = timestep
        self.xcols = xcols
        self.ycols = ycols

    def generate_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generates the input-output pairs for training and testing.

        Returns:
            Tuple[np.ndarray, np.ndarray]: A tuple containing the input and output arrays.

        """
        dx = [
            np.array(self.dataset.iloc[i : i + self.timestep][self.xcols])
            for i in range(len(self.dataset) - self.timestep)
        ]
        dy = [
            self.dataset.iloc[i + self.timestep - 1][self.ycols]
            for i in range(len(self.dataset) - self.timestep)
        ]
        return np.array(dx), np.array(dy)

    def balance_labelization(
        self, frame: np.ndarray, label: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Balances the label distribution by removing excess neutral labels.

        Args:
            frame (np.ndarray): The input array.
            label (np.ndarray): The label array.

        Returns:
            Tuple[np.ndarray, np.ndarray]: A tuple containing the balanced input and label arrays.

        """
        neutral_indices = np.where(label[:, 2] == 1)[0]
        sell_indices = np.where(label[:, 1] == 1)[0]
        buy_indices = np.where(label[:, 0] == 1)[0]

        neutral_count = len(neutral_indices)
        sell_count = len(sell_indices)
        buy_count = len(buy_indices)

        need_delete = neutral_count - min(sell_count, buy_count)
        rand_delete = np.random.choice(neutral_indices, need_delete, replace=False)

        final_frame = np.delete(frame, rand_delete, axis=0)
        final_label = np.delete(label, rand_delete, axis=0)

        return final_frame, final_label

    def train_test_split(
        self, test_per: float, balance: bool = False
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Splits the data into training and testing sets.

        Args:
            test_per (float): The percentage of data to be used for testing.
            balance (bool, optional): Whether to balance the label distribution. Defaults to False.

        Returns:
            Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]: A tuple containing the training and testing input and label arrays.

        """
        x_tmp, y_tmp = self.generate_data()

        if balance:
            x_tmp, y_tmp = self.balance_labelization(x_tmp, y_tmp)

        x_train, x_test, y_train, y_test = train_test_split(
            x_tmp,
            y_tmp,
            test_size=test_per,
            random_state=100,
            shuffle=settings["model_shuffle"],
        )

        return (
            x_train.astype(np.float32),
            y_train.astype(np.float32),
            x_test.astype(np.float32),
            y_test.astype(np.float32),
        )


# GET DATA
# data = get_data(settings["ticker_file"], settings["markets_target"])
# data = get_data(settings["markets_target"], [df])
data = get_data(settings["markets_target"], [features_df])

elements_to_remove = [
    "PCTRET_1",
    "TS_Trends",
    "TS_Trades",
    "TS_Entries",
    "TS_Exits",
    "ACTRET_1",
]

# Use list comprehension for efficiency and readability
filtered_feature_cols = [
    element for element in data[0]["data"].columns if element not in elements_to_remove
]

filtered_feature_cols, len(filtered_feature_cols)

settings["labelisation_features_name"] = filtered_feature_cols

# NORMALIZATION OF THE DATA
norm = Normalizer(data)
norm.fit(
    settings["normalisation_fit_type"],
    settings["labelisation_features_name"],
    settings["normalisation_fit_target"],
)


normalize_data = norm.get_normalized_data()

normalize_data


peaks_max, peaks_min = peaks_detection(
    normalize_data[settings["normalisation_target"]], settings["labelisation_disparity"]
)


# Assuming your DataFrame has a column named "prices" for market data
# data[0]["data"]
labeler = MarketLabeler(peaks_max, peaks_min)
labeled_normalize_df = labeler.label_dataframe(normalize_data, LABEL_TARGET)

data_generator = DataGenerator(labeled_normalize_df, settings["nb_per_bloc"], settings["labelisation_features_name"], settings["labelisation_labels_name"])
