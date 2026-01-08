import os
import yfinance as yf
import pandas_ta as ta
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- 1. GARDIEN DE CONNEXION (POUR RENDER) ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot Carmel Pro Operationnel')

def run_server():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# --- 2. CONFIGURATION ---
TOKEN = "8479698781:AAGSxcKisy5kb2FY4W1IBP_m34Ut5SVtg3I"

# --- 3. LOGIQUE DE TRADING ---
def get_signal(symbol):
    try:
        data = yf.download(symbol, period="2d", interval="5m", progress=False)
        if data.empty: return "❌ Marché fermé ou données indisponibles."
        
        data['RSI'] = ta.rsi(data['Close'], length=14)
        last_rsi = data['RSI'].iloc[-1]
        price = data['Close'].iloc[-1]
        
        if last_rsi < 35:
            return f"🟢 **SIGNAL ACHAT (BUY)**\n━━━━━━━━━━━━━━\n💰 Prix: `{price:.4f}`\n📉 RSI: `{last_rsi:.2f}`\n📢 État: **Sur-vendu** (Opportunité)"
        elif last_rsi > 65:
            return f"🔴 **SIGNAL VENTE (SELL)**\n━━━━━━━━━━━━━━\n💰 Prix: `{price:.4f}`\n📈 RSI: `{last_rsi:.2f}`\n📢 État: **Sur-acheté** (Danger)"
        else:
            return f"⏳ **ANALYSE : NEUTRE**\n━━━━━━━━━━━━━━\n💰 Prix: `{price:.4f}`\n📊 RSI: `{last_rsi:.2f}`\n📢 État: Pas de signal clair"
    except Exception as e:
        return f"⚠️ Erreur: {e}"

# --- 4. INTERFACE ---
def main_menu():
    keyboard = [
        [InlineKeyboardButton("₿ BTC/USD", callback_data='BTC-USD'), InlineKeyboardButton("💎 ETH/USD", callback_data='ETH-USD')],
        [InlineKeyboardButton("☀️ SOL/USD", callback_data='SOL-USD'), InlineKeyboardButton("🔶 BNB/USD", callback_data='BNB-USD')],
        [InlineKeyboardButton("💧 XRP/USD", callback_data='XRP-USD'), InlineKeyboardButton("🔹 ADA/USD", callback_data='ADA-USD')],
        [InlineKeyboardButton("🇪🇺 EUR/USD", callback_data='EURUSD=X'), InlineKeyboardButton("🇬🇧 GBP/USD", callback_data='GBPUSD=X')],
        [InlineKeyboardButton("🇯🇵 USD/JPY", callback_data='JPY=X'), InlineKeyboardButton("🥇 OR (GOLD)", callback_data='GC=F')],
        [InlineKeyboardButton("🛢️ PÉTROLE", callback_data='CL=F'), InlineKeyboardButton("🇺🇸 US30", callback_data='^DJI')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 **CARMEL CRYPTO SIGNAL PRO**\n\nSélectionnez un actif pour obtenir un signal en 5min :", reply_markup=main_menu(), parse_mode='Markdown')

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'menu':
        await query.edit_message_text("🚀 **MENU PRINCIPAL**\nChoisissez un actif :", reply_markup=main_menu(), parse_mode='Markdown')
    else:
        symbol = query.data
        await query.edit_message_text(text=f"🔍 Scan de **{symbol}**...")
        res = get_signal(symbol)
        back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Retour au Menu", callback_data='menu')]])
        await query.edit_message_text(text=res, reply_markup=back_btn, parse_mode='Markdown')

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    print("Bot lancé avec succès !")
    app.run_polling()
