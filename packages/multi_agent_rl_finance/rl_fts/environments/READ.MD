# Environments
Here we have environments. An environment provides new observations and rewards when it is called with an action. The environments below are split between `\sinewave` and `\stock` and the intention is to have more that follow, such as `\crypto`, `currency` and other fincancial instruments. Environments defined within sinewave are for testing purposes and where created to evaluate RL algorithms applied with our custom action and reward schemes. Environments defined within `\stock` are created for the scope of my masters thesis. To read more about these environments, read the `READ.md`'s defined in the child folders.

## Data
Environments make use of a data generation function defined as `data.py`. 

### Sinewave
The sinewave data generation file generates a sinewave price history that depends on some user defines inputs, which include: 
* The number of data points to generate
* The number of waves to generate in the dataset 
* The height of the sine wave
* How y shift of the sinewave.

### Stock
The stock data generation file collects a price history dependant on real stock data. This data is pulled from the yahoo finance python library. The data which is collected can be controlled by the following user defined inputs:
* The ticker symbol of the stock
* The data interval (intraday data cannot extend last 60 days) Valid intervals are: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
* The data period to download (Either Use period parameter or use start and end) Valid periods are: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
* The alternative start data, If not using period - Download start date string (YYYY-MM-DD) or datetime.
* The altternative end date, If not using period - Download end date string (YYYY-MM-DD) or datetime.
* Include Pre and Post market data in results? (Default is False)
* Adjust all OHLC automatically? (Default is True)
* Download stock dividends and stock splits events? (Default is True)