# Flow

You need to create a flow for a trading strategy that includes defining an objective function, specifying a final goal, and configuring various parameters such as the number of steps, evaluator type, risk-reward ratio, and data sources. Below is a detailed explanation and documentation of how this flow should be structured, along with an example YAML configuration.

### Detailed Documentation

#### 1. Objective Function

The objective function defines the criteria by which the success of your trading strategy will be evaluated. It could be based on achieving a specific account balance, a target profit, or another financial metric.

#### 2. Final Goal

The final goal specifies the ultimate target for your trading strategy. This could be a desired account balance or the accumulation of a certain amount of an asset.

#### 3. Number of Steps

The number of steps indicates the iterations or actions the strategy will take before reaching the final goal. For example, 30 steps could represent 30 trading decisions or intervals.

#### 4. Evaluator Type

The evaluator type determines how the strategy's performance will be assessed:

- **Trend**: Used for classifier models that predict the direction of price movements.
- **Price**: Used for regressor models that predict the exact price.

#### 5. Risk-Reward Ratio

The risk-reward ratio is a measure of the expected return of an investment relative to the risk taken. It helps in balancing potential gains against potential losses.

#### 6. Venues

Venues provide the necessary market data for analysis and decision-making. You can configure multiple data venues such as Binance, MetaTrader, and Twitter. Each venue will have its own configuration parameters.

#### 7. Interfaces

Interfaces like Telegram can be used for notifications and updates about the trading strategy. This involves setting up a Telegram bot token and chat ID to send messages.

### Examples

[Example Configurations](config_examples.md)
