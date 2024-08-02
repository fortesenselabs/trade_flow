# Example Configurations

## Example YAML Configuration

Below is an example YAML configuration that incorporates all the elements discussed:

```yaml
# Trading Strategy Configuration

objective_function: "maximize_profit"
final_goal: "10000_usd" # Final goal to achieve
number_of_steps: 30 # Number of iterations or actions

evaluator_type: "price" # Evaluator type (trend or price)
risk_reward_ratio: 2.5 # Risk-Reward ratio

data_sources:
  binance:
    api_key: "your_binance_api_key"
    api_secret: "your_binance_api_secret"
  metatrader:
    files_path: "/path/to/metatrader/files"
  twitter:
    api_key: "your_twitter_api_key"
    api_secret: "your_twitter_api_secret"
    access_token: "your_twitter_access_token"
    access_token_secret: "your_twitter_access_token_secret"

# Data Download and Merge Settings
symbol: "Step Index"
freq: "1min" # Frequency in pandas format

data_sources_details:
  - folder: "Step Index"
    file: "klines"
    column_prefix: ""
time_column: "timestamp"

# Interface Settings
interfaces:
  telegram:
    telegram_bot_token: "your_telegram_bot_token"
    telegram_chat_id: "your_telegram_chat_id"

# === GENERATE FEATURES ===

feature_sets:
  - column_prefix: ""
    generator: "talib"
    feature_prefix: ""
    config:
      columns: ["close"]
      functions: ["SMA"]
      windows: [1, 5, 10, 15, 60]
  - column_prefix: ""
    generator: "talib"
    feature_prefix: ""
    config:
      columns: ["close"]
      functions: ["LINEARREG_SLOPE"]
      windows: [5, 10, 15, 60]
  - column_prefix: ""
    generator: "talib"
    feature_prefix: ""
    config:
      columns: ["close"]
      functions: ["STDDEV"]
      windows: [5, 10, 15, 60]
  - column_prefix: ""
    generator: "talib"
    feature_prefix: ""
    config:
      columns: ["close"]
      functions: ["RSI"]
      windows: [5, 10, 14, 15, 60]

# === LABELS ===

label_sets:
  - column_prefix: ""
    generator: "highlow2"
    feature_prefix: ""
    config:
      columns: ["close", "high", "low"]
      function: "high"
      thresholds: [2.0]
      tolerance: 0.2
      horizon: 120
      names: ["high_20"]
  - column_prefix: ""
    generator: "highlow2"
    feature_prefix: ""
    config:
      columns: ["close", "high", "low"]
      function: "low"
      thresholds: [2.0]
      tolerance: 0.2
      horizon: 120
      names: ["low_20"]
  - column_prefix: ""
    generator: "highlow2"
    feature_prefix: ""
    config:
      columns: ["close", "high", "low"]
      function: "high"
      thresholds: [1.5]
      tolerance: 1.5
      horizon: 120
      names: ["high_15"]
  - column_prefix: ""
    generator: "highlow2"
    feature_prefix: ""
    config:
      columns: ["close", "high", "low"]
      function: "low"
      thresholds: [1.5]
      tolerance: 1.5
      horizon: 120
      names: ["low_15"]

# === TRAIN ===

label_horizon: 120 # Batch/offline: do not use these last rows because their labels might not be correct
train_length: 525600 # Batch/offline: Uses this number of rows for training (if not additionally limited by the algorithm)

train_feature_sets:
  - generator: "train_features"
    config:
      # Use values from the attributes: train_features, labels, algorithms
      pass

train_features:
  - "close_SMA_1"
  - "close_SMA_5"
  - "close_SMA_10"
  - "close_SMA_15"
  - "close_SMA_60"
  - "close_LINEARREG_SLOPE_5"
  - "close_LINEARREG_SLOPE_10"
  - "close_LINEARREG_SLOPE_15"
  - "close_LINEARREG_SLOPE_60"
  - "close_STDDEV_5"
  - "close_STDDEV_10"
  - "close_STDDEV_15"
  - "close_STDDEV_60"
  - "close_RSI_5"
  - "close_RSI_10"
  - "close_RSI_14"
  - "close_RSI_15"
  - "close_RSI_60"

labels:
  - "high_20"
  - "low_20"

algorithms:
  - name: "lc" # Unique name will be used as a column suffix
    algo: "lc" # Algorithm type is used to choose the train/predict function
    params:
      penalty: "l2"
      C: 1.0
      class_weight: null
      solver: "sag"
      max_iter: 100
    train: { is_scale: true, length: 1000000, shifts: [] }
    predict: { length: 1440 }

features_horizon: 2880 # Online/stream: Minimum data length for computing features. Take it from feature generator parameters
features_last_rows: 5 # Online/stream: Last values which are really needed and have to be computed. All older values are not needed

# === GENERATE SIGNALS ===

signal_sets:
  - generator: "combine"
    config:
      columns: ["high_20_lc", "low_20_lc"] # 2 columns: with grow score and fall score
      names: "trade_score" # Output column name: positive values - buy, negative values - sell
      combine: "difference" # "no_combine" (or empty), "relative", "difference"
      coefficient: 1.0
      constant: 0.0 # Normalize
  - generator: "threshold_rule"
    config:
      columns: "trade_score"
      names: ["buy_signal_column", "sell_signal_column"] # Output boolean columns
      parameters:
        buy_signal_threshold: 0.05
        sell_signal_threshold: -0.05

# === NOTIFICATIONS ===

score_notification_model:
  # When and what score notifications to send
  score_notification: true

  score_column_names: ["trade_score"]

  notify_band_up: true
  notify_band_dn: true
  positive_bands:
    - edge: 0.03
      frequency: null
      sign: ""
      text: ""
    - edge: 0.04
      frequency: 3
      sign: "〉"
      text: "weak"
    - edge: 0.05
      frequency: 2
      sign: "〉〉"
      bold: false
      text: "strong"
    - edge: 1.0
      frequency: 1
      sign: "〉〉〉📈"
      bold: true
      text: "BUY ZONE"
  negative_bands:
    - edge: -0.03
      frequency: null
      sign: ""
      text: ""
    - edge: -0.04
      frequency: 3
      sign: "〈"
      text: "weak"
    - edge: -0.05
      frequency: 2
      sign: "〈〈"
      bold: false
      text: "strong"
    - edge: -1.0
      frequency: 1
      sign: "〈〈〈📉"
      bold: true
      text: "SELL ZONE"

diagram_notification_model:
  # Regularly sending historic data with prices, scores and buy-sell trade decisions
  diagram_notification: true
  notification_freq: "1D"

  score_column_names: "trade_score"
  score_thresholds: [-0.05, 0.05]

  # 5 minutes aggregation and this number of 5 minute intervals
  resampling_freq: "5min"
  nrows: 288

# === TRADE MODEL ===

trade_model:
  buy_signal_column: "buy_signal_column"
  sell_signal_column: "sell_signal_column"

  trader_simulation: true # Simulate trading with transaction logging and notifications

  trader_binance: false # Trade using Binance. Uncomment also parameters below
  # no_trades_only_data_processing: false
  # test_order_before_submit: false
  # simulate_order_execution: false
  # percentage_used_for_trade: 99.0  # How much should be used in orders
  # limit_price_adjustment: 0.001  # Limit order price relative to the latest close price

# === FINDING BEST TRADE PARAMETERS ===

train_signal_model:
  data_start: 0
  data_end: null

  direction: "long"
  topn_to_store: 10

  signal_generator: "threshold_rule" # generator in the signal_sets section
  buy_sell_equal: false
  grid:
    buy_signal_threshold: [0.02, 0.03, 0.04, 0.05, 0.1, 0.15]
    sell_signal_threshold: [-0.02, -0.03, -0.04, -0.05, -0.1, -0.15]

rolling_predict:
  # int, null or string with date which will be resolved using time_column and removed from source data
  data_start: "2020-02-01 00:00:00"
  data_end: null

  # One of these 3 parameters can be null and will be computed from the other two
  prediction_start: null # First row for starting predictions, for example, "2022-02-01 00:00:00"
  prediction_size: 10080 # How many predictions, for example, 1 week 7*1440
  prediction_steps: 4 # How many train-prediction steps

  use_multiprocessing: false
  max_workers: 8
```

This configuration file covers the entire trading strategy from data sources to feature generation, labeling, training, signal generation, notifications, and trading models. Make sure to fill in your specific API keys and paths where necessary.

## Example Python Class Configuration

Alternatively, you can define this configuration using a Python class, especially when using a framework like Pydantic for data validation:

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class DataSource:
    api_key: str
    api_secret: str

@dataclass
class DataSourceDetail:
    folder: str
    file: str
    column_prefix: str

@dataclass
class TelegramInterface:
    telegram_bot_token: str
    telegram_chat_id: str

@dataclass
class FeatureSetConfig:
    columns: List[str]
    functions: List[str]
    windows: List[int]

@dataclass
class FeatureSet:
    column_prefix: str
    generator: str
    feature_prefix: str
    config: FeatureSetConfig

@dataclass
class LabelSetConfig:
    columns: List[str]
    function: str
    thresholds: List[float]
    tolerance: float
    horizon: int
    names: List[str]

@dataclass
class LabelSet:
    column_prefix: str
    generator: str
    feature_prefix: str
    config: LabelSetConfig

@dataclass
class AlgorithmParams:
    penalty: str
    C: float
    class_weight: Any
    solver: str
    max_iter: int

@dataclass
class TrainConfig:
    is_scale: bool
    length: int
    shifts: List[Any]

@dataclass
class PredictConfig:
    length: int

@dataclass
class Algorithm:
    name: str
    algo: str
    params: AlgorithmParams
    train: TrainConfig
    predict: PredictConfig

@dataclass
class SignalGeneratorConfig:
    columns: List[str]
    names: str
    combine: str
    coefficient: float
    constant: float

@dataclass
class SignalThresholdConfig:
    columns: str
    names: List[str]
    parameters: Dict[str, float]

@dataclass
class SignalSet:
    generator: str
    config: Any  # Can be SignalGeneratorConfig or SignalThresholdConfig

@dataclass
class Band:
    edge: float
    frequency: Any
    sign: str
    text: str
    bold: bool = False

@dataclass
class NotificationModel:
    score_notification: bool
    score_column_names: List[str]
    notify_band_up: bool
    notify_band_dn: bool
    positive_bands: List[Band]
    negative_bands: List[Band]

@dataclass
class DiagramNotificationModel:
    diagram_notification: bool
    notification_freq: str
    score_column_names: str
    score_thresholds: List[float]
    resampling_freq: str
    nrows: int

@dataclass
class TradeModel:
    buy_signal_column: str
    sell_signal_column: str
    trader_simulation: bool
    trader_binance: bool
    # Additional parameters commented out in the YAML file can be added here

@dataclass
class Grid:
    buy_signal_threshold: List[float]
    sell_signal_threshold: List[float]

@dataclass
class TrainSignalModel:
    data_start: int
    data_end: Any
    direction: str
    topn_to_store: int
    signal_generator: str
    buy_sell_equal: bool
    grid: Grid

@dataclass
class RollingPredict:
    data_start: str
    data_end: Any
    prediction_start: Any
    prediction_size: int
    prediction_steps: int
    use_multiprocessing: bool
    max_workers: int

@dataclass
class TradingStrategyConfig:
    objective_function: str
    final_goal: str
    number_of_steps: int
    evaluator_type: str
    risk_reward_ratio: float
    data_sources: Dict[str, DataSource]
    data_sources_details: List[DataSourceDetail]
    time_column: str
    interfaces: Dict[str, TelegramInterface]
    feature_sets: List[FeatureSet]
    label_sets: List[LabelSet]
    label_horizon: int
    train_length: int
    train_feature_sets: List[Dict[str, Any]]
    train_features: List[str]
    labels: List[str]
    algorithms: List[Algorithm]
    features_horizon: int
    features_last_rows: int
    signal_sets: List[SignalSet]
    score_notification_model: NotificationModel
    diagram_notification_model: DiagramNotificationModel
    trade_model: TradeModel
    train_signal_model: TrainSignalModel
    rolling_predict: RollingPredict

# Example instantiation of the TradingStrategyConfig class
config = TradingStrategyConfig(
    objective_function="maximize_profit",
    final_goal="10000_usd",
    number_of_steps=30,
    evaluator_type="price",
    risk_reward_ratio=2.5,
    data_sources={
        "binance": DataSource(api_key="your_binance_api_key", api_secret="your_binance_api_secret"),
        "metatrader": DataSource(api_key="", api_secret="")
    },
    data_sources_details=[
        DataSourceDetail(folder="Step Index", file="klines", column_prefix="")
    ],
    time_column="timestamp",
    interfaces={
        "telegram": TelegramInterface(
            telegram_bot_token="your_telegram_bot_token",
            telegram_chat_id="your_telegram_chat_id"
        )
    },
    feature_sets=[
        FeatureSet(
            column_prefix="",
            generator="talib",
            feature_prefix="",
            config=FeatureSetConfig(
                columns=["close"],
                functions=["SMA"],
                windows=[1, 5, 10, 15, 60]
            )
        ),
        FeatureSet(
            column_prefix="",
            generator="talib",
            feature_prefix="",
            config=FeatureSetConfig(
                columns=["close"],
                functions=["LINEARREG_SLOPE"],
                windows=[5, 10, 15, 60]
            )
        ),
        FeatureSet(
            column_prefix="",
            generator="talib",
            feature_prefix="",
            config=FeatureSetConfig(
                columns=["close"],
                functions=["STDDEV"],
                windows=[5, 10, 15, 60]
            )
        ),
        FeatureSet(
            column_prefix="",
            generator="talib",
            feature_prefix="",
            config=FeatureSetConfig(
                columns=["close"],
                functions=["RSI"],
                windows=[5, 10, 14, 15, 60]
            )
        )
    ],
    label_sets=[
        LabelSet(
            column_prefix="",
            generator="highlow2",
            feature_prefix="",
            config=LabelSetConfig(
                columns=["close", "high", "low"],
                function="high",
                thresholds=[2.0],
                tolerance=0.2,
                horizon=120,
                names=["high_20"]
            )
        ),
        LabelSet(
            column_prefix="",
            generator="highlow2",
            feature_prefix="",
            config=LabelSetConfig(
                columns=["close", "high", "low"],
                function="low",
                thresholds=[2.0],
                tolerance=0.2,
                horizon=120,
                names=["low_20"]
            )
        ),
        LabelSet(
            column_prefix="",
            generator="highlow2",
            feature_prefix="",
            config=LabelSetConfig(
                columns=["close", "high", "low"],
                function="high",
                thresholds=[1.5],
                tolerance=1.5,
                horizon=120,
                names=["high_15"]
            )
        ),
        LabelSet(
            column_prefix="",
            generator="highlow2",
            feature_prefix="",
            config=LabelSetConfig(
                columns=["close", "high", "low"],
                function="low",
                thresholds=[1.5],
                tolerance=1.5,
                horizon=120,
                names=["low_15"]
            )
        )
    ],
    label_horizon=120,
    train_length=525600,
    train_feature_sets=[
        {
            "generator": "train_features",
            "config": {}
        }
    ],
    train_features=[
        "close_SMA_1",
        "close_SMA_5",
        "close_SMA_10",
        "close_SMA_15",
        "close_SMA_60",
        "close_LINEARREG_SLOPE_5",
        "close_LINEARREG_SLOPE_10",
        "close_LINEARREG_SLOPE_15",
        "close_LINEARREG_SLOPE_60",
        "close_STDDEV_5",
        "close_STDDEV_10",
        "close_STDDEV_15",
        "close_STDDEV_60",
        "close_RSI_5",
        "close_RSI_10",
        "close_RSI_14",
        "close_RSI_15",
        "close_RSI_60"
    ],
    labels=["high_20", "low_20"],
    algorithms=[
        Algorithm(
            name="lc",
            algo="lc",
            params=AlgorithmParams(
                penalty="l2",
                C=1.0,
                class_weight=None,
                solver="sag",
                max_iter=100
            ),
            train=TrainConfig(is_scale=True, length=1000000, shifts=[]),
            predict=PredictConfig(length=1440)
        )
    ],
    features_horizon=2880,
    features_last_rows=5,
    signal_sets=[
        SignalSet(
            generator="combine",
            config=SignalGeneratorConfig(
                columns=["high_20_lc", "low_20_lc"],
                names="trade_score",
                combine="difference",
                coefficient=1.0,
                constant=0.0
            )
        ),
        SignalSet(
            generator="threshold_rule",
            config=SignalThresholdConfig(
                columns="trade_score",
                names=["buy_signal_column", "sell_signal_column"],
                parameters={
                    "buy_signal_threshold": 0.05,
                    "sell_signal_threshold": -0.05
                }
            )
        )
    ],
    score_notification_model=NotificationModel(
        score_notification=True,
        score_column_names=["trade_score"],
        notify_band_up=True,
        notify_band_dn=True,
        positive_bands=[
            Band(edge=0.03, frequency=None, sign="", text=""),
            Band(edge=0.04, frequency=3, sign="〉", text="weak"),
            Band(edge=0.05, frequency=2, sign="〉〉", text="strong", bold=False),
            Band(edge=1.0, frequency=1, sign="〉〉〉📈", text="BUY ZONE", bold=True)
        ],
        negative_bands=[
            Band(edge=-0.03, frequency=None, sign="", text=""),
            Band(edge=-0.04, frequency=3, sign="〈", text="weak"),
            Band(edge=-0.05, frequency=2, sign="〈〈", text="strong", bold=False),
            Band(edge=-1.0, frequency=1, sign="〈〈〈📉", text="SELL ZONE", bold=True)
        ]
    ),
    diagram_notification_model=DiagramNotificationModel(
        diagram_notification=True,
        notification_freq="1D",
        score_column_names="trade_score",
        score_thresholds=[-0.05, 0.05],
        resampling_freq="5min",
        nrows=288
    ),
    trade_model=TradeModel(
        buy_signal_column="buy_signal_column",
        sell_signal_column="sell_signal_column",
        trader_simulation=True,
        trader_binance=False
    ),
    train_signal_model=TrainSignalModel(
        data_start=0,
        data_end=None,
        direction="long",
        topn_to_store=10,
        signal_generator="threshold_rule",
        buy_sell_equal=False,
        grid=Grid(
            buy_signal_threshold=[0.02, 0.03, 0.04, 0.05, 0.1, 0.15],
            sell_signal_threshold=[-0.02, -0.03, -0.04, -0.05, -0.1, -0.15]
        )
    ),
    rolling_predict=RollingPredict(
        data_start="2020-02-01 00:00:00",
        data_end=None,
        prediction_start=None,
        prediction_size=10080,
        prediction_steps=4,
        use_multiprocessing=False,
        max_workers=8
    )
)
```

This structured approach ensures that all necessary parameters are clearly defined and documented, making it easier to understand, maintain, and modify the trading strategy configuration.
