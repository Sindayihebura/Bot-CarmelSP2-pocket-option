import os
import yfinance as yf
import pandas_ta as ta
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- 1. SERVEUR DE MAINTIEN EN LIGNE (POUR RENDER) ---
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
TOKEN = "8479698781:AAGSxcKisy5kb2FY4W1IBP_m34Ut5SVtg3I"

# --- 3. MOTEUR D'ANALYSE (RSI + EMA) ---
def get_signal(symbol):
    try:
        # Téléchargement des données (intervalle 5 min)
        data = yf.download(symbol, period="2d", interval="5m", progress=False)
        if data.empty: return "❌ Données indisponibles pour le moment."
        
        # Calcul des indicateurs
        data['RSI'] = ta.rsi(data['Close'], length=14)
        price = data['Close'].iloc[-1]
        last_rsi = data['RSI'].iloc[-1]
        
        # Logique de signal
        if last_rsi < 30:
            res = f"🟢 **SIGNAL ACHAT (BUY)**\n\n💰 Prix: `{price:.4f}`\n📉 RSI: `{last_rsi:.2f}`\n📢 État: **Sur-vendu** (Hausse probable)"
        elif last_rsi > 70:
            res = f"🔴 **SIGNAL VENTE (SELL)**\n\n💰 Prix: `{price:.4f}`\n📈 RSI: `{last_rsi:.2f}`\n📢 État: **Sur-acheté** (Baisse probable)"
        else:
            res = f"⏳ **ANALYSE : NEUTRE**\n\n💰 Prix: `{price:.4f}`\n📊 RSI: `{last_rsi:.2f}`\n📢 État: Aucun signal clair"
        return res
    except Exception as e:
        return f"⚠️ Erreur technique : {e}"

# --- 4. INTERFACE ET BOUTONS ---
def main_menu_keyboard():
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
    text = "🚀 **CARMEL CRYPTO SIGNAL PRO**\n\nBienvenue ! Sélectionnez un actif pour scanner les signaux de trading en temps réel (RSI 5min)."
    await update.message.reply_text(text, reply_markup=main_menu_keyboard(), parse_mode='Markdown')

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'back_to_menu':
        await query.edit_message_text("🚀 **MENU PRINCIPAL**\nSélectionnez un actif :", reply_markup=main_menu_keyboard(), parse_mode='Markdown')
    else:
        symbol = query.data
        await query.edit_message_text(text=f"🔍 Scan du marché pour **{symbol}** en cours...")
        signal = get_signal(symbol)
        
        # Bouton pour revenir
        back_btn = [[InlineKeyboardButton("🔙 Retour au Menu", callback_data='back_to_menu')]]
        await query.edit_message_text(text=signal, reply_markup=InlineKeyboardMarkup(back_btn), parse_mode='Markdown')

# --- 5. LANCEMENT ---
if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    print("Bot Pro démarré !")
    app.run_polling()
