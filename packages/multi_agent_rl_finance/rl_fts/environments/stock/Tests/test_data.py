import unittest
import os
from rl_fts.environments.stock.data import StockDataGenerator

class TestDataDownload(unittest.TestCase):

    def test_download(self):
        StockDataGenerator(ticker="NFLX", interval="1d", start="2012-12-31", end="2022-12-31")
        save_path = "data/stock/NFLX/2012-12-31_2022-12-31_1d.parquet.gzip"
        self.assertEqual(os.path.exists(save_path), True)

    def normalise_information():
        data_loader = StockDataGenerator(ticker="NFLX", interval="1d", start="2012-12-31", end="2022-12-31")
        data_loader.normalise_info()
        print("done")

if __name__ == '__main__':
    unittest.main()