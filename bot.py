import logging
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Remplace par ton Token reçu de BotFather
TOKEN = "8479698781:AAGSxcKisy5kb2FY4W1IBP_m34Ut5SVtg3I"

# Dictionnaires pour stocker les préférences des utilisateurs (Plus tard : Base de données)
user_data = {}

async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data[user_id] = {} # Création du profil
    
    welcome_msg = (
        "🌍 Bienvenue sur votre Assistant de Trading !\n\n"
        "Pour commencer, configurons votre profil pour qu'il "
        "corresponde à votre pays et vos besoins sur Pocket Option."
    )
    
    # Boutons de réglages
    keyboard = [['🌍 Choisir Pays', '⏳ Délai Bougie'], ['💰 Montant Mise', '📈 Démarrer Scan']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(welcome_msg, reply_markup=reply_markup)

async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    user_id = update.message.from_user.id

    if text == '🌍 Choisir Pays':
        await update.message.reply_text("Entrez votre pays (ex: Burundi, France) :")
    elif text == '⏳ Délai Bougie':
        # Liste des délais demandés : S5, S10... M1... D1
        await update.message.reply_text("Choisissez votre délai (S5, S30, M1, M5, H1) :")
    elif text == '💰 Montant Mise':
        await update.message.reply_text("Indiquez le montant de votre mise en $ :")
    else:
        await update.message.reply_text("Option enregistrée ! Nous préparons l'analyse...")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot allumé... En attente d'utilisateurs.")
    app.run_polling()

if __name__ == '__main__':
    main()