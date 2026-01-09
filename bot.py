import os
import threading
import yfinance as yf
import pandas_ta as ta
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ================= KEEP ALIVE =================
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot Carmel Running')

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# ================= CONFIG =================
TOKEN = "8479698781:AAECcBK1EaPGvwPEX_xjx4jRt7iVS7UCay8"

CRYPTOS = [
    "BTC-USD","ETH-USD","BNB-USD","SOL-USD","XRP-USD",
    "ADA-USD","DOGE-USD","DOT-USD","MATIC-USD","LINK-USD",
    "AVAX-USD","TRX-USD","LTC-USD","BCH-USD","UNI-USD",
    "ATOM-USD","XLM-USD","ICP-USD","APT-USD","NEAR-USD"
]

# ================= STRATEGIE =================
def analyse(symbol, tf):
    tf_map = {"1m": "1m", "5m": "5m", "15m": "15m"}
    period_map = {"1m": "1d", "5m": "3d", "15m": "5d"}

    df = yf.download(
        symbol,
        interval=tf_map[tf],
        period=period_map[tf],
        progress=False
    )

    if df.empty:
        return "❌ Données indisponibles."

    df["RSI"] = ta.rsi(df["Close"], length=14)
    rsi = df["RSI"].iloc[-1]
    price = df["Close"].iloc[-1]

    if rsi < 35:
        signal = "🟢 ACHAT"
    elif rsi > 65:
        signal = "🔴 VENTE"
    else:
        signal = "⏳ ATTENTE"

    return price, rsi, signal

# ================= MENUS =================
def crypto_menu():
    keyboard = []
    for i in range(0, len(CRYPTOS), 2):
        row = [InlineKeyboardButton(CRYPTOS[i], callback_data=CRYPTOS[i])]
        if i + 1 < len(CRYPTOS):
            row.append(InlineKeyboardButton(CRYPTOS[i+1], callback_data=CRYPTOS[i+1]))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def timeframe_menu(symbol):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1 MIN", callback_data=f"tf_1m_{symbol}")],
        [InlineKeyboardButton("5 MIN", callback_data=f"tf_5m_{symbol}")],
        [InlineKeyboardButton("15 MIN", callback_data=f"tf_15m_{symbol}")],
    ])

def expiration_menu(symbol, tf):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏱ 1-2 min", callback_data=f"exp_2_{symbol}_{tf}")],
        [InlineKeyboardButton("⏱ 3-5 min", callback_data=f"exp_5_{symbol}_{tf}")],
        [InlineKeyboardButton("⏱ 10-15 min", callback_data=f"exp_15_{symbol}_{tf}")]
    ])

# ================= COMMANDES =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 BOT CARMEL SIGNALS\n\nChoisis une crypto :",
        reply_markup=crypto_menu()
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📘 AIDE\n\n"
        "Ce bot fournit des signaux basés sur RSI.\n"
        "1️⃣ Choisis une crypto\n"
        "2️⃣ Choisis le timeframe\n"
        "3️⃣ Choisis le temps de mise\n\n"
        "Commandes:\n"
        "/start\n"
        "/strategie\n"
        "/risque"
    )

async def strategie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 STRATÉGIE\n\n"
        "RSI 14\n"
        "RSI < 35 : ACHAT\n"
        "RSI > 65 : VENTE\n"
        "Sinon : ATTENTE"
    )

async def risque(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚠️ GESTION DU RISQUE\n\n"
        "• Toujours tester en compte démo\n"
        "• 1 à 3 % par trade\n"
        "• Aucun bot ne garantit des gains"
    )

# ================= BOUTONS =================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data in CRYPTOS:
        await query.edit_message_text(
            f"⏱ Choisis le timeframe pour {data}",
            reply_markup=timeframe_menu(data)
        )

    elif data.startswith("tf_"):
        _, tf, symbol = data.split("_")
        await query.edit_message_text(
            f"⌛ Choisis le temps de mise\nCrypto: {symbol}\nTF: {tf}",
            reply_markup=expiration_menu(symbol, tf)
        )

    elif data.startswith("exp_"):
        _, exp, symbol, tf = data.split("_")
        price, rsi, signal = analyse(symbol, tf)

        await query.edit_message_text(
            f"{signal}\n\n"
            f"🪙 Actif : {symbol}\n"
            f"💰 Prix : {price:.4f}\n"
            f"📊 RSI : {rsi:.2f}\n"
            f"⏱ Bougie : {tf}\n"
            f"⌛ Mise : {exp} min"
        )

# ================= MAIN =================
if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("strategie", strategie))
    app.add_handler(CommandHandler("risque", risque))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()
