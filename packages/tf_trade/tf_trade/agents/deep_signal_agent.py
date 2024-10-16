import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from pytorch_tcn import TCN
from datetime import datetime
from typing import Any, List, Optional, Tuple
from trade_flow.common.logging import Logger
from packages.tf_trade.tf_trade.types import Signal, TradeType
from packages.tf_trade.tf_trade.portfolio import RiskManager
from .agent import Agent

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)


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
        selected_instruments: List[str] = ["EURUSD", "BTCUSD", "ETHUSD", "XAUUSD"],
        whitelist_instruments: List[str] = ["BTCUSD", "ETHUSD"],
        logger: Optional[Logger] = None,
        models_path: Optional[str] = None,
    ):
        """
        Initialize the DeepSignalAgent.

        Args:
            initial_balance (float): Initial account balance for trading.
            strategy_name (str): The strategy to apply for risk management.
                Options include: ['fixed_percentage', 'kelly_criterion', 'martingale',
                'mean_reversion', 'equity_curve', 'volatility_based'].
                Defaults to 'fixed_percentage'.
            selected_instruments (List[str]): Instruments to trade. Defaults to
                ["EURUSD", "BTCUSD", "ETHUSD", "XAUUSD"].
            whitelist_instruments (List[str]): Instruments that can be traded during
                weekends (e.g., crypto pairs).
            logger (Optional[Logger]): Logger instance for logging activities and errors.
            models_path (Optional[str]): Path to the directory where model files are stored.

        Raises:
            ValueError: If any instrument in the whitelist is not included in the selected instruments.
        """
        super().__init__(selected_instruments, logger)
        self.whitelist_instruments = whitelist_instruments
        self.start_time = datetime.now().strftime("%H:%M:%S")
        self.is_time = False

        # Validate whitelist instruments are in selected instruments
        invalid_instruments = [
            symbol
            for symbol in self.whitelist_instruments
            if symbol not in self.selected_instruments
        ]
        if invalid_instruments:
            error_message = f"Invalid whitelist instruments: {invalid_instruments}. "
            error_message += "These instruments are not in the selected instruments."
            self.logger.error(error_message)
            raise ValueError(error_message)

        # Risk Manager Setup
        contract_size: float = 1.0
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

        # Model parameters
        input_dim = 123  # Feature size per time step (input dimension)
        hidden_dim_1 = 7  # Hidden layer size
        output_dim = 3  # Number of output classes
        self.device = "cpu"

        trained_models = {
            "BidirectionalLSTM": BidirectionalLSTMModel(
                input_size=input_dim, hidden_size=hidden_dim_1, output_size=output_dim
            ),
            "BidirectionalGRU": BidirectionalGRUModel(input_size=input_dim, hidden_size=hidden_dim_1, output_size=output_dim),
            "TCN": TCNModel(input_size=input_dim, output_size=output_dim)
        }

        # Load models for the agent
        self.load_models(models_path)


    def model_inference(
        self,
        trained_model: Tuple[nn.Module, nn.Module],
        dataloader: DataLoader,
        device: Optional[str] = None,
    ) -> dict:
        """Run inference on a PyTorch model using a given dataset.

        Args:
            trained_model (Tuple[nn.Module, nn.Module]): A tuple containing the trained PyTorch model and the loss function.
            dataloader (DataLoader): DataLoader object for loading evaluation data.
            device (Optional[str]): Device to use for evaluation (e.g., 'cpu', 'cuda').

        Returns:
            dict: A dictionary containing evaluation metrics such as accuracy, precision, recall, F1 score, and confusion matrix.
        """
        if device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        model, loss_function = trained_model
        model.to(device)
        model.eval()  # Set the model to evaluation mode

        raw_targets = []
        raw_predictions = []
        all_targets = []
        all_predictions = []
        total_loss = 0

        with torch.no_grad():  # Disable gradient calculation during evaluation
            for inputs, targets in dataloader:
                inputs, targets = inputs.to(device), targets.to(device)

                outputs = model(inputs)
                loss = loss_function(outputs, targets)
                total_loss += loss.item()

                raw_targets.extend(targets.cpu().numpy())
                raw_predictions.extend(outputs.cpu().numpy())

                # Convert outputs to predicted class (argmax for multi-class classification)
                _, predicted = torch.max(outputs, 1)

                # Convert one-hot encoded targets to class indices if necessary
                if len(targets.shape) > 1 and targets.shape[1] > 1:
                    targets = torch.argmax(targets, dim=1)

                all_targets.extend(targets.cpu().numpy())
                all_predictions.extend(predicted.cpu().numpy())

        metrics = {
            "loss": total_loss / len(dataloader),
            "accuracy": accuracy_score(all_targets, all_predictions),
            "precision": precision_score(all_targets, all_predictions, average="weighted"),
            "recall": recall_score(all_targets, all_predictions, average="weighted"),
            "f1_score": f1_score(all_targets, all_predictions, average="weighted"),
            "confusion_matrix": confusion_matrix(all_targets, all_predictions),
        }

        return metrics

    async def _process_signal(
        self, data: pd.DataFrame, model: Any, is_classification: bool = True
    ) -> Tuple[bool, bool, float]:
        """
        Generate trading signals based on classification from input data and the model.

        Args:
            data (pd.DataFrame): Input data containing return values for feature engineering.
            model (Any): The trained model used for making predictions.
            is_classification (bool): Flag indicating whether to perform classification.
                If True, predictions are classified as buy or sell.

        Returns:
            Tuple[bool, bool, float]: A tuple containing:
                - buy (bool): Whether to buy.
                - sell (bool): Whether to sell.
                - score (float): Confidence score of the prediction, ranging from 0 to 1.

        Notes:
            - Performs feature engineering by calculating mean and volatility of returns
              over different rolling windows.
            - Predictions are adjusted based on the classification flag.
              If `is_classification` is True, predictions are transformed into -1 (sell) or 1 (buy).
            - If the model supports probability estimation, the score is calculated from
              `model.predict_proba`; otherwise, a default score of 1.0 is returned.
        """
        # Feature engineering
        data["mean_returns_15"] = data["returns"].rolling(15).mean()
        data["mean_returns_60"] = data["returns"].rolling(60).mean()
        data["volatility_returns_15"] = data["returns"].rolling(15).std()
        data["volatility_returns_60"] = data["returns"].rolling(60).std()

        # Prepare input features for the model
        X = (
            data[
                [
                    "returns",
                    "mean_returns_15",
                    "mean_returns_60",
                    "volatility_returns_15",
                    "volatility_returns_60",
                ]
            ]
            .iloc[-1:, :]
            .values
        )

        # Generate the signal using an ensemble of all available models for the asset/symbol
        prediction = model.predict(X)
        self.logger.debug(f"Prediction: {prediction}")

        if is_classification:
            prediction = np.where(prediction == 0, -1, 1)  # -1 for sell, 1 for buy

        buy = prediction[0] > 0
        sell = not buy

        # Confidence score (assuming model.predict_proba returns probabilities)
        score = (
            model.predict_proba(X)[0][1] if hasattr(model, "predict_proba") else 1.0
        )  # Default score if not available

        return buy, sell, score

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

        Notes:
            - Verifies if the current day is a weekend and prevents trading if so.
            - Signals are categorized into Buy, Sell, or Neutral zones based on the model's predictions.
        """
        if self.models[symbol] is None:
            raise ValueError(f"{symbol} model is not loaded. Please load the model first.")

        current_time = datetime.now().strftime("%H:%M:%S")
        current_weekday = datetime.now().weekday()

        # Weekend check
        if current_weekday in (5, 6):  # Saturday and Sunday
            if symbol in self.whitelist_instruments:
                self.logger.warning(f"Weekend trading is allowed for {symbol}.")
            else:
                self.logger.error("Weekend trading is not allowed.")
                return Signal(signal_type=TradeType.NEUTRAL, price=0.0)

        buy, sell, score = await self._process_signal(data, self.models[symbol])
        self.logger.info(
            f"Generated signal for {symbol}: Buy={buy}, Sell={sell}, Score={score:.2f}"
        )

        # Return signal based on predictions
        if buy:
            return Signal(signal_type=TradeType.BUY, price=0.0)  # Replace 0.0 with actual price
        elif sell:
            return Signal(signal_type=TradeType.SELL, price=0.0)  # Replace 0.0 with actual price

        return Signal(signal_type=TradeType.NEUTRAL, price=0.0)


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
        out = out[:, -1, :]

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
        out = out[:, -1, :]

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
        out = out[:, -1, :]

        # Fully connected layer
        fc = self.fc(out)

        # Softmax activation for classification
        x = F.softmax(fc)
        return x
