import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, CallbackQueryHandler
from deep_translator import GoogleTranslator
from flask import Flask
import threading

# Load environment variables
load_dotenv()

# Get the token from the .env file
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# States for the ConversationHandler
TRANSLATING = 0

# Create a Flask app
app = Flask(name)

@app.route('/')
def home():
    return "Telegram Bot is running!"

# ... (rest of your existing Telegram bot code)

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

def main() -> None:
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^(Traducir al Español|Traducir al Inglés)$'), start_translation)],
        states={
            TRANSLATING: [MessageHandler(Filters.text & ~Filters.command, translate)]
        },
        fallbacks=[MessageHandler(Filters.regex('^(Traducir al Español|Traducir al Inglés)$'), start_translation)]
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler('delete', show_delete_button))
    dispatcher.add_handler(CallbackQueryHandler(delete_history, pattern='^delete_history$'))

    # Start the Flask server in a separate thread
    threading.Thread(target=run_flask, daemon=True).start()

    updater.start_polling()
    updater.idle()

if name == 'main':
    main()
