import os
import yfinance as yf
import pandas_ta as ta
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- CONFIGURATION ---
# REMPLACE BIEN LE TEXTE CI-DESSOUS PAR TON TOKEN TELEGRAM
TOKEN = "8479698781:AAGSxcKisy5kb2FY4W1IBP_m34Ut5SVtg3I" 

# --- FONCTION DE SIGNAL ---
def get_signal(symbol):
    try:
        data = yf.download(symbol, period="1d", interval="5m", progress=False)
        if data.empty: return "Erreur : Marché fermé ou symbole inconnu."
        
        data['RSI'] = ta.rsi(data['Close'], length=14)
        last_rsi = data['RSI'].iloc[-1]
        
        if last_rsi > 70:
            return f"🔴 SIGNAL VENTE (SELL)\nRSI: {last_rsi:.2f}\nZone de surachat."
        elif last_rsi < 30:
            return f"🟢 SIGNAL ACHAT (BUY)\nRSI: {last_rsi:.2f}\nZone de survente."
        else:
            return f"⏳ ATTENTE\nRSI: {last_rsi:.2f}\nPas de signal clair."
    except Exception as e:
        return f"Erreur : {e}"

# --- COMMANDES ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Analyse BTC/USD", callback_data='BTC-USD')],
        [InlineKeyboardButton("Analyse EUR/USD", callback_data='EURUSD=X')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📊 Choisissez un actif à analyser :", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    symbol = query.data
    await query.edit_message_text(text=f"🔍 Analyse de {symbol}...")
    res = get_signal(symbol)
    await query.edit_message_text(text=res)

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()
