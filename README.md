# TradeFlow

**TradeFlow** is a toolkit designed to streamline the creation and management of intelligent trading bots. It provides a comprehensive tool set for deploying, scaling, and optimizing your automated trading strategies.

The toolkit is exclusively designed to manage and optimize **self-learning** trading bots. By leveraging **reinforcement learning**, TradeFlow's bots autonomously learn to make optimal trading decisions through continuous interaction with the market. This approach enables traders to enhance their performance and adapt more effectively to evolving market conditions.

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

## TODOs

- Fix Environment Rendering including the one for Multiple Rendering
- Create a basic nautilus backtest environment for testing the trained Agent

## Disclaimer

Before deciding to trade in a financial instrument you should be fully informed of the risks and costs associated with trading the financial markets, carefully consider your investment objectives, level of experience, and risk appetite, and seek professional advice where needed.

The data contained in TradeFlow is not necessarily accurate.

TradeFlow and any provider of the data contained in this website will not accept liability for any loss or damage as a result of your trading, or your reliance on the information displayed.

All names, logos, and brands of third parties that may be referenced in our sites, products or documentation are trademarks of their respective owners. Unless otherwise specified, TradeFlow and its products and services are not endorsed by, sponsored by, or affiliated with these third parties. Our use of these names, logos, and brands is for identification purposes only, and does not imply any such endorsement, sponsorship, or affiliation.

## References

**Note:** This project is built on top of the following libraries/frameworks, so most of the code and concepts are heavily borrowed from them.

- https://github.com/tensortrade-org/tensortrade
- https://github.com/nautechsystems/nautilus_trader/
- https://github.com/AI4Finance-Foundation
- https://github.com/OpenBB-finance
- https://github.com/crflynn/stochastic
- [Core paper](https://github.com/fortesenselabs/trade_flow/blob/main/docs/books/1911.10107v1.pdf)
