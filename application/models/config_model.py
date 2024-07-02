from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any


class DataSource(BaseModel):
    folder: str
    file: str
    column_prefix: str


class FeatureConfig(BaseModel):
    columns: List[str]
    functions: List[str]
    windows: Optional[List[int]] = None
    parameter: Optional[float] = None
    names: Optional[str] = None


class FeatureSet(BaseModel):
    column_prefix: str
    generator: str
    feature_prefix: str
    config: FeatureConfig


class LabelConfig(BaseModel):
    columns: List[str]
    function: str
    thresholds: List[float]
    tolerance: float
    horizon: int
    names: List[str]


class LabelSet(BaseModel):
    column_prefix: str
    generator: str
    feature_prefix: str
    config: LabelConfig


class TrainFeatureConfig(BaseModel):
    pass  # Add any specific configurations here if needed


class AlgorithmParams(BaseModel):
    penalty: str
    C: float
    class_weight: Optional[Any] = None
    solver: str
    max_iter: int


class TrainConfig(BaseModel):
    is_scale: bool
    length: int
    shifts: List[Any]


class PredictConfig(BaseModel):
    length: int


class Algorithm(BaseModel):
    name: str
    algo: str
    params: AlgorithmParams
    train: TrainConfig
    predict: PredictConfig


class SignalConfig(BaseModel):
    columns: List[str]
    names: List[str]
    combine: str
    coefficient: float
    constant: float


class SignalSet(BaseModel):
    generator: str
    config: SignalConfig


class ScoreBand(BaseModel):
    edge: float
    frequency: Optional[int] = None
    sign: str
    text: str
    bold: Optional[bool] = None


class ScoreNotificationModel(BaseModel):
    score_notification: bool
    score_column_names: List[str]
    notify_band_up: bool
    notify_band_dn: bool
    positive_bands: List[ScoreBand]
    negative_bands: List[ScoreBand]


class DiagramNotificationModel(BaseModel):
    diagram_notification: bool
    notification_freq: str
    score_column_names: str
    score_thresholds: List[float]
    resampling_freq: str
    nrows: int


class TradeModel(BaseModel):
    buy_signal_column: str
    sell_signal_column: str
    trader_simulation: bool
    trader_binance: bool
    no_trades_only_data_processing: Optional[bool] = None
    test_order_before_submit: Optional[bool] = None
    simulate_order_execution: Optional[bool] = None
    percentage_used_for_trade: Optional[float] = None
    limit_price_adjustment: Optional[float] = None


class TrainSignalModel(BaseModel):
    data_start: int
    data_end: Optional[Any] = None
    direction: str
    topn_to_store: int
    signal_generator: str
    buy_sell_equal: bool
    grid: Dict[str, List[float]]


class RollingPredict(BaseModel):
    data_start: str
    data_end: Optional[Any] = None
    prediction_start: Optional[Any] = None
    prediction_size: int
    prediction_steps: int
    use_multiprocessing: bool
    max_workers: int


class ConfigModel(BaseModel):
    api_key: str
    api_secret: str
    mt_directory_path: Optional[str]
    telegram_bot_token: str
    telegram_chat_id: str
    symbol: str
    freq: str
    data_folder: str
    models_folder: str
    merge_file_name: str
    feature_file_name: str
    matrix_file_name: str
    predict_file_name: str
    signal_file_name: str
    signal_models_file_name: str
    data_sources: List[DataSource]
    time_column: str
    feature_sets: List[FeatureSet] # TODO: fix validation problem
    label_sets: List[LabelSet]
    label_horizon: int
    train_length: int
    train_feature_sets: List[Dict[str, Any]]
    train_features: List[str]
    labels: List[str]
    algorithms: List[Algorithm]
    features_horizon: int
    features_last_rows: int
    # signal_sets: List[SignalSet]
    # score_notification_model: ScoreNotificationModel
    # diagram_notification_model: DiagramNotificationModel
    # trade_model: TradeModel
    # train_signal_model: TrainSignalModel
    # rolling_predict: RollingPredict
