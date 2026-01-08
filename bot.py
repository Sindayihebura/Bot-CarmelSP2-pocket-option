import os
import yfinance as yf
import pandas_ta as ta
import threading
import math
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot Active')

def run_server():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# --- UTILISEZ CE JETON EXACT ---
TOKEN = "8479698781:AAECcBK1EaPGvwPEX_xjx4jRt7iVS7UCay8"

def get_signal(symbol):
    try:
        data = yf.download(symbol, period="3d", interval="5m", progress=False)
        if data.empty or len(data) < 20:
            return "❌ Données indisponibles."
        rsi = ta.rsi(data['Close'], length=14)
        if rsi is None or rsi.empty or math.isnan(rsi.iloc[-1]):
            return "⏳ Calcul en cours..."
        last_rsi = rsi.iloc[-1]
        price = data['Close'].iloc[-1]
        if last_rsi < 35: return f"🟢 ACHAT\nPrix: {price:.4f}\nRSI: {last_rsi:.2f}"
        if last_rsi > 65: return f"🔴 VENTE\nPrix: {price:.4f}\nRSI: {last_rsi:.2f}"
        return f"⏳ NEUTRE\nRSI: {last_rsi:.2f}"
    except:
        return "⚠️ Erreur technique."

def main_menu():
    keyboard = [[InlineKeyboardButton("₿ BTC", callback_data='BTC-USD'), InlineKeyboardButton("🥇 GOLD", callback_data='GC=F')]]
    return InlineKeyboardMarkup(keyboard)

async def start(update, context):
    await update.message.reply_text("📊 Sélectionnez un actif :", reply_markup=main_menu())

async def handle(update, context):
    query = update.callback_query
    await query.answer()
    res = get_signal(query.data)
    await query.edit_message_text(text=res, reply_markup=main_menu())

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle))
    app.run_polling(drop_pending_updates=True)
