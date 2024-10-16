import asyncio
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Any, List, Optional, Tuple
from packages.tf_trade.tf_trade.types import Signal, TradeType
from packages.tf_trade.tf_trade.portfolio import RiskManager
from trade_flow.common.logging import Logger
from .agent import Agent


class BasicMLAgent(Agent):
    """
    A basic ML agent that implements the Agent interface for loading a model, generating signals,
    and sending them to a trading bot.

    This class is based on concepts from the book "Python for Finance and Algorithmic Trading" (2nd edition).

    Reference:
        https://github.com/Quantreo/2nd-edition-BOOK-AMAZON-Python-for-Finance-and-Algorithmic-Trading/

    Attributes:
        logger (Logger): Instance of Logger for logging activities and errors.
        risk_manager (RiskManager): Instance of RiskManager for managing trade risks.
        position_size (float): Size of the trading position to be executed.
        whitelist_instruments (List[str]): List of instruments that can be traded during weekends (e.g., crypto pairs).
        start_time (str): The time when the agent was initialized.
        is_time (bool): Flag to determine if it's time to execute trades.
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
        Initialize the BasicMLAgent.

        Args:
            initial_balance (float): Initial account balance for trading.
            strategy_name (str): The strategy to apply for risk management.
                                 Options: ['fixed_percentage', 'kelly_criterion', 'martingale',
                                 'mean_reversion', 'equity_curve', 'volatility_based'].
                                 Defaults to 'fixed_percentage'.
            selected_instruments (List[str]): A list of instruments to trade. Defaults to ["EURUSD", "BTCUSD", "XAUUSD"].
            whitelist_instruments (List[str]): Instruments that can be traded during weekends (e.g., crypto pairs).
            logger (Optional[Logger]): Instance of Logger for logging activities and errors.
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
            error_message = f"Invalid whitelist instruments: {invalid_instruments}. These instruments are not in selected instruments."
            self.logger.error(error_message)
            raise ValueError(error_message)

        # Risk Manager Setup
        target_returns: Optional[List[float]] = None
        period_per_return: int = 3
        total_periods: int = 30
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

        # Load model for the agent
        self.load_models(models_path, model_name="voting")

    async def _get_model_prediction(
        self, data: pd.DataFrame, model: Any, is_classification: bool = True
    ) -> Tuple[bool, bool, float]:
        """
        Generate trading signal based on classification from input data and the model.

        Args:
            data (pd.DataFrame): The input data containing return values for feature engineering.
            model (Any): The trained model used for making predictions.
            is_classification (bool): A flag indicating whether to perform classification.
                                      If True, predictions are classified as buy or sell.
                                      If False, predictions are returned as is.

        Returns:
            Tuple[bool, bool, float]: A tuple containing:
                - buy (bool): Whether to buy.
                - sell (bool): Whether to sell.
                - score (float): The confidence score of the prediction, ranging from 0 to 1.

        Notes:
            - The method performs feature engineering by calculating mean and volatility of returns
              over different rolling windows.
            - The predictions are adjusted based on the classification flag. If `is_classification`
              is True, predictions are transformed into -1 (sell) or 1 (buy).
            - If the model supports probability estimation, the score is calculated from
              `model.predict_proba`; otherwise, a default score of 1.0 is returned.
        """

        # Define the feature columns
        feature_columns = [
            "returns t-1",
            "mean returns 15",
            "mean returns 60",
            "volatility returns 15",
            "volatility returns 60",
        ]

        # Calculate returns
        data["returns"] = data["close"].pct_change(1)  # .dropna()
        self.logger.debug(data)

        # Features engineering
        data["mean returns 15"] = data["returns"].rolling(15).mean()
        data["mean returns 60"] = data["returns"].rolling(60).mean()
        data["volatility returns 15"] = data["returns"].rolling(15).std()
        data["volatility returns 60"] = data["returns"].rolling(60).std()

        # Prepare input features for the model
        X = (
            data[
                [
                    "returns",
                    "mean returns 15",
                    "mean returns 60",
                    "volatility returns 15",
                    "volatility returns 60",
                ]
            ]
            .iloc[-1:, :]
            .values
        )

        # Find the signal
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
        Generate a trading signal based on processed data.

        Args:
            symbol (str): The trading symbol for which the signal is generated.
            data (pd.DataFrame): The market data used to generate the signal.

        Returns:
            Signal: A trading signal object indicating buy, sell, or neutral.

        Raises:
            ValueError: If the model is not loaded before generating signals.

        Notes:
            - The method verifies if the current day is a weekend and prevents trading if so.
            - The signals are categorized into Buy, Sell, or Neutral zones based on the model's predictions.
        """
        if self.models[symbol] is None:
            raise ValueError(f"{symbol} Model is not loaded. Please load the model first.")

        current_time = datetime.now().strftime("%H:%M:%S")
        current_weekday = datetime.now().weekday()

        # Verification for launch
        if current_weekday in (5, 6):  # Weekend check
            if symbol in self.whitelist_instruments:
                self.logger.info(f"Trading pair {symbol} during the weekend is allowed.")
            else:
                self.logger.warning(f"Trading symbol {symbol} is not allowed during the weekend.")
                return
        else:
            # If not weekend, check trading window
            if current_time == self.start_time:
                self.is_time = True
                self.logger.info(f"Trading window opened at {self.start_time} for {symbol}.")
            else:
                self.is_time = False
                self.logger.debug(
                    f"Current time: {current_time}. Waiting for trading window at {self.start_time}."
                )

        self.logger.debug(f"Processing data for {symbol}")

        # Check if data is sufficient for processing
        if len(data) < 1:
            self.logger.warning(f"Not enough data for {symbol} to generate signals.")
            return

        await asyncio.sleep(5)
        # Toggle between random actions or actual signal processing
        # buy, sell, score = True, False, 0.6  # Example random action
        buy, sell, score = await self._get_model_prediction(data, self.models[symbol])

        self.logger.debug(f"Signal => Buy: {buy} | Sell: {sell} => {score*100}%")

        price = data["close"].iloc[-1]  # Get the latest close price

        # Generate signal based on buy/sell conditions
        if buy:
            return self._create_signal(symbol, price, score, TradeType.BUY, "↑", "Buy Zone")
        elif sell:
            return self._create_signal(symbol, price, score, TradeType.SELL, "↓", "Sell Zone")

        return self._create_signal(symbol, price, score, TradeType.NEUTRAL, "→", "Neutral Zone")
