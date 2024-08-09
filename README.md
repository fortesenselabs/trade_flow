# TradeFlow

TradeFlow is an intelligent trading bot designed to streamline your trading experience. It utilizes state-of-the-art machine/deep learning algorithms to analyze markets and execute trades based on your defined `strategies` and `trading style`.

## Features

- Automated Trading: Set your parameters and let TradeFlow handle the execution.
- Algorithmic Analysis: Leverage powerful algorithms to identify trading opportunities.
- Customizable Strategies: Tailor TradeFlow's behavior to your risk tolerance and goals.

## Getting Started

1. **Prerequisites:**

- Python (>=3.10)
- poetry
- [TA-Lib](./scripts/install-talib.sh)

2. **Clone the Repository:**

```bash
git clone https://github.com/fortesenselabs/trade_flow.git
```

3. **Installation:**

```bash
cd trade_flow
pip install -e .
```

4. **Start server/daemon in a separate terminal:**

```bash
flow
```

5. **Get a list of available environments:**

```bash
flowcli environments available
```

## Extras

- Run tests:

```bash
python -m pytest tests/
```

- Configuration:
  Edit the `config.json` OR `config.yaml` OR `config.jsonc` file to define your API keys, trading strategies, and risk parameters.

## Milestones

1. Nautilus Trader Adapter: This connects Nautilus Trader to MetaTrader.

2. TradeFlow: Infrastructure for building and deploying multiple agents with trading nodes (This is the platform we want to build and to be honest, we can do it along with the adapter for now, then later we would push it out as a standalone package)

3. Trading Agent: The trained agent that makes decisions. (To be built on after of the Nautilus Adapter and simulated training environment) (3)

4. Ansible: This is for provisioning MetaTrader platforms automatically. (Optional for now)

## Niche Markets

- Forex
- Synthetic Indices
- DeFi

## MetaTrader 5 Docker Image

[This](./infrastructure/MetaTrader5/) docker image provides an environment to access Metatrader 5 Terminal with a web browser.

## Disclaimer

TradeFlow is for educational purposes only. The developers are not responsible for any financial losses incurred while using this software. Please understand the inherent risks involved in trading before using any automated system.
