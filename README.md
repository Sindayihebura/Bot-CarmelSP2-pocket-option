# Pocket Signal Bot

Telegram bot that calculates experimental CALL/PUT/NEUTRAL technical signals from public Binance spot candles.

## Important limitations
- This is a **signal/learning tool**, not an automated trader. It does not log in to Pocket Option, place trades, or guarantee profits.
- Binance spot prices may differ from Pocket Option prices, especially OTC instruments.
- Signals are not validated as profitable. Run proper chronological backtests and paper testing before considering any financial decision.
- Never put Telegram tokens or other secrets in source code. Set `BOT_TOKEN` as an environment variable.
- If a token was ever committed to GitHub, revoke it with BotFather and generate a new one. Removing it from the latest code does not remove it from Git history.

## Commands
- `/start` — show asset menu
- `/assets` — list supported assets
- `/signal BTC` — analyze BTC/USDT

Supported symbols: BTC, ETH, BNB, SOL, XRP, ADA, DOGE, LTC. Default candle interval: 5m.

## Run locally
Python 3.11+ recommended.

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Set BOT_TOKEN in your environment before starting:
python bot.py
```

## Free-hosting template (Render)
1. Push this repository to GitHub.
2. Create a new **Web Service** in Render and connect this repository.
3. Build command: `pip install -r requirements.txt`
4. Start command: `python bot.py`
5. Add environment variable `BOT_TOKEN` with a newly generated Telegram bot token. Optionally set `CANDLE_INTERVAL=5m`.
6. Deploy and inspect the logs. The health endpoint returns JSON at `/`.

Free plans and their availability/limits can change. A free service may sleep or restart; do not assume uninterrupted real-time signals. Never publish the token in GitHub, logs, screenshots, or chat.
