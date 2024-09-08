"""
A Class for downloading and scaling stock data.

Data is stored in the data/stock directory with the following file naming conventions: 
<tickername>/<start-date>_<end-date>_interval. 

Normalised variables are stored in csv's ending with: _max, _mean, min, _std and _var. 
The first column of each csv defines the variables being normalised as 
['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits']

A z-score scaled dataframe of the data is stored as _scaled. 
"""

import yfinance as yf
import pandas as pd
from typing import List
from math import ceil
import os

class StockDataGenerator:
    """Provides methods for retrieving data on different stocks from yahoo finance using the yfinance python module
    Attributes
    ----------
    ticker : str
        The ticker symbol of the stock.
    interval : str
        The data interval (intraday data cannot extend last 60 days) Valid intervals are: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    start : str
        If not using period - Download start date string (YYYY-MM-DD) or datetime.
    end : str
        If not using period - Download end date string (YYYY-MM-DD) or datetime.
    period : str
        data period to download (Either Use period parameter or use start and end) Valid periods are: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    prepost : str
        Include Pre and Post market data in results? (Default is False)
    auto_adjust : str
        Adjust all OHLC automatically? (Default is True)
    actions : str
        Download stock dividends and stock splits events? (Default is True)


    Methods
    -------
    generate()
        Fetches data from yahoo finance.
    train()
        Generates the training data.
    eval()
        Generates the evaluation data.
    test()
        Generates the testing data.
    """

    def __init__(self,
              ticker: str,
              interval: str,
              start: str = None,
              end: str = None,
              period: str = "5y",
              prepost: bool = False,
              auto_adjust: bool = True,
              actions: bool = True,
              d_ratio: List[float] = [0.5, 0.3, 0.2]) -> pd.DataFrame:
        """Fetches data for different exchanges and cryptocurrency pairs.
        Parameters
        ----------
        ticker : str
            The ticker symbol of the stock.
        interval : str
            The data interval (intraday data cannot extend last 60 days) Valid intervals are: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
        start : str
            If not using period - Download start date string (YYYY-MM-DD) or datetime.
        end : str
            If not using period - Download end date string (YYYY-MM-DD) or datetime.
        period : str
            data period to download (Either Use period parameter or use start and end) Valid periods are: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        prepost : str
            Include Pre and Post market data in results? (Default is False)
        auto_adjust : str
            Adjust all OHLC automatically? (Default is True)
        actions : str
            Download stock dividends and stock splits events? (Default is True)
        Returns
        -------
        """
        self.ticker = ticker
        self.interval = interval
        self.start = start
        self.end = end
        self.period = period
        self.prepost = prepost
        self.auto_adjust = auto_adjust
        self.actions = actions
        self.d_ratio = d_ratio
        self.folder_path = "data/stock/"+ticker
        self.file_name = start+"_"+end+"_"+interval
        self.file_path = self.folder_path+"/"+self.file_name
        self.load()

    def download(self):
        """Download stock data from yfinance"""
        msft = yf.Ticker(self.ticker)
        if self.start:
            history: pd.DataFrame = msft.history(
                interval=self.interval, 
                start=self.start, 
                end=self.end, 
                prepost=self.prepost, 
                auto_adjust=self.auto_adjust, 
                actions=self.actions
            ) 
        else:
            history: pd.DataFrame = msft.history(
                interval=self.interval, 
                period=self.period, 
                prepost=self.prepost, 
                auto_adjust=self.auto_adjust, 
                actions=self.actions
            )

        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)
        
        history.to_parquet(path=self.file_path+".parquet")

        return history

    def load(self):
        """Load the stock price information for the specified ticker"""
        # if file does not exist
        if not os.path.isfile(self.file_path+".parquet"):
            self.data = self.download()
            # self.scaled_data = self.scale_data()
            # self.save_normalisation_values()
            # self.load_normalisation_values()
        else:
            self.data = pd.read_parquet(path=self.file_path+".parquet")
            # self.scaled_data = pd.read_parquet(path=self.file_path+"_scaled"+".parquet")
            # self.load_normalisation_values()

    # def scale_data(self):
    #     df_copy = self.data.copy()
    #     df_z_scaled = (df_copy - df_copy.mean()) / df_copy.std() 
    #     df_z_scaled.to_parquet(path=self.file_path+"_scaled"+".parquet")
    #     return df_z_scaled

    # def save_normalisation_values(self):
    #     """Normalise the price information for the specified ticker"""
    #     self.data.min().to_csv(self.file_path+"_min"+".csv", header=False)
    #     self.data.max().to_csv(self.file_path+"_max"+".csv",  header=False)
    #     self.data.mean().to_csv(self.file_path+"_mean"+".csv",  header=False)
    #     self.data.std().to_csv(self.file_path+"_std"+".csv",  header=False)
    #     self.data.var().to_csv(self.file_path+"_var"+".csv",  header=False)

    # def load_normalisation_values(self):
    #     self.min = pd.read_csv(self.file_path+"_min"+".csv")
    #     self.max = pd.read_csv(self.file_path+"_max"+".csv")
    #     self.mean = pd.read_csv(self.file_path+"_mean"+".csv")
    #     self.std = pd.read_csv(self.file_path+"_std"+".csv")
    #     self.var = pd.read_csv(self.file_path+"_var"+".csv")

    def train(self):
        """
        Retrieve the training data from the data source.
        Returns
        -------
        `pd.DataFrame`:
            Price.
        """
        train_start_index = 0
        # Get the ending dataframe row from our train, test, evaluation ratio's
        train_end_index = ceil(len(self.data) * self.d_ratio[0])
        # get the dataframe with rows indexed for training
        dataframe = self.data.iloc[train_start_index:train_end_index]
        return dataframe
    
    def validate(self):
        """
        Retrieve the evaluation data from the data source.
        Returns
        -------
        `pd.DataFrame`:
            Price.
        """
        valid_start_index = ceil(len(self.data) * self.d_ratio[0])
        # Get the ending dataframe row from our train, test, evaluation ratio's
        valid_end_index = ceil(len(self.data) * (self.d_ratio[0] + self.d_ratio[1]))
        # get the dataframe with rows indexed for training
        dataframe = self.data.iloc[valid_start_index:valid_end_index]
        return dataframe

    def test(self):
        """
        Retrieve the testing data from the data source.
        Returns
        -------
        `pd.DataFrame`:
            Price.
        """
        test_start_index = ceil(len(self.data) * (self.d_ratio[0] + self.d_ratio[1]))
        # Get the ending dataframe row from our train, test, evaluation ratio's
        test_end_index = len(self.data)
        # get the dataframe with rows indexed for training
        dataframe = self.data.iloc[test_start_index:test_end_index]
        return dataframe