# Freqtrade strategies with RL

### Download Data

```bash
freqtrade download-data --config user_data/config.test.json --days 90 -t 1m 3m 5m 15m 30m
```

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
