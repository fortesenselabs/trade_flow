# Intelligent Trading Bot Signal Forwarder

This Python script forwards trading signals from the [intelligent-trading-bot](https://github.com/asavinov/intelligent-trading-bot) Telegram channel to both WhatsApp and MetaTrader 5.

**Features:**

- Subscribes to the `intelligent-trading-bot` Telegram channel using telethon.
- Parses incoming messages for trading signals.
- Forwards parsed signals to a WhatsApp group or individual contact. [Not done]
- Sends the signals to MetaTrader 5 for potential execution (configuration required). [Currently in Progress]

**Requirements:**

- Python 3.8+
- `aiogram` library for Telegram integration (see installation instructions: [invalid URL removed])
- `twilio` library for WhatsApp integration (see installation instructions: [https://www.twilio.com/docs/whatsapp/quickstart](https://www.twilio.com/docs/whatsapp/quickstart))
- MetaTrader 5 API (see installation instructions: [https://www.mql5.com/en/docs/integration](https://www.mql5.com/en/docs/integration))

**Installation:**

1. Clone this repository or download the script.
2. Install required libraries:
   ```bash
   pip install aiogram twilio
   ```
3. Configure `config.py` (see below for details).

**Configuration:**

1. Create a `config.py` file in the same directory as the script.
2. Add the following configurations to `config.py`:

   ```python
   # Telegram API credentials
   BOT_TOKEN = 'YOUR_BOT_TOKEN'  # Replace with your bot token

   # WhatsApp details (optional)
   WHATSAPP_ACCOUNT_SID = YOUR_WHATSAPP_ACCOUNT_SID
   WHATSAPP_AUTH_TOKEN = YOUR_WHATSAPP_AUTH_TOKEN
   WHATSAPP_TARGET = 'whatsapp:+14155552671'  # Phone number or group chat ID

   # MetaTrader 5 details (optional)
   MT5_ACCOUNT = YOUR_MT5_ACCOUNT_NUMBER
   MT5_PASSWORD = YOUR_MT5_PASSWORD
   MT5_SERVER = YOUR_MT5_SERVER_ADDRESS
   ```

   - Replace placeholders with your actual credentials.
   - Obtain a Telegram bot token from BotFather.
   - Obtain a Twilio account and WhatsApp sandbox testing credentials (optional).
   - MetaTrader 5 details can be found in your trading platform settings (optional).

**Usage:**

1. Run the script: `python main.py`

**Disclaimer:**

This script is for educational purposes only. It is recommended to back-test any strategies before using them with real capital. You are solely responsible for any financial losses incurred while using this script.

## Credits

- https://github.com/fpierrem/telegram-aggregator/
- https://github.com/nsniteshsahni/telegram-channel-listener/
