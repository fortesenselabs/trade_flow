import asyncio
from abc import ABC, abstractmethod
import os
import joblib
import threading
import logging
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
import torch
import torch.nn as nn
import torch.optim as optim
from trade_flow.common.logging import Logger
from packages.tf_trade.tf_trade.types import ModelType, Signal, TradeType


class Agent(ABC):
    """
    Abstract base class for agent interfaces responsible for loading trained models and generating trading signals.
    The agent continuously waits for data and sends signals asynchronously as an event-driven program.
    """

    def __init__(
        self,
        selected_instruments: List[str] = ["EURUSD", "BTCUSD", "XAUUSD"],
        logger: Optional[Logger] = None,
    ):
        """Initialize the trading bot with logging and a list of trading instruments.

        Args:
            selected_instruments (List[str]): List of instruments to trade. Default is ["EURUSD", "BTCUSD","XAUUSD"].
            logger (Optional[Logger]): An optional logger instance. If not provided, a default logger will be created.
        """
        # Set up logging
        self.logger = logger or Logger(name="it_bot", level=logging.DEBUG, filename="Bot.log")

        # Initialize the signal queue for asynchronous handling
        self.data_queue: asyncio.Queue[Dict] = asyncio.Queue()

        # Initialize the event loop
        self.loop = asyncio.get_event_loop()  # Use the current event loop

        # Store the selected instruments for trading
        self.selected_instruments = selected_instruments
        self.models = {
            symbol: None for symbol in self.selected_instruments
        }  # Initialize models for instruments

        # Log the initialized instruments
        self.logger.debug(f"Initialized with instruments: {self.selected_instruments}")

    def load_models(
        self, models_path: str, model_name: str, model_type: ModelType = ModelType.SKLEARN, **kwargs
    ) -> None:
        """
        Load trained models from the specified directory.

        Args:
            models_path (str): The directory path where the trained models are stored.
            model_name (str): The name of the model to load.
            model_type (ModelType): The type of model to load. Default is ModelType.SKLEARN.
            **kwargs: Additional keyword arguments, including:
                - model_definitions (Tuple[nn.Module, nn.Module]): Required for loading PyTorch models.
                  This should include the architecture definitions necessary for model instantiation.

        Raises:
            ValueError: If the provided path is not a directory, if the model type is invalid,
                         or if model definitions are missing for Torch models.

        Notes:
            - The function checks for the existence of model files for each symbol in `self.selected_instruments`.
            - For SKLearn models, it expects files in the format "<symbol>_voting.joblib".
            - For Torch models, it requires `model_definitions` to be provided as a tuple.
            - If the model is loaded successfully, a success message is logged; if no model file is found, a warning is logged.
            - Errors encountered during model loading are captured and logged accordingly.
        """

        # Validate the provided path
        if not os.path.isdir(models_path):
            raise ValueError(f"The provided path '{models_path}' is not a valid directory.")

        # Select the model loading function based on model type
        if model_type == ModelType.TORCH:
            load_model = _load_torch_model
            model_definitions = kwargs.get("model_definitions")
            if model_definitions is None or not isinstance(model_definitions, tuple):
                raise ValueError("Model definitions must be provided as a tuple for Torch models.")
        elif model_type == ModelType.SKLEARN:
            load_model = _load_sklearn_model
        else:
            raise ValueError(f"Invalid model type: {model_type}.")

        # Load models for each symbol based on model type
        for symbol in self.selected_instruments:
            try:
                if model_type != ModelType.TORCH:
                    self.models[symbol] = load_model(
                        symbol, model_name=model_name, path=models_path
                    )
                else:
                    self.models[symbol] = load_model(
                        symbol,
                        model_name=model_name,
                        model_definitions=model_definitions,
                        path=models_path,
                    )

                self.logger.info(f"Model for {symbol} loaded successfully from {models_path}.")

            except Exception as e:
                self.logger.error(f"Error loading model for {symbol}: {e}")

    def _create_signal(
        self,
        symbol: str,
        price: float,
        score: float,
        trade_type: TradeType,
        trend: str,
        zone: str,
        position_size: float,
    ) -> Signal:
        """
        Helper method to create a trading signal.

        Args:
            symbol (str): The trading symbol.
            price (float): The current price.
            score (float): Confidence score for the signal.
            trade_type (TradeType): The type of trade (BUY, SELL, or NEUTRAL).
            trend (str): Trend indicator.
            zone (str): Zone description for the signal.
            position_size (float): Position size

        Returns:
            Signal: A structured signal object.
        """
        return Signal(
            symbol=symbol,
            price=price,
            score=score,
            trend=trend,
            zone=zone,
            trade_type=trade_type,
            position_size=position_size,
        )

    @abstractmethod
    async def generate_signal(self, symbol: str, data: pd.DataFrame) -> Signal:
        """
        Generate trading signals using the loaded model and input data.

        Args:
            symbol (str): The trading symbol for which signals are being generated.
            data (pd.DataFrame): The input data used by the agent to make trading decisions.

        Returns:
            Signal: A list of trading signals generated by the model.
        """
        pass

    async def add_data(self, symbol: str, data: pd.DataFrame) -> None:
        """
        Add new data to the agent to trigger signal generation. This function acts as an event
        to push incoming market data for the specified symbol, which is then processed asynchronously.

        Args:
            symbol (str): The symbol or instrument for which the data is being added.
            data (pd.DataFrame): The new market data for the symbol, typically containing price
                                 and volume information for generating trading signals.

        Raises:
            ValueError: If the symbol is not in the agent's list of selected instruments.

        Notes:
            - The method pushes the data to an internal queue (`data_queue`) for further asynchronous processing.
            - Data is only added if the symbol exists in the agent's `selected_instruments` list.
        """

        if symbol in self.selected_instruments:
            await self.data_queue.put({symbol: data})
            self.logger.debug(f"Data for {symbol} added to the queue.")
        else:
            raise ValueError(f"Symbol '{symbol}' is not in the selected instruments list.")

    async def send_signals(self, queue: asyncio.Queue) -> None:
        """
        Asynchronously send the generated signals to Bot for further processing and forwarding to MT5.

        Args:
            queue (Queue): An asyncio queue to send generated signals to.

        Notes:
            - The method continuously listens for new data, generates signals for the selected instruments,
              and sends them to the provided queue.
        """
        while True:
            # Wait for new data to be added
            data_dict = await self.data_queue.get()
            self.logger.debug(data_dict)

            # Generate signals based on new data
            for symbol, data in data_dict.items():
                signal = await self.generate_signal(symbol, data)
                self.logger.info(f"Generated signals for {symbol}: {signal}")

                # Send the signal to the provided queue for further processing
                await queue.put(signal)

    async def run(self, queue: asyncio.Queue) -> None:
        """
        Start the event loop in a separate thread, allowing the agent to process signals in the background.

        Args:
            queue (asyncio.Queue): The queue where signals will be sent for further processing.

        This method:
            - Initializes a new asyncio event loop for the agent.
            - Sets the new loop as the current event loop.
            - Asynchronously sends signals to the provided queue using the `send_signals` method.
            - Starts the event loop, allowing the agent to run without blocking the main thread.
        """
        self.logger.debug("Starting the agent in a separate task.")

        # self.loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(self.loop)
        # self.loop.create_task(await self.send_signals(queue))
        # self.loop.run_forever()
        await asyncio.gather(
            self.send_signals(queue),
        )


def _load_torch_model(
    symbol: str, model_name: str, model_definitions: Tuple[nn.Module, nn.Module], path: str
) -> Tuple[nn.Module, nn.Module]:
    """
    Load a previously saved PyTorch model and its training state from a file.

    Args:
        symbol (str): The identifier for which the model is loaded (e.g., an asset or instrument symbol).
        model_name (str): The name or version of the model for the specified symbol.
        model_definitions (Tuple[nn.Module, nn.Module]): A tuple containing the PyTorch model architecture
            (nn.Module) and the loss function (nn.Module).
        path (str): The directory path where the model and its state are saved.

    Returns:
        Tuple[nn.Module, nn.Module]: A tuple containing the loaded PyTorch model and the loss function.

    Raises:
        FileNotFoundError: If no model file is found at the specified path.
        RuntimeError: If an error occurs during the loading of the model or its state.

    Notes:
        - The model file should be in the format: "<symbol>_<model_name>.pth".
        - The state dictionary contains both the model's parameters and the loss function's state.
    """
    model_file = os.path.join(path, f"{symbol}_{model_name}.pth")
    if not os.path.isfile(model_file):
        raise FileNotFoundError(f"No model file found at {path}.")

    try:
        model, loss_function = model_definitions
        state_dict = torch.load(model_file)
        model.load_state_dict(state_dict["model_state_dict"])
        loss_function.load_state_dict(state_dict["loss_function"])

        return model, loss_function
    except Exception as e:
        raise RuntimeError(f"Error loading model from {path}: {e}")


def _load_sklearn_model(symbol: str, model_name: str, path: str) -> Any:
    """
    Load a trained scikit-learn model from the specified file.

    Args:
        symbol (str): The identifier for which the model is loaded (e.g., an asset or instrument symbol).
        model_name (str): The name or version of the model for the specified symbol.
        path (str): The directory path where the scikit-learn model file is stored.

    Returns:
        model: The loaded scikit-learn model.

    Raises:
        FileNotFoundError: If no model file is found at the specified path.
        RuntimeError: If an error occurs during the loading of the model.

    Notes:
        - The model file should be in the format: "<symbol>_<model_name>.joblib".
        - This function uses `joblib` to load the model file.
    """
    model_file = os.path.join(path, f"{symbol}_{model_name}.joblib")
    if not os.path.isfile(model_file):
        raise FileNotFoundError(f"No model file found at {path}.")

    try:
        model = joblib.load(model_file)
        return model
    except Exception as e:
        raise RuntimeError(f"Error loading model from {path}: {e}")
