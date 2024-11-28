import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import TensorDataset, DataLoader
from pytorch_tcn import TCN
from sklearn.preprocessing import StandardScaler
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from datetime import datetime
from typing import Any, List, Optional, Tuple
from trade_flow.common.logging import Logger
from packages.tf_trade.tf_trade.types import ModelType, Signal, TradeType
from packages.tf_trade.tf_trade.portfolio import RiskManager
from .agent import Agent
from .features import add_ta_features


class DeepSignalAgent(Agent):
    """
    A deep learning agent that implements the Agent interface for loading a model,
    generating trading signals, and sending them to a trading bot.

    Attributes:
        logger (Logger): Logger instance for logging activities and errors.
        risk_manager (RiskManager): RiskManager instance for managing trade risks.
        position_size (float): Size of the trading position to be executed.
    """

    def __init__(
        self,
        initial_balance: float,
        strategy_name: str = "fixed_percentage",
        selected_instruments: List[str] = None,
        whitelist_instruments: List[str] = None,
        logger: Optional[Logger] = None,
        models_path: Optional[str] = None,
    ):
        """
        Initialize the DeepSignalAgent.

        Args:
            initial_balance (float): Initial account balance for trading.
            strategy_name (str): The strategy to apply for risk management.
            selected_instruments (List[str]): Instruments to trade. Defaults to ["EURUSD", "BTCUSD", "ETHUSD", "XAUUSD"].
            whitelist_instruments (List[str]): Instruments that can be traded during weekends (e.g., crypto pairs).
            logger (Optional[Logger]): Logger instance for logging activities and errors.
            models_path (Optional[str]): Path to the directory where model files are stored.
        """
        super().__init__(selected_instruments or ["EURUSD", "BTCUSD", "ETHUSD", "XAUUSD"], logger)
        self.whitelist_instruments = whitelist_instruments or ["BTCUSD", "ETHUSD"]
        self.start_time = datetime.now().strftime("%H:%M:%S")
        self.is_time = False

        # Validate whitelist instruments are in selected instruments
        invalid_instruments = [
            symbol
            for symbol in self.whitelist_instruments
            if symbol not in self.selected_instruments
        ]
        if invalid_instruments:
            error_message = f"Invalid whitelist instruments: {invalid_instruments}. These instruments are not in the selected instruments."
            self.logger.error(error_message)
            raise ValueError(error_message)

        # Risk Manager Setup
        contract_size = 1.0
        self.risk_manager = RiskManager(
            initial_balance=initial_balance,
            risk_percentage=0.1,
            contract_size=contract_size,
            logger=logger,
        )
        self.position_size = 0.1
        self.risk_manager.select_strategy(strategy_name)
        self.logger.info(
            f"Executing trade with strategy '{strategy_name}' and position size: {self.position_size}"
        )

        # Model parameters and loading
        input_dim = 123
        hidden_dim_1 = 7
        output_dim = 3

        model_definitions = {
            "BidirectionalLSTM": BidirectionalLSTMModel(
                input_size=input_dim, hidden_size=hidden_dim_1, output_size=output_dim
            ),
            "BidirectionalGRU": BidirectionalGRUModel(
                input_size=input_dim, hidden_size=hidden_dim_1, output_size=output_dim
            ),
            # "TCN": TCNModel(input_size=input_dim, output_size=output_dim),
        }

        for name, model_definition in model_definitions.items():
            self.load_models(
                models_path,
                model_name=name,
                model_type=ModelType.TORCH,
                model_definition=model_definition,
            )

        self.label_map = {0: TradeType.BUY, 1: TradeType.BUY, 2: TradeType.NEUTRAL}

    def model_inference(
        self,
        trained_model: nn.Module,
        dataloader: DataLoader,
        device: Optional[str] = None,
    ) -> dict:
        """
        Run inference on a PyTorch model using a given dataset.

        Args:
            trained_model (Tuple[nn.Module, nn.Module]): A tuple containing the trained PyTorch model.
            dataloader (DataLoader): DataLoader object for loading inference data.
            device (Optional[str]): Device to use for inference (e.g., 'cpu', 'cuda').

        Returns:
            dict: A dictionary containing loss and predictions.
        """
        device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = trained_model
        model.to(device)
        model.eval()

        raw_predictions, predicted_class = [], []

        with torch.no_grad():
            for inputs in dataloader:
                inputs = inputs[0].to(device)
                outputs = model(inputs)

                raw_predictions.extend(outputs.cpu().numpy())
                _, predicted = torch.max(outputs, 1)

                predicted_class.extend(predicted.cpu().numpy())

        # Get the probability score for the predicted class
        predicted_probability = torch.max(torch.Tensor(raw_predictions)).cpu().numpy().tolist()
        self.logger.debug(f"Predicted Probability: {predicted_probability}")

        return {
            "prediction": predicted_class[0],
            "score": predicted_probability,
            "raw_predictions": raw_predictions[0],
        }

    def ensemble_inference(
        self,
        trained_models: Tuple[nn.Module],
        dataloader: DataLoader,
        method: str = "voting",
        device: Optional[str] = None,
    ) -> Any:
        """
        Combine predictions from multiple models using the specified ensemble method.

        Args:
            trained_models (Tuple[nn.Module]): A tuple of trained model instances to be used in the ensemble.
            dataloader (DataLoader): DataLoader object for loading the inference data.
            method (str): The ensemble method to use, either 'voting' or 'averaging'. Defaults to 'voting'.
                - 'voting': Performs majority voting on the predictions from all models.
                - 'averaging': Averages the raw output scores from each model and selects the class with the highest average score.
            device (Optional[str]): The device to perform inference on, such as 'cpu' or 'cuda'. Defaults to None,
            which uses the device setup from the model inference.

        Returns:
            Any: The combined prediction after applying the ensemble method.
            The returned predictions are based on majority voting or average score, depending on the selected method.

        Raises:
            ValueError: If an unsupported ensemble method is specified.

        Example:
            To perform ensemble inference with voting:

            >>> ensemble_inference(models, dataloader, method='voting', device='cuda')

            To perform ensemble inference with averaging:

            >>> ensemble_inference(models, dataloader, method='averaging', device='cuda')
        """

        if method == "voting":
            # Get predictions from each model
            model_predictions = [
                self.model_inference(model, dataloader=dataloader, device=device)
                for model in trained_models
            ]

            # Perform majority voting
            final_predictions = []
            for i in range(len(model_predictions[0])):
                votes = [pred[i] for pred in model_predictions]
                final_prediction = max(set(votes), key=votes.count)  # Majority vote
                final_predictions.append(final_prediction)

            self.logger.debug(f"Ensemble voting predictions: {final_predictions}")
            return final_predictions

        elif method == "averaging":
            # Get raw outputs (scores) from each model
            model_raw_outputs = [
                self.model_inference(model, dataloader=dataloader, device=device)["raw_predictions"]
                for model in trained_models
            ]

            # Average raw outputs and make final predictions based on the highest score
            averaged_predictions = []
            for i in range(len(model_raw_outputs[0])):
                averaged_output = sum([raw_output[i] for raw_output in model_raw_outputs]) / len(
                    self.models
                )
                final_prediction = torch.argmax(
                    torch.Tensor(averaged_output)
                ).item()  # Select class with highest average score
                averaged_predictions.append(final_prediction)

            self.logger.debug(f"Ensemble averaging predictions: {averaged_predictions}")
            return averaged_predictions

        else:
            self.logger.error(f"Unknown ensemble method: {method}")
            raise ValueError(f"Unsupported ensemble method: {method}")

    async def _get_model_prediction(
        self, data: pd.DataFrame, model: Any, ensemble_mode: bool = False, **kwargs
    ) -> Tuple[str, float]:
        """
        Generate trading signals based on classification from input data and the model.

        Args:
            data (pd.DataFrame): Input data containing return values for feature engineering.
            model (Any): The trained model used for making predictions.
            ensemble_mode (bool): If True, ensemble mode will be used.

        Returns:
            Tuple[str, float]: A tuple containing:
                - action (str): Buy/Sell/Neutral action.
                - score (float): Confidence score of the prediction (0 to 1).
        """
        # Define the feature columns
        feature_columns = [
            "returns t-1",
            "mean returns 15",
            "mean returns 60",
            "volatility returns 15",
            "volatility returns 60",
        ]

        # Feature engineering
        # Create columns for returns and other features
        data["returns"] = (data["close"] - data["close"].shift(1)) / data["close"].shift(1)
        data["sLow"] = (data["low"] - data["close"].shift(1)) / data["close"].shift(1)
        data["sHigh"] = (data["high"] - data["close"].shift(1)) / data["close"].shift(1)

        data["returns t-1"] = data["returns"].shift(1)
        data["mean returns 15"] = data["returns"].rolling(15).mean().shift(1)
        data["mean returns 60"] = data["returns"].rolling(60).mean().shift(1)
        data["volatility returns 15"] = data["returns"].rolling(15).std().shift(1)
        data["volatility returns 60"] = data["returns"].rolling(60).std().shift(1)

        # Add technical analysis features
        data = add_ta_features(data)
        feature_columns.extend(data.columns)
        self.logger.warning(f"{data.iloc[-1].values}")

        # Drop any NaN values caused by shifting or rolling computations
        # data = data.dropna(axis=0, how='all')
        data[feature_columns + ["returns"]] = data[feature_columns + ["returns"]].fillna(0) #.mean()

        self.logger.debug(f"processed_data.shape: {data.shape}")

        # Select the last row for prediction
        X = data.iloc[-1:].values

        # Standardize the data
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Create a DataLoader with the scaled data
        tensor_x = torch.Tensor(X_scaled)
        dataloader = DataLoader(TensorDataset(tensor_x), shuffle=False)

        if not ensemble_mode:
            # Perform single model inference
            prediction = self.model_inference(model, dataloader, device="cpu")
        else:
            # Perform ensemble inference
            symbol = kwargs.get("symbol")
            if not symbol:
                raise ValueError("Symbol must be provided in ensemble mode")

            # Get models corresponding to the symbol
            symbol_models = {key: value for key, value in self.models.items() if symbol in key}
            if not symbol_models:
                raise ValueError(f"No models found for symbol: {symbol}")

            prediction = self.ensemble_inference(
                tuple(symbol_models.values()), dataloader, device="cpu"
            )

        self.logger.debug(f"prediction: {prediction}")

        # Extract action and score
        action = self.label_map[prediction["prediction"]]
        score = prediction.get("score", None)
        return action, score

    async def generate_signal(self, symbol: str, data: pd.DataFrame) -> Signal:
        """
        Generate trading signals using the loaded model and input data.

        Args:
            symbol (str): Trading symbol for which signals are generated.
            data (pd.DataFrame): Input data used by the agent to make trading decisions.

        Returns:
            Signal: A trading signal generated by the model.

        Raises:
            ValueError: If the model is not loaded before generating signals.
        """
        if self.models[symbol] is None:
            raise ValueError(f"{symbol} model is not loaded. Please load the model first.")

        if datetime.now().weekday() in (5, 6) and symbol not in self.whitelist_instruments:
            self.logger.error("Weekend trading is not allowed.")
            return Signal(signal_type=TradeType.NEUTRAL, price=0.0)

        price = data["close"].iloc[-1]
        action, score = await self._get_model_prediction(data, self.models[symbol])

        if action == TradeType.BUY:
            return self._create_signal(
                symbol, price, score, TradeType.BUY, "↑", "Buy Zone", self.position_size
            )
        elif action == TradeType.SELL:
            return self._create_signal(
                symbol, price, score, TradeType.SELL, "↓", "Sell Zone", self.position_size
            )
        return self._create_signal(
            symbol, price, score, TradeType.NEUTRAL, "→", "Neutral Zone", self.position_size
        )


"""
Model Definitions
"""


class BidirectionalLSTMModel(nn.Module):
    """
    A Bidirectional Long Short-Term Memory (LSTM) model with softmax output for sequence processing tasks.

    Args:
        input_size (int): The number of features in the input data.
        hidden_size (int): The number of features in the hidden state of the LSTM.
        output_size (int): The number of output classes or values predicted by the model.
        num_layers (int, optional): The number of stacked LSTM layers. Default is 4.
        kwargs: Additional keyword arguments.

    Attributes:
        bilstm (nn.LSTM): Bidirectional LSTM layer with dropout.
        fc (nn.Linear): Fully connected layer that maps the LSTM output to the desired output size.

    Methods:
        forward(x): Performs the forward pass of the model, taking the input through the LSTM and fully connected layer, returning softmax probabilities.
    """

    def __init__(self, input_size, hidden_size, output_size, num_layers: int = 4, **kwargs):
        super(BidirectionalLSTMModel, self).__init__()

        self.hidden_size = hidden_size or 24
        self.num_layers = num_layers

        # Bidirectional LSTMs
        self.bilstm = nn.LSTM(
            input_size, hidden_size, num_layers, batch_first=True, bidirectional=True, dropout=0.2
        )

        # Dense (fully connected) layer with softmax activation
        self.fc = nn.Linear(hidden_size * 2, output_size)

    def forward(self, x):
        # Passing input through LSTMs
        out, _ = self.bilstm(x)

        # Taking the output of the last time step
        # out = out[:, -1, :]

        # Fully connected layer
        fc = self.fc(out)

        # Softmax activation for classification
        x = F.softmax(fc)
        return x


class BidirectionalGRUModel(nn.Module):
    """
    A Bidirectional Gated Recurrent Unit (GRU) model with softmax output for sequence processing tasks.

    Args:
        input_size (int): The number of features in the input data.
        hidden_size (int): The number of features in the hidden state of the GRU.
        output_size (int): The number of output classes or values predicted by the model.
        num_layers (int, optional): The number of stacked GRU layers. Default is 4.
        kwargs: Additional keyword arguments.

    Attributes:
        bigru (nn.GRU): Bidirectional GRU layer with dropout.
        fc (nn.Linear): Fully connected layer that maps the GRU output to the desired output size.

    Methods:
        forward(x): Performs the forward pass of the model, taking the input through the GRU and fully connected layer, returning softmax probabilities.
    """

    def __init__(self, input_size, hidden_size, output_size, num_layers: int = 4, **kwargs):
        super(BidirectionalGRUModel, self).__init__()

        self.hidden_size = hidden_size or 24
        self.num_layers = num_layers

        # Bidirectional GRU layers
        self.bigru = nn.GRU(
            input_size, hidden_size, num_layers, batch_first=True, bidirectional=True, dropout=0.2
        )

        # Dense (fully connected) layer with softmax activation
        self.fc = nn.Linear(hidden_size * 2, output_size)

    def forward(self, x):
        # Forward pass through bidirectional GRU layers
        out, _ = self.bigru(x)

        # Taking the output of the last time step
        # out = out[:, -1, :]

        # Fully connected layer
        fc = self.fc(out)

        # Softmax activation for classification
        x = F.softmax(fc)
        return x


class TCNModel(nn.Module):
    """
    A Temporal Convolutional Network (TCN) model with softmax output for time-series data.

    Args:
        input_size (int): The number of features in the input data.
        output_size (int): The number of output classes or values predicted by the model.
        num_channels (Tuple, optional): The number of channels in each TCN layer. Default is (2, 3, 5, 8, 16, 32).
        kernel_size (int, optional): The size of the convolutional kernel. Default is 5.
        dilations (Tuple, optional): Dilation rates for the TCN layers. Default is (1, 2, 4, 8, 16, 32).

    Attributes:
        tcn (TCN): The Temporal Convolutional Network layer.
        fc (nn.Linear): Fully connected layer that maps the TCN output to the desired output size.

    Methods:
        forward(x): Performs the forward pass of the model, taking the input through the TCN and fully connected layer, returning softmax probabilities.
    """

    def __init__(
        self,
        input_size,
        output_size,
        num_channels: Tuple = (2, 3, 5, 8, 16, 32),
        kernel_size: int = 5,
        dilations: Tuple = (1, 2, 4, 8, 16, 32),
    ):
        super(TCNModel, self).__init__()

        # Define the TCN layer with appropriate parameters
        self.tcn = TCN(
            input_size, num_channels, kernel_size, dilations, input_shape="NLC", dropout=0.2
        )

        # Fully connected layer with input size matching the last TCN channel size
        self.fc = nn.Linear(num_channels[-1], output_size)

    def forward(self, x):
        # Passing input through the TCN layer
        out = self.tcn(x)

        # Taking the output of the last time step
        # out = out[:, -1, :]

        # Fully connected layer
        fc = self.fc(out)

        # Softmax activation for classification
        x = F.softmax(fc)
        return x
