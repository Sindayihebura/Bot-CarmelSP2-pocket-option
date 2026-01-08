import os
import yfinance as yf
import pandas_ta as ta
import threading
import math
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- SERVEUR DE MAINTIEN RENDER ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot Carmel Final OK')

def run_server():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# --- CONFIGURATION ---
# REMPLACE BIEN PAR TON NOUVEAU TOKEN CI-DESSOUS
TOKEN = "8179698781:AA6SXcKisy5kb2FY4WT18P_m34UL5SVtg3I"

# --- ANALYSE SÉCURISÉE ---
def get_signal(symbol):
    try:
        data = yf.download(symbol, period="3d", interval="5m", progress=False)
        if data.empty or len(data) < 20:
            return "❌ Marché fermé ou données indisponibles pour le moment."
        
        rsi_series = ta.rsi(data['Close'], length=14)
        if rsi_series is None or len(rsi_series) < 1:
            return "⏳ Calcul technique en pause... Réessayez."

        last_rsi = rsi_series.iloc[-1]
        price = data['Close'].iloc[-1]

        if math.isnan(last_rsi):
            return "⏳ Signal en cours de génération... Patientez 30s."

        # LOGIQUE DE SIGNAL
        if last_rsi < 35:
            return f"🟢 **SIGNAL ACHAT (BUY)**\n━━━━━━━━━━━━━━\n💰 Prix: `{price:.4f}`\n📉 RSI: `{last_rsi:.2f}`\n📢 État: **SUR-VENDU** (Opportunité)"
        elif last_rsi > 65:
            return f"🔴 **SIGNAL VENTE (SELL)**\n━━━━━━━━━━━━━━\n💰 Prix: `{price:.4f}`\n📈 RSI: `{last_rsi:.2f}`\n📢 État: **SUR-ACHETÉ** (Prudence)"
        else:
            return f"⏳ **ANALYSE : NEUTRE**\n━━━━━━━━━━━━━━\n💰 Prix: `{price:.4f}`\n📊 RSI: `{last_rsi:.2f}`\n📢 État: Aucun signal clair"
    except Exception:
        return "⚠️ Erreur de connexion aux marchés. Réessayez."

# --- MENU 16 ACTIFS ---
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
    await update.message.reply_text("🚀 **CARMEL TRADING BOT FINAL**\n\nChoisissez un actif pour obtenir un signal immédiat :", reply_markup=main_menu(), parse_mode='Markdown')

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'menu':
        await query.edit_message_text("🚀 **MENU PRINCIPAL** :", reply_markup=main_menu(), parse_mode='Markdown')
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
    print("Bot lancé avec succès!")
    app.run_polling(drop_pending_updates=True) # Cette ligne vide les anciens messages bloqués
