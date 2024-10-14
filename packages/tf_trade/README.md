# TFTrade (An Intelligent Trading Bot Signals Forwarder)

This script forwards trading signals from the [intelligent-trading-bot](https://github.com/asavinov/intelligent-trading-bot) Telegram channel to both WhatsApp and MetaTrader 5.

## Features

- Subscribes to the `intelligent-trading-bot` Telegram channel using telethon.
- Parses incoming messages for trading signals.
- Forwards parsed signals to a WhatsApp group or individual contact. [Not done]
- Sends the signals to MetaTrader 5 for potential execution (configuration required).

## Requirements

- Python 3.8+
- `telethon` library for Telegram integration (see installation instructions)
- MetaTrader 5 API (see installation instructions: [https://www.mql5.com/en/docs/integration](https://www.mql5.com/en/docs/integration))

## Installation

1. Clone this repository or download the script.
2. Install required libraries:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure `.env` (see below for details).

## Configuration

1. Create a `.env` file in the same directory as the script.
2. Add the following configurations to `.env`:

   ```python
   # Telegram API credentials
   API_ID = ""
   API_HASH = ""
   PHONE_NUMBER = ""

   # MetaTrader 5 details (optional)
   MT5_ACCOUNT = YOUR_MT5_ACCOUNT_NUMBER
   MT5_PASSWORD = YOUR_MT5_PASSWORD
   MT5_SERVER = YOUR_MT5_SERVER_ADDRESS
   ```

   - Replace placeholders with your actual credentials.
   - MetaTrader 5 details can be found in your trading platform settings (optional).

## Usage

```bash
$ python main.py
```

## TODOs

- Train RL Agents for the top 5 assets from the Quantreo ML Project (data platform -> MT5)

## Credits

- https://github.com/asavinov/intelligent-trading-bot/
- https://github.com/fpierrem/telegram-aggregator/
- https://github.com/nsniteshsahni/telegram-channel-listener/

**Disclaimer:**

This script is for educational purposes only. It is recommended to back-test any strategies before using them with real capital. You are solely responsible for any financial losses incurred while using this script.
