import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Any

# Define the dataclasses (from the previous answer)


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


# Function to parse the YAML and create a Python class instance
def parse_yaml_to_class(yaml_file: str) -> TradingStrategyConfig:
    with open(yaml_file, "r") as file:
        data = yaml.safe_load(file)

    # Manually parse nested structures
    data_sources = {k: DataSource(**v) for k, v in data["data_sources"].items()}
    data_sources_details = [
        DataSourceDetail(**ds) for ds in data["data_sources_details"]
    ]
    interfaces = {k: TelegramInterface(**v) for k, v in data["interfaces"].items()}

    feature_sets = [
        FeatureSet(
            column_prefix=fs["column_prefix"],
            generator=fs["generator"],
            feature_prefix=fs["feature_prefix"],
            config=FeatureSetConfig(**fs["config"]),
        )
        for fs in data["feature_sets"]
    ]

    label_sets = [
        LabelSet(
            column_prefix=ls["column_prefix"],
            generator=ls["generator"],
            feature_prefix=ls["feature_prefix"],
            config=LabelSetConfig(**ls["config"]),
        )
        for ls in data["label_sets"]
    ]

    algorithms = [
        Algorithm(
            name=algo["name"],
            algo=algo["algo"],
            params=AlgorithmParams(**algo["params"]),
            train=TrainConfig(**algo["train"]),
            predict=PredictConfig(**algo["predict"]),
        )
        for algo in data["algorithms"]
    ]

    signal_sets = [
        SignalSet(
            generator=ss["generator"],
            config=(
                SignalGeneratorConfig(**ss["config"])
                if "combine" in ss["config"]
                else SignalThresholdConfig(**ss["config"])
            ),
        )
        for ss in data["signal_sets"]
    ]

    score_notification_model = NotificationModel(
        score_notification=data["score_notification_model"]["score_notification"],
        score_column_names=data["score_notification_model"]["score_column_names"],
        notify_band_up=data["score_notification_model"]["notify_band_up"],
        notify_band_dn=data["score_notification_model"]["notify_band_dn"],
        positive_bands=[
            Band(**b) for b in data["score_notification_model"]["positive_bands"]
        ],
        negative_bands=[
            Band(**b) for b in data["score_notification_model"]["negative_bands"]
        ],
    )

    diagram_notification_model = DiagramNotificationModel(
        diagram_notification=data["diagram_notification_model"]["diagram_notification"],
        notification_freq=data["diagram_notification_model"]["notification_freq"],
        score_column_names=data["diagram_notification_model"]["score_column_names"],
        score_thresholds=data["diagram_notification_model"]["score_thresholds"],
        resampling_freq=data["diagram_notification_model"]["resampling_freq"],
        nrows=data["diagram_notification_model"]["nrows"],
    )

    trade_model = TradeModel(
        buy_signal_column=data["trade_model"]["buy_signal_column"],
        sell_signal_column=data["trade_model"]["sell_signal_column"],
        trader_simulation=data["trade_model"]["trader_simulation"],
        trader_binance=data["trade_model"]["trader_binance"],
    )

    train_signal_model = TrainSignalModel(
        data_start=data["train_signal_model"]["data_start"],
        data_end=data["train_signal_model"]["data_end"],
        direction=data["train_signal_model"]["direction"],
        topn_to_store=data["train_signal_model"]["topn_to_store"],
        signal_generator=data["train_signal_model"]["signal_generator"],
        buy_sell_equal=data["train_signal_model"]["buy_sell_equal"],
        grid=Grid(**data["train_signal_model"]["grid"]),
    )

    rolling_predict = RollingPredict(
        data_start=data["rolling_predict"]["data_start"],
        data_end=data["rolling_predict"]["data_end"],
        prediction_start=data["rolling_predict"]["prediction_start"],
        prediction_size=data["rolling_predict"]["prediction_size"],
        prediction_steps=data["rolling_predict"]["prediction_steps"],
        use_multiprocessing=data["rolling_predict"]["use_multiprocessing"],
        max_workers=data["rolling_predict"]["max_workers"],
    )

    config = TradingStrategyConfig(
        objective_function=data["objective_function"],
        final_goal=data["final_goal"],
        number_of_steps=data["number_of_steps"],
        evaluator_type=data["evaluator_type"],
        risk_reward_ratio=data["risk_reward_ratio"],
        data_sources=data_sources,
        data_sources_details=data_sources_details,
        time_column=data["time_column"],
        interfaces=interfaces,
        feature_sets=feature_sets,
        label_sets=label_sets,
        label_horizon=data["label_horizon"],
        train_length=data["train_length"],
        train_feature_sets=data["train_feature_sets"],
        train_features=data["train_features"],
        labels=data["labels"],
        algorithms=algorithms,
        features_horizon=data["features_horizon"],
        features_last_rows=data["features_last_rows"],
        signal_sets=signal_sets,
        score_notification_model=score_notification_model,
        diagram_notification_model=diagram_notification_model,
        trade_model=trade_model,
        train_signal_model=train_signal_model,
        rolling_predict=rolling_predict,
    )

    return config


# Example usage
config = parse_yaml_to_class("path_to_yaml_file.yaml")
print(config)
