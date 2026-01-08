import os
import yfinance as yf
import pandas_ta as ta
import threading
import math
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- SERVEUR DE MAINTIEN ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot Carmel Final Ready')

def run_server():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# --- CONFIG ---
TOKEN = "8479698781:AAECcBK1EaPGvwPEX_xjx4jRt7iVS7UCay8"

# --- LOGIQUE D'ANALYSE ---
def get_signal(symbol, timeframe):
    try:
        # Correspondance des timeframes pour yfinance
        tf_map = {"1m": "1m", "5m": "5m", "15m": "15m"}
        period_map = {"1m": "1d", "5m": "3d", "15m": "5d"}
        
        data = yf.download(symbol, period=period_map[timeframe], interval=tf_map[timeframe], progress=False)
        
        if data.empty or len(data) < 20:
            return "❌ Données indisponibles pour ce délai."
        
        rsi = ta.rsi(data['Close'], length=14)
        last_rsi = rsi.iloc[-1]
        price = data['Close'].iloc[-1]
        
        expirations = {"1m": "2-3 min", "5m": "10-15 min", "15m": "30-45 min"}
        reco_time = expirations[timeframe]

        if last_rsi < 35:
            res = f"🟢 **ACHAT (BUY)**\n💰 Prix: `{price:.4f}`\n📊 RSI: `{last_rsi:.2f}`\n⏱️ Exp: **{reco_time}**"
        elif last_rsi > 65:
            res = f"🔴 **VENTE (SELL)**\n💰 Prix: `{price:.4f}`\n📊 RSI: `{last_rsi:.2f}`\n⏱️ Exp: **{reco_time}**"
        else:
            res = f"⏳ **NEUTRE**\n💰 Prix: `{price:.4f}`\n📊 RSI: `{last_rsi:.2f}`\n📢 Attendre."
        return res
    except:
        return "⚠️ Erreur de connexion."

# --- MENUS ---
def asset_menu():
    keyboard = [
        [InlineKeyboardButton("₿ BTC", callback_data='BTC-USD'), InlineKeyboardButton("💎 ETH", callback_data='ETH-USD')],
        [InlineKeyboardButton("☀️ SOL", callback_data='SOL-USD'), InlineKeyboardButton("🔶 BNB", callback_data='BNB-USD')],
        [InlineKeyboardButton("💧 XRP", callback_data='XRP-USD'), InlineKeyboardButton("🔹 ADA", callback_data='ADA-USD')],
        [InlineKeyboardButton("🐕 DOGE", callback_data='DOGE-USD'), InlineKeyboardButton("🟣 DOT", callback_data='DOT1-USD')],
        [InlineKeyboardButton("🔗 LINK", callback_data='LINK-USD'), InlineKeyboardButton("🚀 MATIC", callback_data='POL-USD')],
        [InlineKeyboardButton("🇪🇺 EUR/USD", callback_data='EURUSD=X'), InlineKeyboardButton("🇬🇧 GBP/USD", callback_data='GBPUSD=X')],
        [InlineKeyboardButton("🥇 GOLD", callback_data='GC=F'), InlineKeyboardButton("🛢️ OIL", callback_data='CL=F')],
        [InlineKeyboardButton("🇺🇸 US30", callback_data='^DJI'), InlineKeyboardButton("📊 NASDAQ", callback_data='^IXIC')]
    ]
    return InlineKeyboardMarkup(keyboard)

def timeframe_menu(symbol):
    keyboard = [
        [InlineKeyboardButton("1 MINUTE", callback_data=f"tf_1m_{symbol}")],
        [InlineKeyboardButton("5 MINUTES", callback_data=f"tf_5m_{symbol}")],
        [InlineKeyboardButton("15 MINUTES", callback_data=f"tf_15m_{symbol}")],
        [InlineKeyboardButton("🔙 Retour", callback_data="back_assets")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- GESTIONNAIRES ---
async def start(update, context):
    await update.message.reply_text("🚀 **CARMEL TRADING POCKET**\nChoisissez un actif :", reply_markup=asset_menu())

async def button_handler(update, context):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "back_assets":
        await query.edit_message_text("🚀 Choisissez un actif :", reply_markup=asset_menu())
    
    elif data.startswith("tf_"):
        # Format: tf_1m_BTC-USD
        parts = data.split("_")
        tf = parts[1]
        symbol = parts[2]
        await query.edit_message_text(f"🔍 Analyse de **{symbol}** en **{tf}**...")
        result = get_signal(symbol, tf)
        back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Nouveau Scan", callback_data="back_assets")]])
        await query.edit_message_text(f"📊 **RESULTAT {symbol} ({tf})**\n\n{result}", reply_markup=back_btn, parse_mode='Markdown')

    else:
        # L'utilisateur a choisi l'actif, on demande le temps
        symbol = data
        await query.edit_message_text(f"⏱️ **{symbol}**\nChoisissez votre délai d'analyse :", reply_markup=timeframe_menu(symbol))

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling(drop_pending_updates=True)
