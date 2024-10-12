import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import skew, kurtosis


class Portfolio:
    def __init__(self, data: pd.DataFrame):
        """
        Initialize the Portfolio with the given stock return data.

        Args:
            data (pd.DataFrame): DataFrame containing the returns of different stocks.
        """
        self.data = data

    @staticmethod
    def sor_criterion(weight: np.ndarray, data: pd.DataFrame) -> float:
        """
        Sortino ratio optimization criterion.

        Args:
            weight (np.ndarray): Weights for the portfolio.
            data (pd.DataFrame): DataFrame containing the returns of different stocks.

        Returns:
            float: Opposite of the Sortino ratio for minimization.
        """
        portfolio_return = np.multiply(data, np.transpose(weight)).sum(axis=1)
        mean = np.mean(portfolio_return)
        std = np.std(portfolio_return[portfolio_return < 0])
        sortino = mean / std
        return -sortino

    @staticmethod
    def mv_criterion(weights: np.ndarray, data: pd.DataFrame) -> float:
        """
        Mean-Variance portfolio optimization criterion.

        Args:
            weights (np.ndarray): Weights for the portfolio.
            data (pd.DataFrame): DataFrame containing the returns of different stocks.

        Returns:
            float: Optimization criterion value for mean-variance.
        """
        Lambda = 3
        W = 1
        Wbar = 1 + 0.25 / 100
        portfolio_return = np.multiply(data, np.transpose(weights)).sum(axis=1)
        mean = np.mean(portfolio_return)
        std = np.std(portfolio_return)
        criterion = (
            Wbar ** (1 - Lambda) / (1 + Lambda)
            + Wbar ** (-Lambda) * W * mean
            - Lambda / 2 * Wbar ** (-1 - Lambda) * W**2 * std**2
        )
        return -criterion

    @staticmethod
    def sk_criterion(weights: np.ndarray, data: pd.DataFrame) -> float:
        """
        Skewness and Kurtosis portfolio optimization criterion.

        Args:
            weights (np.ndarray): Weights for the portfolio.
            data (pd.DataFrame): DataFrame containing the returns of different stocks.

        Returns:
            float: Optimization criterion value for skewness and kurtosis.
        """
        Lambda = 3
        W = 1
        Wbar = 1 + 0.25 / 100
        portfolio_return = np.multiply(data, np.transpose(weights)).sum(axis=1)
        mean = np.mean(portfolio_return)
        std = np.std(portfolio_return)
        skewness = skew(portfolio_return)
        kurt = kurtosis(portfolio_return)

        criterion = (
            Wbar ** (1 - Lambda) / (1 + Lambda)
            + Wbar ** (-Lambda) * W * mean
            - Lambda / 2 * Wbar ** (-1 - Lambda) * W**2 * std**2
            + Lambda * (Lambda + 1) / 6 * Wbar ** (-2 - Lambda) * W**3 * skewness
            - Lambda * (Lambda + 1) * (Lambda + 2) / 24 * Wbar ** (-3 - Lambda) * W**4 * kurt
        )
        return -criterion

    def optimize_portfolio(self, criterion: callable) -> np.ndarray:
        """
        Optimize the portfolio based on the given criterion.

        Args:
            criterion (callable): Optimization criterion function (e.g. sor_criterion, mv_criterion, sk_criterion).

        Returns:
            np.ndarray: Optimal portfolio weights.
        """
        n = self.data.shape[1]
        x0 = np.ones(n) / n  # Initialize equal weights
        cons = {"type": "eq", "fun": lambda x: sum(abs(x)) - 1}
        bounds = [(0, 1) for _ in range(n)]

        result = minimize(
            criterion,
            x0,
            args=(self.data,),  # Pass self.data as the second argument to the criterion function
            method="SLSQP",
            bounds=bounds,
            constraints=cons,
            options={"disp": True},
        )
        return result.x


# Example Usage:

# # Assume `returns_df` is a pandas DataFrame containing the returns of different stocks
# portfolio = Portfolio(returns_df)

# # Optimize the portfolio using the Sortino ratio criterion
# optimal_weights_sor = portfolio.optimize_portfolio(Portfolio.sor_criterion)

# # Optimize the portfolio using the Mean-Variance criterion
# optimal_weights_mv = portfolio.optimize_portfolio(Portfolio.mv_criterion)

# # Optimize the portfolio using the Skewness-Kurtosis criterion
# optimal_weights_sk = portfolio.optimize_portfolio(Portfolio.sk_criterion)

# print("Optimal Weights (Sortino):", optimal_weights_sor)
# print("Optimal Weights (Mean-Variance):", optimal_weights_mv)
# print("Optimal Weights (Skewness-Kurtosis):", optimal_weights_sk)
