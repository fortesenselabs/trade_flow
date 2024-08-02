# TradeFlow

TradeFlow is an intelligent trading bot designed to streamline your trading experience. It utilizes state-of-the-art machine/deep learning algorithms to analyze markets and execute trades based on your defined `strategies` and `trading style`.

## Features

- Automated Trading: Set your parameters and let TradeFlow handle the execution.
- Algorithmic Analysis: Leverage powerful algorithms to identify trading opportunities.
- Customizable Strategies: Tailor TradeFlow's behavior to your risk tolerance and goals.

## Getting Started

1. **Prerequisites:**

- Python (version 3.11)
- ta-lib, nautilus_trader
- pandas, tensorflow, ray
- flask, metatrader-sockets-client

1. **Clone the Repository:**

```bash
git clone https://github.com/FortesenseLabs/trade_flow.git
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

5. **Get list of available environments:**

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

1. Nautilus Trader Adapter: For connecting Nautilus to MetaTrader.

2. TradeFlow: Infrastructure for running multiple trading nodes(based on nautilus) and agents (This is the platform we want to build and to be honest we can do it along with the adapter for now, then later we would push it out as a standalone package)

3. Trading Agent: The trained agent that makes decisions. (To be built on after of the Nautilus Adapter and simulated training environment) (3)

4. Ansible: For provisioning MetaTrader platforms automatically. (Optional for now)

## Disclaimer

TradeFlow is for educational purposes only. The developers are not responsible for any financial losses incurred while using this software. Please understand the inherent risks involved in trading before using any automated system.
