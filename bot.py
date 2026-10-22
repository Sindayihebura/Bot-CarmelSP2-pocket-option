import json
import logging
import math
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

# Public Binance spot data only. This bot does not connect to Pocket Option
# and never places trades or requests deposits/passwords.
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=os.getenv("LOG_LEVEL", "INFO"),
)
log = logging.getLogger("pocket-signal-bot")
TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "8080"))
BASE_URL = "https://api.binance.com/api/v3/klines"
INTERVAL = os.getenv("CANDLE_INTERVAL", "5m")
SYMBOLS = {
    "BTC": "BTCUSDT", "ETH": "ETHUSDT", "BNB": "BNBUSDT",
    "SOL": "SOLUSDT", "XRP": "XRPUSDT", "ADA": "ADAUSDT",
    "DOGE": "DOGEUSDT", "LTC": "LTCUSDT",
}

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"status": "ok", "service": "pocket-signal-bot"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return

def start_health_server():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

def fetch_candles(symbol: str, limit: int = 250):
    response = requests.get(
        BASE_URL,
        params={"symbol": symbol, "interval": INTERVAL, "limit": limit},
        timeout=12,
        headers={"User-Agent": "PocketSignalBot/1.0"},
    )
    response.raise_for_status()
    rows = response.json()
    if not isinstance(rows, list) or len(rows) < 210:
        raise ValueError("Pas assez de bougies réelles pour calculer les indicateurs.")
    # Exclude the currently forming candle to avoid unstable signals.
    rows = rows[:-1]
    return [{
        "time": int(row[0]),
        "open": float(row[1]),
        "high": float(row[2]),
        "low": float(row[3]),
        "close": float(row[4]),
        "volume": float(row[5]),
        "closed_at": int(row[6]),
    } for row in rows]

def ema(values, period):
    alpha = 2.0 / (period + 1.0)
    out = []
    current = values[0]
    for value in values:
        current = alpha * value + (1.0 - alpha) * current
        out.append(current)
    return out

def rsi(values, period=14):
    gains, losses = [], []
    for previous, current in zip(values[:-1], values[1:]):
        change = current - previous
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))
    if len(gains) < period:
        return None
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    result = [50.0] * period
    for i in range(period, len(gains)):
        avg_gain = ((period - 1) * avg_gain + gains[i]) / period
        avg_loss = ((period - 1) * avg_loss + losses[i]) / period
        result.append(100.0 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss))
    return result[-1]

def analyze(symbol: str):
    candles = fetch_candles(symbol)
    closes = [c["close"] for c in candles]
    latest = candles[-1]
    # Refuse stale data instead of showing a misleading signal.
    age_ms = int(__import__("time").time() * 1000) - latest["closed_at"]
    interval_ms = {"1m": 60_000, "3m": 180_000, "5m": 300_000,
                   "15m": 900_000, "30m": 1_800_000, "1h": 3_600_000}.get(INTERVAL)
    if interval_ms is None:
        raise ValueError("Intervalle non pris en charge dans la configuration.")
    if age_ms > interval_ms * 3:
        raise ValueError("Données trop anciennes : aucun signal publié.")

    rsi_value = rsi(closes)
    ema20 = ema(closes, 20)[-1]
    ema50 = ema(closes, 50)[-1]
    ema12, ema26 = ema(closes, 12), ema(closes, 26)
    macd_values = [a - b for a, b in zip(ema12, ema26)]
    macd_signal = ema(macd_values, 9)[-1]
    macd = macd_values[-1]
    price = closes[-1]

    trend = "haussière" if ema20 > ema50 else "baissière" if ema20 < ema50 else "neutre"
    # Conservative confluence filter: otherwise publish NEUTRE.
    signal = "NEUTRE"
    reasons = []
    if price > ema20 > ema50 and macd > macd_signal and 50 <= rsi_value <= 68:
        signal = "CALL (hausse)"
        reasons.append("prix et EMA alignés à la hausse")
        reasons.append("MACD au-dessus de sa ligne de signal")
        reasons.append("RSI confirme sans surachat extrême")
    elif price < ema20 < ema50 and macd < macd_signal and 32 <= rsi_value <= 50:
        signal = "PUT (baisse)"
        reasons.append("prix et EMA alignés à la baisse")
        reasons.append("MACD sous sa ligne de signal")
        reasons.append("RSI confirme sans survente extrême")
    else:
        reasons.append("conditions non réunies : pas de signal directionnel")

    return {
        "signal": signal, "price": price, "rsi": rsi_value,
        "ema20": ema20, "ema50": ema50, "macd": macd,
        "macd_signal": macd_signal, "trend": trend,
        "time": latest["closed_at"], "reasons": reasons,
    }

def keyboard():
    rows, row = [], []
    for label in SYMBOLS:
        row.append(InlineKeyboardButton(label, callback_data=label))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🤖 *Pocket Signal Bot*\n\n"
        "Choisis un actif pour analyser les dernières bougies clôturées. "
        "Les données viennent du marché spot Binance, pas du flux Pocket Option.\n\n"
        "Commandes : /signal BTC, /assets",
        parse_mode="Markdown",
        reply_markup=keyboard(),
    )

async def assets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Actifs disponibles : " + ", ".join(SYMBOLS))

async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("Usage : /signal BTC (ou ETH, BNB, SOL...)")
        return
    key = context.args[0].upper()
    if key not in SYMBOLS:
        await update.effective_message.reply_text("Actif inconnu. Utilise /assets.")
        return
    await send_analysis(update.effective_message, key)

async def send_analysis(message, key: str):
    symbol = SYMBOLS[key]
    try:
        data = analyze(symbol)
        from datetime import datetime, timezone
        stamp = datetime.fromtimestamp(data["time"] / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        text = (
            f"📊 *{key}/USDT — intervalle {INTERVAL}*\n"
            f"Signal : *{data['signal']}*\n"
            f"Prix spot : {data['price']:.8g} USDT\n"
            f"RSI(14) : {data['rsi']:.1f}\n"
            f"EMA20 : {data['ema20']:.8g}\n"
            f"EMA50 : {data['ema50']:.8g}\n"
            f"MACD : {data['macd']:.8g} | Signal MACD : {data['macd_signal']:.8g}\n"
            f"Tendance : {data['trend']}\n"
            f"Dernière bougie clôturée : {stamp}\n"
            f"Motif : {data['reasons'][0]}\n\n"
            "_Signal technique expérimental, non validé comme stratégie rentable. "
            "Binance spot peut différer des actifs OTC/de la cotation Pocket Option. "
            "Aucun ordre n'est passé._"
        )
        await message.reply_text(text, parse_mode="Markdown")
    except (requests.RequestException, ValueError, KeyError, IndexError) as exc:
        log.warning("Analysis unavailable for %s: %s", symbol, exc)
        await message.reply_text(f"⚠️ Analyse indisponible pour {key}. Aucun signal publié.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data
    if key not in SYMBOLS:
        await query.edit_message_text("Actif non reconnu. Envoie /start.")
        return
    await send_analysis(query.message, key)

def main():
    if not TOKEN:
        raise RuntimeError("Variable secrète BOT_TOKEN manquante. Configure-la dans l'hébergeur.")
    start_health_server()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("assets", assets))
    app.add_handler(CommandHandler("signal", signal_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    log.info("Bot started; interval=%s", INTERVAL)
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
