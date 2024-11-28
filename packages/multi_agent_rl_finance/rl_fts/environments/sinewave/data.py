import pandas as pd
import numpy as np
from math import ceil
from typing import List

class SineWaveDataGenerator:
    """Provides methods for generating sinewave data
    Attributes
    ----------
    x_sample: number of samples to generate,
    period: the number of periods (peaks) in the sinewave,
    amplitude: the amplitude of the sine wave,
    y_adjustment: how much to shift the sinewave by 
     - this helps with removing negative price values
    d_ratio: the ratio to use for training, validating and testing

    Methods
    -------
    generate()
        Generates the data.
    train()
        Generates the training data.
    eval()
        Generates the evaluation data.
    test()
        Generates the testing data.
    """

    def __init__(self, 
        x_sample: int = 1000,
        period: int = 10,
        amplitude: int = 50,
        y_adjustment: int = 100,
        d_ratio: List[float] = [0.5, 0.3, 0.2]) -> None:
        """
        Parameters
        ----------
        x_range : int
            The number of data points to generate.
        period: int
            The number of waves to generate in the dataset
        amplitude : int
            The height of the sine wave (number of units above and below the y_adjustment)
        y_adjustment: int
            Where on the y-axis to center the sine wave
        d_ratio : List[float]
            The ratio for the [train, evaluation, test] split.
        """
        self.x_sample = x_sample
        self.period = period
        self.amplitude = amplitude
        self.y_adjustment = y_adjustment
        self.d_ratio = d_ratio
        self.data = self.generate()

    def generate(self):
        """
        Generates training, evaluation and testing data for a sinwave. 
        Parameters
        ----------
        x_range : int
            The number of data points to generate.
        y_height : int
            The height of the sine wave
        Returns
        -------
        `pd.DataFrame`:
            Price.
        """
        # generate x values
        x = np.linspace(0, self.period * np.pi, num=self.x_sample)
        # generate y values from x values
        y = self.amplitude * np.sin(x) + self.y_adjustment # scale sign by 50 and shift up by 50
        # generate the dataframe
        return pd.DataFrame(y, columns =['price'])

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