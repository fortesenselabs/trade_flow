# TradeFlow

**TradeFlow** is a robust framework designed to streamline the creation and management of intelligent trading bots. It provides a comprehensive tool set for deploying, scaling, and optimizing your automated trading strategies.

The framework is exclusively designed to manage and optimize **self-learning** trading bots. By leveraging **reinforcement learning**, TradeFlow's bots autonomously learn to make optimal trading decisions through continuous interaction with the market. This approach enables traders to enhance their performance and adapt more effectively to evolving market conditions.

<div align="center">
<img align="center" src=docs/images/overview.png>
</div>

## Key Features

- **Automated Trading:** Set your parameters and let TradeFlow handle the execution, freeing up your time.
- **Algorithmic Analysis:** Benefit from powerful algorithms that identify promising trading opportunities.
- **Customizable Strategies:** Tailor TradeFlow's behavior to your unique risk tolerance and trading goals.
- **Self-Learning Bots:** TradeFlow's bots utilize advanced deep-learning algorithms to analyze market trends and execute trades. These bots are capable of continuous learning through reinforcement learning, adapting to changing market conditions and making informed trading decisions.
- **Composable Architecture:** The framework's modular design allows you to easily combine different components, such as data sources, trading strategies, and risk management tools, to create customized trading solutions.

By leveraging TradeFlow, you can efficiently build, deploy, and manage sophisticated trading bots that align with your unique trading objectives and risk tolerance.

## Getting Started

**Before you begin, ensure you have the following:**

- **Rust (>=1.78):** Download and install Rust version 1.78 or later from the official website ([https://www.rust-lang.org/tools/install](https://www.rust-lang.org/tools/install)).

- **Python (>=3.10):** Download and install Python version 3.10 or later from the official website ([https://www.python.org/downloads/](https://www.python.org/downloads/)).
- **Poetry:** Poetry simplifies dependency management for Python projects. Follow the installation instructions on their website ([https://python-poetry.org/docs/](https://python-poetry.org/docs/)).
- **TA-Lib:** TA-Lib is a technical analysis library used by TradeFlow. Find installation instructions in the script: `./scripts/install-talib.sh`

**1. Installation:**

Follow the detailed instructions provided in the separate [document](./docs/install.md):

**2. Start the Server:**

Open a separate terminal window and run the following command to start the TradeFlow server in the background:

```bash
flow
```

**3. List Available Environments (Optional):**

Use the `flowcli` tool to interact with the TradeFlow server. In another terminal window, run the following command to see a list of available environments:

```bash
flowcli environments available
```

## Additional Features

- **Run Tests:** Verify TradeFlow's functionality with the following command (in a terminal):

```bash
poetry run pytest --maxfail=1 --disable-warnings -q tests/
```

## Supported Markets

TradeFlow currently focuses on the following markets:

- [] Forex
- [] Crypto
- [] Stocks

## Disclaimer

Before deciding to trade in a financial instrument you should be fully informed of the risks and costs associated with trading the financial markets, carefully consider your investment objectives, level of experience, and risk appetite, and seek professional advice where needed.

The data contained in TradeFlow is not necessarily accurate.

TradeFlow and any provider of the data contained in this website will not accept liability for any loss or damage as a result of your trading, or your reliance on the information displayed.

All names, logos, and brands of third parties that may be referenced in our sites, products or documentation are trademarks of their respective owners. Unless otherwise specified, TradeFlow and its products and services are not endorsed by, sponsored by, or affiliated with these third parties. Our use of these names, logos, and brands is for identification purposes only, and does not imply any such endorsement, sponsorship, or affiliation.

## Project Roadmap

### **Phase 1: Foundation and Training Node**

1. **Node Development:**
   - Inherit from NautilusTrader's TradingNode to provide a robust foundation for real-time trading(called `LiveNode`).
   - Integrate the Nautilus backtest engine and RL gymnasium environment to create a comprehensive training environment(called `TrainingNode`, look at the backtest Node for reference).
   - Implement necessary features for data handling, market simulation, and agent interaction.

### **Phase 2: Agent Development**

1. **Agent Design:**
   - Define the agent's architecture, including its decision-making process and learning mechanisms.
   - Inherit from Nautilus trader's Actor and a defined Agent Interface to ensure compatibility and leverage existing functionalities.
2. **Agent Training:**
   - Train the agent using the TrainingNode environment and appropriate reinforcement learning algorithms.
   - Experiment with different hyperparameters and training strategies to optimize performance.

### **Phase 3: Strategies and Adaptation**

1. **Strategy Development:**
   - Create or adapt strategies from Nautilus trader's library, incorporating ActionScheme and RewardScheme to align with the agent's decision-making process.
   - Consider factors such as risk management, reward functions, and trading objectives.
2. **Strategy Optimization:**
   - Fine-tune strategies based on agent performance and market conditions.
   - Explore techniques like backtesting and parameter tuning to improve strategy effectiveness.

### **Phase 4: Integration and Testing**

1. **MetaTrader 5 Adapter Integration:**
   - Connect the Nautilus Trader framework to MetaTrader 5 using the adapter.
   - Ensure seamless data exchange and execution of trades through the MetaTrader 5 platform.
2. **Comprehensive Testing:**
   - Conduct rigorous testing of the entire system, including agent performance, strategy effectiveness, and risk management.
   - Simulate various market scenarios and evaluate the system's ability to adapt and respond to changing conditions.

### **Phase 5: Deployment and Monitoring**

1. **Deployment:**
   - Deploy the trained agent and strategies to a production environment.
   - Set up necessary infrastructure and configurations for real-time trading.
2. **Monitoring and Maintenance:**
   - Continuously monitor the agent's performance and system health.
   - Implement mechanisms for risk management and early warning systems.
   - Regularly update and maintain the system to adapt to evolving market conditions and technological advancements.

## References

- https://github.com/tensortrade-org/tensortrade
- https://github.com/nautechsystems/nautilus_trader/
- https://github.com/AI4Finance-Foundation
- https://github.com/OpenBB-finance

Note: Most of the code and concepts was heavily borrowed from `https://github.com/tensortrade-org/tensortrade` ``
