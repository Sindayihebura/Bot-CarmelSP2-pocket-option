import os
import yfinance as yf
import pandas_ta as ta
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- BLOC MAGIQUE POUR RENDER (Serveur Web) ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot en ligne !')

def run_server():
    # Utilise le port 8080 que tu as configuré sur Render
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# Lance le serveur dans un fil séparé (threading)
threading.Thread(target=run_server, daemon=True).start()

# --- TON TOKEN TELEGRAM ---
TOKEN = "8479698781:AAGSxcKisy5kb2FY4W1IBP_m34Ut5SVtg3I" # <--- METS TON TOKEN ICI !

# --- LOGIQUE DE SIGNAL ---
def get_signal(symbol):
    try:
        data = yf.download(symbol, period="1d", interval="5m", progress=False)
        if data.empty: return "Données indisponibles."
        data['RSI'] = ta.rsi(data['Close'], length=14)
        last_rsi = data['RSI'].iloc[-1]
        if last_rsi > 70: return f"🔴 VENTE (SELL)\nRSI: {last_rsi:.2f}"
        elif last_rsi < 30: return f"🟢 ACHAT (BUY)\nRSI: {last_rsi:.2f}"
        else: return f"⏳ ATTENTE\nRSI: {last_rsi:.2f}"
    except Exception as e: return f"Erreur: {e}"

async def start(update, context):
    keyboard = [[InlineKeyboardButton("Analyse BTC/USD", callback_data='BTC-USD')],
                [InlineKeyboardButton("Analyse EUR/USD", callback_data='EURUSD=X')]]
    await update.message.reply_text("📊 Choisissez un actif :", reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update, context):
    query = update.callback_query
    await query.answer()
    symbol = query.data
    await query.edit_message_text(text=f"🔍 Analyse de {symbol}...")
    await query.edit_message_text(text=get_signal(symbol))

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    print("Bot démarré...")
    app.run_polling()
