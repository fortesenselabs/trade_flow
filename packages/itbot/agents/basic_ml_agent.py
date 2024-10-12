from datetime import datetime
from typing import Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from packages.itbot.itbot import Signal, TradeType
from packages.itbot.agents.agent import Agent
from packages.itbot.itbot.portfolio import RiskManager
from trade_flow.common.logging import Logger


class BasicMLAgent(Agent):
    """
    An agent that implements the Agent interface for loading a model, generating signals,
    and sending them to ITBot.

    Attributes:
        logger (Logger): Instance of Logger for logging activities and errors.
        risk_manager (RiskManager): Instance of RiskManager for managing trade risks.
        position_size (float): Size of the trading position to be executed.
    """

    def __init__(
        self,
        initial_balance: float,
        strategy_name: str = "fixed_percentage",
        selected_symbols: List[str] = ["EURUSD", "BTCUSD", "ETHUSD", "XAUUSD"],
        whitelist_symbols: List[str] = ["BTCUSD", "ETHUSD"],
        logger: Optional[Logger] = None,
    ):
        """
        Initialize the BasicMLAgent.

        Args:
            initial_balance (float): Initial account balance for trading.
            strategy_name (str): The strategy to apply for risk management.
                                 Options: ['fixed_percentage', 'kelly_criterion', 'martingale',
                                 'mean_reversion', 'equity_curve', 'volatility_based'].
                                 Defaults to 'fixed_percentage'.
            selected_symbols (List[str]): A list of symbols to trade. Defaults to ["EURUSD", "BTCUSD", "XAUUSD"].
            whitelist_symbols (List[str]): Symbols that can be traded during weekends (e.g., crypto pairs).
            logger (Optional[Logger]): Instance of Logger for logging activities and errors.
        """
        super().__init__(selected_symbols, logger)
        self.whitelist_symbols = whitelist_symbols
        self.start_time = datetime.now().strftime("%H:%M:%S")
        self.is_time = False

        # Validate whitelist symbols are in selected symbols
        invalid_symbols = [
            symbol for symbol in self.whitelist_symbols if symbol not in self.selected_symbols
        ]
        if invalid_symbols:
            error_message = f"Invalid whitelist symbols: {invalid_symbols}. These symbols are not in selected symbols."
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

    async def _generate_signal(
        self, data: pd.DataFrame, model: Any, is_classification: bool = True
    ) -> Tuple[bool, bool, float]:
        """
        Generate trading signals based on classification from input data and the model.

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
        # Create new variable
        data.columns = ["returns"]

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

    async def generate_signals(self, symbol: str, data: pd.DataFrame) -> List[Signal]:
        """
        Generate trading signals using the loaded model and input data.

        Args:
            symbol (str): The trading symbol for which signals are being generated.
            data (pd.DataFrame): The input data used by the agent to make trading decisions.

        Returns:
            List[Signal]: A list of trading signals generated by the model.

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
            if symbol in self.whitelist_symbols:
                self.logger.info(f"Trading pair {symbol} during the weekend is allowed.")
            else:
                self.logger.warning(f"Trading symbol {symbol} is not allowed during the weekend.")
                raise RuntimeError(f"Trading {symbol} is restricted on weekends.")
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
        self.logger.debug(data)

        # Calculate returns
        data["returns"] = data["close"].pct_change(1)  # .dropna()

        # Check if data is sufficient for processing
        if len(data) < 1:
            self.logger.warning(f"Not enough data for {symbol} to generate signals.")
            return []

        # Create the signals
        buy, sell, score = await self._generate_signal(data, self.models[symbol])
        self.logger.debug(f"Signal => Buy: {buy} | Sell: {sell} => {score*100}%")

        price = data["close"].iloc[-1]  # Latest close price

        signals = []
        if buy:
            signals.append(
                Signal(
                    symbol=symbol,
                    price=price,
                    score=score,
                    trend="↑",
                    zone="Buy Zone",
                    trade_type=TradeType.BUY,
                    position_size=self.position_size,
                )
            )
        elif sell:
            signals.append(
                Signal(
                    symbol=symbol,
                    price=price,
                    score=score,
                    trend="↓",
                    zone="Sell Zone",
                    trade_type=TradeType.SELL,
                    position_size=self.position_size,
                )
            )
        else:
            signals.append(
                Signal(
                    symbol=symbol,
                    price=price,
                    score=score,
                    trend="→",
                    zone="Neutral Zone",
                    trade_type=TradeType.NEUTRAL,
                )
            )

        return signals

    async def send_signals(self) -> None:
        """
        Asynchronously send the generated signals to ITBot for further processing and forwarding to MT5.

        Notes:
            - The method continuously listens for new data, generates signals for the selected symbols,
              and logs the generated signals.
        """
        while True:
            # Wait for new data to be added
            data = await self.signals_queue.get()

            # Generate signals based on new data
            for symbol in self.selected_symbols:
                signals = await self.generate_signals(symbol, data[symbol])
                # Logic to send signals to ITBot would go here
                self.logger.info(f"Generated signals for {symbol}: {signals}")

    def run(self):
        """
        Run the agent in the background, processing data and sending signals.

        Notes:
            - This method starts the event loop and processes tasks.
        """
        super().run()  # Starts the event loop and processes tasks
