# TradeFlow: Intelligent Trading Automation Platform

**TradeFlow** is a platform designed to manage and optimize intelligent trading bots. it provides the infrastructure for deploying, maintaining, and scaling your automated trading strategies, functioning as the Kubernetes for trading bots. TradeFlow's bots leverage sophisticated deep-learning algorithms to analyze market trends and execute trades based on your specific risk tolerance and trading objectives. 

**NOTE:** TradeFlow is exclusively dedicated to the management and optimization of reinforcement learning-based trading bots. By harnessing the power of reinforcement learning, TradeFlow's bots autonomously learn optimal trading decisions through continuous interaction with the market. This approach might empower traders to perform better and adapt to evolving market conditions.

## Key Features

- **Automated Trading:** Set your parameters and let TradeFlow handle the execution, freeing up your time.
- **Algorithmic Analysis:** Benefit from powerful algorithms that identify promising trading opportunities.
- **Customizable Strategies:** Tailor TradeFlow's behavior to your unique risk tolerance and trading goals.

## Getting Started

**Before you begin, ensure you have the following:**

- **Python (>=3.10):** Download and install Python version 3.10 or later from the official website ([https://www.python.org/downloads/](https://www.python.org/downloads/)).
- **Poetry:** Poetry simplifies dependency management for Python projects. Follow the installation instructions on their website ([https://python-poetry.org/docs/](https://python-poetry.org/docs/)).
- **TA-Lib:** TA-Lib is a technical analysis library used by TradeFlow. Find installation instructions in the script: `./scripts/install-talib.sh`

**1. Installation:**

Follow the detailed instructions provided in the separate document: [./docs/install.md](./docs/install.md).

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

## Project Roadmap

**1. Nautilus Trader Adapter:** This component will connect Nautilus Trader to MetaTrader, facilitating data exchange.

**2. TradeFlow Platform:** This comprehensive framework will enable building and deploying multiple trading agents with dedicated trading nodes. (**Current Focus** - We recommend developing this alongside the adapter, potentially combining them into a single package later.)

**3. Trading Agent:** As the core decision-maker, this trained agent will execute trades based on market analysis. Development will commence after the Nautilus Adapter and simulated training environment are established.

**4. Ansible Integration (Optional):** While not essential for initial functionality, Ansible can be used for automated MetaTrader platform provisioning.

## Supported Markets

TradeFlow currently focuses on the following markets:

- Forex
- Synthetic Indices
- DeFi

## MetaTrader 5 Docker Image

Access the MetaTrader 5 Terminal with a web browser using this Docker image: [https://github.com/fortesenselabs/trade_flow/pkgs/container/metatrader5-terminal](https://github.com/fortesenselabs/trade_flow/pkgs/container/metatrader5-terminal)

## Disclaimer

**Important Note:** TradeFlow is designed for educational purposes only. The developers take no responsibility for any financial losses incurred while using this software. We strongly recommend thoroughly understanding the inherent risks associated with trading before using any automated system.
