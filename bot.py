import os
import time
import threading
import pandas as pd
import yfinance as yf
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ================= KEEP ALIVE =================
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Carmel Bot Online")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(("0.0.0.0", port), SimpleHandler).serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# ================= TOKEN =================
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN manquant")

# ================= USERS =================
users = {}  # user_id : {"capital","start","active","signals_sent","last_signal_time"}

# ================= CRYPTOS =================
CRYPTOS = {
    "BTC": "BTC-USD", "ETH": "ETH-USD", "BNB": "BNB-USD", "SOL": "SOL-USD",
    "XRP": "XRP-USD", "ADA": "ADA-USD", "DOGE": "DOGE-USD", "DOT": "DOT-USD",
    "LTC": "LTC-USD", "AVAX": "AVAX-USD", "LINK": "LINK-USD", "TRX": "TRX-USD"
}

# ================= INDICATEURS =================
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta>0,0).rolling(period).mean()
    loss = -delta.where(delta<0,0).rolling(period).mean()
    rs = gain/loss
    return 100 - (100/(1+rs))

def calculate_ema(series, period=50):
    return series.ewm(span=period, adjust=False).mean()

def calculate_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line

def calculate_bollinger(series, period=20):
    sma = series.rolling(period).mean()
    std = series.rolling(period).std()
    upper = sma + 2*std
    lower = sma - 2*std
    return upper, lower

def calculate_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()

# ================= ANALYSE =================
def get_signal(symbol):
    try:
        data = yf.download(symbol, interval="5m", period="7d", progress=False)
        if data.empty or len(data)<20:
            return "❌ Données insuffisantes"

        close = data["Close"]
        rsi = calculate_rsi(close).iloc[-1]
        ema50 = calculate_ema(close,50).iloc[-1]
        ema200 = calculate_ema(close,200).iloc[-1]
        macd_line, signal_line = calculate_macd(close)
        macd = macd_line.iloc[-1] - signal_line.iloc[-1]
        upper, lower = calculate_bollinger(close)
        price = close.iloc[-1]
        atr = calculate_atr(data).iloc[-1]
        volume = data["Volume"].iloc[-1]

        # LOGIQUE SIGNAL
        trend = "bull" if price>ema50 and price>ema200 else "bear"
        signal = "⏳ NEUTRE"
        if rsi<30 and trend=="bull" and macd>0 and price<lower:
            signal = "🟢 ACHAT"
        elif rsi>70 and trend=="bear" and macd<0 and price>upper:
            signal = "🔴 VENTE"

        return f"{signal}\n💰 Prix: {price:.4f}\n📊 RSI: {rsi:.2f}\n📈 Trend: {trend}\n📊 ATR: {atr:.4f}\n📊 Volume: {volume}"
    except Exception as e:
        return f"⚠️ Erreur analyse: {e}"

# ================= MENU =================
def crypto_menu():
    kb, row = [], []
    for k, v in CRYPTOS.items():
        row.append(InlineKeyboardButton(k, callback_data=v))
        if len(row)==2:
            kb.append(row)
            row=[]
    if row: kb.append(row)
    return InlineKeyboardMarkup(kb)

# ================= COMMANDES =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 *CARMEL TRADING BOT*\n\nEnvoie ton capital de départ (min 5 USDT)\nEx: 10",
        parse_mode="Markdown"
    )

async def capital(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cap = float(update.message.text)
        if cap<5:
            await update.message.reply_text("❌ Minimum 5 USDT")
            return
        uid = update.effective_user.id
        users[uid] = {"capital":cap,"start":cap,"active":True,
                      "signals_sent":{crypto:0 for crypto in CRYPTOS.values()},
                      "last_signal_time":{crypto:0 for crypto in CRYPTOS.values()}}
        await update.message.reply_text("✅ Capital enregistré\nChoisis une crypto:", reply_markup=crypto_menu())
    except:
        await update.message.reply_text("❌ Veuillez envoyer un nombre valide")

# ================= LOGIQUE SIGNAL =================
def can_send_signal(user, crypto):
    max_signaux = 5
    intervalle = 24*3600 / max_signaux
    last = user["last_signal_time"].get(crypto,0)
    if time.time()-last < intervalle:
        return False
    if user["signals_sent"].get(crypto,0)>=max_signaux:
        return False
    if not user["active"]:
        return False
    return True

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = update.effective_user.id
    await query.answer()
    user = users.get(uid)
    if not user:
        await query.edit_message_text("⛔ Envoie ton capital d'abord (/start)")
        return
    crypto = query.data
    if not can_send_signal(user,crypto):
        await query.edit_message_text(f"⏱ Pas encore de signal pour {crypto} ou max atteint")
        return
    signal = get_signal(crypto)
    # Protection capital fictif
    if user["capital"]<=user["start"]*0.5:
        user["active"]=False
        await query.edit_message_text("⛔ STOP -50% atteint pour protection")
        return
    user["signals_sent"][crypto]+=1
    user["last_signal_time"][crypto]=time.time()
    await query.edit_message_text(f"📈 Signal {crypto}:\n\n{signal}")

# ================= MAIN =================
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("capital",capital))
    app.add_handler(CallbackQueryHandler(buttons))
    app.run_polling()

if __name__=="__main__":
    main()
