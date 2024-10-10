import asyncio
import os
from typing import List, Optional
from packages.itbot.itbot import Signal
from packages.itbot.agents.agent import Agent
from trade_flow.common.logging import Logger


class Agent001(Agent):
    """
    Example agent that implements Agent, for loading a model, generating signals, and sending them to ITBot.
    """

    def __init__(self, logger: Optional[Logger] = None):
        super().__init__(logger)
        self.model = None

    def load_model(self, model_path: str) -> None:
        """
        Load the trained model from the specified path.
        """
        if os.path.exists(model_path):
            # Dummy model loading for demonstration purposes
            self.model = f"Loaded model from {model_path}"
            self.logger.info(f"Model loaded from {model_path}")
        else:
            raise FileNotFoundError(f"Model file {model_path} not found.")

    async def generate_signals(self, data: dict) -> List[Signal]:
        """
        Asynchronously generate trading signals using the loaded model based on the data.

        Args:
            data: Data from the environment to generate signals.

        Returns:
            List[Signal]: A list of generated trading signals.
        """
        if self.model is None:
            raise ValueError("Model is not loaded. Please load the model first.")

        # Simulate signal generation delay
        await asyncio.sleep(1)

        # Example signals based on input data
        signals = [
            Signal(
                symbol="BTCUSD",
                price=data["price"],
                score=data["score"],
                trend="↑",
                zone="Buy Zone",
                trade_type="Buy",
            ),
            Signal(
                symbol="ETHUSD",
                price=data["price"] * 0.05,
                score=data["score"] - 0.2,
                trend="↓",
                zone="Sell Zone",
                trade_type="Sell",
            ),
        ]
        return signals

    async def send_signals(self) -> None:
        """
        Asynchronously send the generated signals to ITBot for further processing and forwarding to MT5.
        """
        while True:
            # Wait for new data to be added
            data = await self.signals_queue.get()

            # Generate signals asynchronously based on new data
            signals = await self.generate_signals(data)

            for signal in signals:
                # Forward the signal to ITBot's queue
                self.trader.execute_trade(signal)
                self.logger.info(f"Signal sent to ITBot: {signal}")

    def run(self):
        """
        Run the agent in the background, processing data and sending signals.
        """
        super().run()  # Starts the event loop and processes tasks
