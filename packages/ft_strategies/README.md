# Freqtrade Strategies with RL

In this setup, you will use Freqtrade’s strategy integration with reinforcement learning (RL) models, enabling you to create automated trading strategies based on past data and optimized through iterative learning.

### Install Package

```bash
pip install -e .
```

### Download Data

```bash
freqtrade download-data --config user_data/config.test.json -t 3m 5m 15m 1h --timerange=20181110-20241101
```

- **Purpose**: This command downloads historical trading data across multiple timeframes, which is essential for training and backtesting RL-based strategies.
- **Parameters**:
  - `-t`: Indicates the timeframes for data collection (e.g., 3-minute, 5-minute, etc.). These can be adjusted based on your strategy's needs.
  - `--timerange=20181110-20241101`: Sets the date range for data collection (from November 10, 2018, to November 1, 2024).

Having access to various timeframes helps the RL model make more informed predictions by observing market trends across different granularities.

### Run Backtests

**Simple:**

```bash
freqtrade backtesting --freqaimodel TradeFlowSimpleAgent --config user_data/config.test.json --strategy TradeFlowAgentStrategy --timerange=20181110-20241101
```

**Support and Resistance levels:**

```bash
freqtrade backtesting --freqaimodel TradeFlowSRAgent --config user_data/config.test.json --strategy TradeFlowAgentStrategy --timerange=20181110-20241101
```

**RSI with Support and Resistance levels:**

```bash
freqtrade backtesting --freqaimodel TradeFlowRSIWithSRAgent --config user_data/config.test.json --strategy TradeFlowAgentStrategy --timerange=20181110-20241101
```

- **Purpose**: Backtesting evaluates the strategy's performance on historical data to determine its effectiveness before deploying it live.
- **Parameters**:
  - `--freqaimodel TradeFlowAgent`: Specifies the RL model (in this case, `TradeFlowAgent`) to be used in the backtest.
  - `--config user_data/config.test.json`: Points to the configuration file for running the backtest.
  - `--strategy TradeFlowAgentStrategy`: Indicates the specific strategy configuration that the RL model will follow.
  - `--timerange=20181110-20241101`: Sets the date range for backtesting (from November 10, 2018, to November 1, 2024).

By running this command, you’ll gain insight into the strategy’s performance metrics, such as profit/loss and trade accuracy, allowing you to make any necessary adjustments before live trading.

### **Using Tensorboard**

```bash
tensorboard --logdir user_data/models/unique-id
```

- **Purpose**: Tensorboard visualizes the learning progress of your RL model, providing insights into metrics like reward, loss, and accuracy.
- **Setup**:
  - `--logdir user_data/models/unique-id`: Sets the directory where Tensorboard retrieves model logs. Replace `unique-id` with your specific model’s ID.

Monitoring the RL model’s performance over time ensures it is learning and adapting to the strategy effectively. This step is essential for diagnosing potential issues with model convergence or overfitting.

## FAQ

### What is Freqtrade?

[Freqtrade](https://github.com/freqtrade/freqtrade) Freqtrade is a free and open source crypto trading bot written in Python.
It is designed to support all major exchanges and be controlled via Telegram. It contains backtesting, plotting and money management tools as well as strategy optimization by machine learning.

### What includes these strategies?

Each Strategies includes:

- [x] **Minimal ROI**: Minimal ROI optimized for the strategy.
- [x] **Stoploss**: Optimimal stoploss.
- [x] **Buy signals**: Result from Hyperopt or based on exisiting trading strategies.
- [x] **Sell signals**: Result from Hyperopt or based on exisiting trading strategies.
- [x] **Indicators**: Includes the indicators required to run the strategy.

Best backtest multiple strategies with the exchange and pairs you're interrested in, and finetune the strategy to the markets you're trading.

### How to install a strategy?

First you need a [working Freqtrade](https://freqtrade.io).

Once you have the bot on the right version, follow this steps:

1. Select the strategy you want. All strategies of the repo are into
   [user_data/strategies](https://github.com/freqtrade/freqtrade-strategies/tree/main/user_data/strategies)
2. Copy the strategy file
3. Paste it into your `user_data/strategies` folder
4. Run the bot with the parameter `--strategy <STRATEGY CLASS NAME>` (ex: `freqtrade trade --strategy Strategy001`)

More information [about backtesting](https://www.freqtrade.io/en/latest/backtesting/) and [strategy customization](https://www.freqtrade.io/en/latest/strategy-customization/).

### How to test a strategy?

Let assume you have selected the strategy `strategy001.py`:

#### Simple backtesting

```bash
freqtrade backtesting --strategy Strategy001
```

#### Refresh your test data

```bash
freqtrade download-data --days 100
```

_Note:_ Generally, it's recommended to use static backtest data (from a defined period of time) for comparable results.

Please check out the [official backtesting documentation](https://www.freqtrade.io/en/latest/backtesting/) for more information.

## Resources

- https://github.com/freqtrade/freqtrade-strategies/
- https://github.com/Netanelshoshan/freqAI-LSTM
- https://github.com/markdregan/FreqAI-Marcos-Lopez-De-Prado
- https://github.com/PeetCrypto/freqtrade-stuff/tree/f6c38def0b2fe01d8d42e47740cdeab53511527b
- https://github.com/DutchCryptoDad/bamboo-ta
- https://github.com/iterativv/NostalgiaForInfinity
