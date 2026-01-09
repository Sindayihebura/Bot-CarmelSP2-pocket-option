import os
import threading
import pandas as pd
import yfinance as yf
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ===================== SERVEUR KEEP ALIVE =====================
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Carmel Trading Bot Online')

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# ===================== CONFIG =====================
TOKEN = "8479698781:AAECcBK1EaPGvwPEX_xjx4jRt7iVS7UCay8"

# ===================== RSI SANS LIBRAIRIE =====================
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# ===================== ANALYSE =====================
def get_signal(symbol, timeframe):
    tf_map = {"1m": "1m", "5m": "5m", "15m": "15m"}
    period_map = {"1m": "1d", "5m": "3d", "15m": "7d"}

    data = yf.download(
        symbol,
        interval=tf_map[timeframe],
        period=period_map[timeframe],
        progress=False
    )

    if data.empty or len(data) < 20:
        return "❌ Données insuffisantes"

    rsi = calculate_rsi(data["Close"])
    last_rsi = rsi.iloc[-1]
    price = data["Close"].iloc[-1]

    if last_rsi < 30:
        signal = "🟢 ACHAT (BUY)"
    elif last_rsi > 70:
        signal = "🔴 VENTE (SELL)"
    else:
        signal = "⏳ NEUTRE"

    return (
        f"{signal}\n\n"
        f"💰 Prix : {price:.4f}\n"
        f"📊 RSI : {last_rsi:.2f}"
    )

# ===================== MENUS =====================
CRYPTOS = {
    "BTC": "BTC-USD", "ETH": "ETH-USD", "BNB": "BNB-USD", "SOL": "SOL-USD",
    "XRP": "XRP-USD", "ADA": "ADA-USD", "DOGE": "DOGE-USD", "DOT": "DOT-USD",
    "LINK": "LINK-USD", "AVAX": "AVAX-USD", "MATIC": "POL-USD", "LTC": "LTC-USD",
    "TRX": "TRX-USD", "SHIB": "SHIB-USD", "ATOM": "ATOM-USD", "XLM": "XLM-USD",
    "ICP": "ICP-USD", "APT": "APT-USD", "NEAR": "NEAR-USD", "FIL": "FIL-USD"
}

def crypto_menu():
    keyboard = []
    row = []
    for name, symbol in CRYPTOS.items():
        row.append(InlineKeyboardButton(name, callback_data=symbol))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def timeframe_menu(symbol):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1 MIN", callback_data=f"tf_1m_{symbol}")],
        [InlineKeyboardButton("5 MIN", callback_data=f"tf_5m_{symbol}")],
        [InlineKeyboardButton("15 MIN", callback_data=f"tf_15m_{symbol}")],
        [InlineKeyboardButton("⬅ Retour", callback_data="back")]
    ])

# ===================== COMMANDES =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 *CARMEL TRADING BOT*\n\nChoisis une crypto :",
        reply_markup=crypto_menu(),
        parse_mode="Markdown"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📘 *AIDE*\n\n"
        "/start - Démarrer le bot\n"
        "/strategie - Stratégie utilisée\n"
        "/risque - Gestion du risque\n"
        "/fonctionnement - Comment ça marche",
        parse_mode="Markdown"
    )

async def strategie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 *STRATÉGIE*\n\n"
        "• RSI 14\n"
        "• Achat < 30\n"
        "• Vente > 70\n"
        "• Confirmation par tendance",
        parse_mode="Markdown"
    )

async def risque(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚠️ *RISQUE*\n\n"
        "• Ne jamais miser plus de 5%\n"
        "• Toujours attendre confirmation\n"
        "• Le trading comporte des risques",
        parse_mode="Markdown"
    )

async def fonctionnement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚙️ *FONCTIONNEMENT*\n\n"
        "1️⃣ Choisis une crypto\n"
        "2️⃣ Choisis la bougie\n"
        "3️⃣ Reçois le signal",
        parse_mode="Markdown"
    )

# ===================== BOUTONS =====================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "back":
        await query.edit_message_text("Choisis une crypto :", reply_markup=crypto_menu())
        return

    if query.data.startswith("tf_"):
        _, tf, symbol = query.data.split("_")
        result = get_signal(symbol, tf)
        await query.edit_message_text(
            f"📈 *Signal {symbol} ({tf})*\n\n{result}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Nouveau scan", callback_data="back")]
            ])
        )
        return

    await query.edit_message_text(
        f"⏱ Choisis le délai pour {query.data}",
        reply_markup=timeframe_menu(query.data)
    )

# ===================== MAIN =====================
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("strategie", strategie))
    app.add_handler(CommandHandler("risque", risque))
    app.add_handler(CommandHandler("fonctionnement", fonctionnement))
    app.add_handler(CallbackQueryHandler(buttons))

    app.run_polling()

if __name__ == "__main__":
    main()
