import os
import yfinance as yf
import pandas_ta as ta
import threading
import math
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- 1. SERVEUR DE MAINTIEN EN LIGNE ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot Pro de Carmel est Actif')

def run_server():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# --- 2. CONFIGURATION ---
TOKEN = "8179698781:AA6SXcKisy5kb2FY4WT18P_m34UL5SVtg3I"

# --- 3. MOTEUR D'ANALYSE SÉCURISÉ ---
def get_signal(symbol):
    try:
        data = yf.download(symbol, period="2d", interval="5m", progress=False)
        
        if data.empty or len(data) < 15:
            return "❌ Marché fermé ou données insuffisantes. Réessayez plus tard."
        
        rsi_series = ta.rsi(data['Close'], length=14)
        
        if rsi_series is None or rsi_series.empty:
            return "⏳ Calcul technique impossible pour le moment."

        last_rsi = rsi_series.iloc[-1]
        price = data['Close'].iloc[-1]

        if math.isnan(last_rsi):
            return "⏳ Le signal est en cours de calcul... Patientez 1 minute."

        if last_rsi < 35:
            return f"🟢 **SIGNAL ACHAT (BUY)**\n━━━━━━━━━━━━━━\n💰 Prix: `{price:.4f}`\n📉 RSI: `{last_rsi:.2f}`\n📢 État: **Sur-vendu** (Hausse probable)"
        elif last_rsi > 65:
            return f"🔴 **SIGNAL VENTE (SELL)**\n━━━━━━━━━━━━━━\n💰 Prix: `{price:.4f}`\n📈 RSI: `{last_rsi:.2f}`\n📢 État: **Sur-acheté** (Baisse probable)"
        else:
            return f"⏳ **ANALYSE : NEUTRE**\n━━━━━━━━━━━━━━\n💰 Prix: `{price:.4f}`\n📊 RSI: `{last_rsi:.2f}`\n📢 État: Aucun signal clair"

    except Exception as e:
        return "⚠️ Erreur technique temporaire. Réessayez."

# --- 4. INTERFACE ---
def main_menu():
    keyboard = [
        [InlineKeyboardButton("₿ BTC/USD", callback_data='BTC-USD'), InlineKeyboardButton("💎 ETH/USD", callback_data='ETH-USD')],
        [InlineKeyboardButton("☀️ SOL/USD", callback_data='SOL-USD'), InlineKeyboardButton("🔶 BNB/USD", callback_data='BNB-USD')],
        [InlineKeyboardButton("🇪🇺 EUR/USD", callback_data='EURUSD=X'), InlineKeyboardButton("🥇 OR (GOLD)", callback_data='GC=F')],
        [InlineKeyboardButton("🛢️ PÉTROLE", callback_data='CL=F'), InlineKeyboardButton("🇺🇸 US30", callback_data='^DJI')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 **CARMEL CRYPTO PRO**\n\nChoisissez un actif :", reply_markup=main_menu(), parse_mode='Markdown')

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'back':
        await query.edit_message_text("🚀 **MENU PRINCIPAL**\nChoisissez un actif :", reply_markup=main_menu(), parse_mode='Markdown')
    else:
        symbol = query.data
        await query.edit_message_text(text=f"🔍 Scan de **{symbol}**...")
        res = get_signal(symbol)
        back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Retour au Menu", callback_data='back')]])
        await query.edit_message_text(text=res, reply_markup=back_btn, parse_mode='Markdown')

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()
