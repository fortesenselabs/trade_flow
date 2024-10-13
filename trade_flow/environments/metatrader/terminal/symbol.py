from typing import Tuple
from .interface import MTSymbolInfo


class SymbolInfo:
    """
    Represents symbol information from a MetaTrader symbol.

    Attributes:
        name (str): The name of the trading symbol.
        market (str): The market category (e.g., Forex, Crypto, Stock).
        currency_margin (str): The currency used for margin.
        currency_profit (str): The currency used for profit calculations.
        currencies (Tuple[str, ...]): A tuple of distinct currencies (margin, profit).
        trade_contract_size (float): The contract size for each trade.
        margin_rate (float): The margin rate (default set to 1.0).
        volume_min (float): The minimum trade volume.
        volume_max (float): The maximum trade volume.
        volume_step (float): The step size for adjusting trade volumes.
    """

    def __init__(self, info: MTSymbolInfo) -> None:
        """
        Initializes the SymbolInfo class with relevant symbol details.

        Args:
            info (MTSymbolInfo): An instance of the MTSymbolInfo interface that
            provides the symbol data.
        """
        self.name: str = info.name
        self.market: str = self._determine_market(info)

        self.currency_margin: str = info.currency_margin
        self.currency_profit: str = info.currency_profit
        self.currencies: Tuple[str, ...] = (
            (self.currency_margin, self.currency_profit)
            if self.currency_margin != self.currency_profit
            else (self.currency_margin,)
        )

        self.trade_contract_size: float = info.trade_contract_size
        self.margin_rate: float = (
            1.0  # Margin rate is not provided by MetaTrader, so default is set to 1.0
        )

        self.volume_min: float = info.volume_min
        self.volume_max: float = info.volume_max
        self.volume_step: float = info.volume_step

    def __str__(self) -> str:
        """
        Returns a string representation of the symbol's market and name.

        Returns:
            str: A formatted string combining market and name.
        """
        return f"{self.market}/{self.name}"

    def _determine_market(self, info: MTSymbolInfo) -> str:
        """
        Determines the market type (e.g., Forex, Crypto, Stock) based on the symbol's path.

        Args:
            info (MTSymbolInfo): An instance of MTSymbolInfo containing the symbol's path.

        Returns:
            str: The identified market type or the root directory name if no match is found.
        """
        market_map = {
            "forex": "Forex",
            "crypto": "Crypto",
            "stock": "Stock",
        }

        root = info.path.split("\\")[0].lower()
        for prefix, market_name in market_map.items():
            if root.startswith(prefix):
                return market_name

        return root.capitalize()  # Fallback to capitalizing the root directory name
