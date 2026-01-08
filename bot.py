import os
import yfinance as yf
import pandas_ta as ta
import threading
import math
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- 1. SERVEUR DE MAINTIEN RENDER ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'BOT CARMEL OPERATIONNEL')

def run_server():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# --- 2. CONFIGURATION ---
TOKEN = "8479698781:AAGSxcKisy5kb2FY4W1IBP_m34Ut5SVtg3I"

# --- 3. ANALYSE SÉCURISÉE ---
def get_signal(symbol):
    try:
        data = yf.download(symbol, period="3d", interval="5m", progress=False)
        if data.empty or len(data) < 20:
            return "❌ Marché fermé ou données indisponibles."
        
        rsi_series = ta.rsi(data['Close'], length=14)
        if rsi_series is None or rsi_series.empty:
            return "⏳ Calcul en cours... réessayez."

        last_rsi = rsi_series.iloc[-1]
        price = data['Close'].iloc[-1]

        if math.isnan(last_rsi):
            return "⏳ Analyse en cours... patientez 30s."

        if last_rsi < 35:
            return f"🟢 **SIGNAL ACHAT (BUY)**\n━━━━━━━━━━━━━━\n💰 Prix: `{price:.4f}`\n📉 RSI: `{last_rsi:.2f}`\n📢 État: **SUR-VENDU**"
        elif last_rsi > 65:
            return f"🔴 **SIGNAL VENTE (SELL)**\n━━━━━━━━━━━━━━\n💰 Prix: `{price:.4f}`\n📈 RSI: `{last_rsi:.2f}`\n📢 État: **SUR-ACHETÉ**"
        else:
            return f"⏳ **ANALYSE : NEUTRE**\n━━━━━━━━━━━━━━\n💰 Prix: `{price:.4f}`\n📊 RSI: `{last_rsi:.2f}`"
    except Exception:
        return "⚠️ Erreur technique temporaire."

# --- 4. INTERFACE ---
def main_menu():
    keyboard = [
        [InlineKeyboardButton("₿ BTC", callback_data='BTC-USD'), InlineKeyboardButton("💎 ETH", callback_data='ETH-USD')],
        [InlineKeyboardButton("☀️ SOL", callback_data='SOL-USD'), InlineKeyboardButton("🔶 BNB", callback_data='BNB-USD')],
        [InlineKeyboardButton("💧 XRP", callback_data='XRP-USD'), InlineKeyboardButton("🔹 ADA", callback_data='ADA-USD')],
        [InlineKeyboardButton("🐕 DOGE", callback_data='DOGE-USD'), InlineKeyboardButton("🟣 DOT", callback_data='DOT1-USD')],
        [InlineKeyboardButton("🔗 LINK", callback_data='LINK-USD'), InlineKeyboardButton("🚀 MATIC", callback_data='POL-USD')],
        [InlineKeyboardButton("🇪🇺 EUR/USD", callback_data='EURUSD=X'), InlineKeyboardButton("🇬🇧 GBP/USD", callback_data='GBPUSD=X')],
        [InlineKeyboardButton("🥇 OR (GOLD)", callback_data='GC=F'), InlineKeyboardButton("🛢️ PÉTROLE", callback_data='CL=F')],
        [InlineKeyboardButton("🇺🇸 US30", callback_data='^DJI'), InlineKeyboardButton("📊 NASDAQ", callback_data='^IXIC')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 **CARMEL TRADING PRO**\nSignal RSI (5min) disponible :", reply_markup=main_menu(), parse_mode='Markdown')

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'menu':
        await query.edit_message_text("🚀 **MENU PRINCIPAL** :", reply_markup=main_menu(), parse_mode='Markdown')
    else:
        symbol = query.data
        await query.edit_message_text(text=f"🔍 Scan de **{symbol}**...")
        res = get_signal(symbol)
        back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Retour", callback_data='menu')]])
        await query.edit_message_text(text=res, reply_markup=back_btn, parse_mode='Markdown')

# --- 5. LANCEMENT AVEC NETTOYAGE DES CONFLITS ---
if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    print("Bot démarré !")
    # drop_pending_updates=True élimine les erreurs de conflit au démarrage
    app.run_polling(drop_pending_updates=True)
