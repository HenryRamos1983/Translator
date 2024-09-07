import os
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, CallbackQueryHandler
from deep_translator import GoogleTranslator
from flask import Flask
import threading
import time
import requests

# Configurar logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Obtener el token del archivo .env
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
logger.info(f"Token loaded: {'*' * (len(TOKEN) - 4) + TOKEN[-4:]}")

# Estados para el ConversationHandler
TRANSLATING = 0

# Crear una aplicación Flask
app = Flask(__name__)

@app.route('/')
def home():
    logger.info("Home route accessed")
    return "¡El Bot de Telegram está funcionando!"

@app.route('/keep-alive')
def keep_alive():
    logger.info("Keep-alive route accessed")
    return "Bot is alive", 200

def start(update: Update, context: CallbackContext) -> int:
    logger.info(f"Start command received from user {update.effective_user.id}")
    reply_keyboard = [['Traducir al Español'], ['Traducir al Inglés']]
    update.message.reply_text(
        '¡Hola! Soy tu bot traductor. ¿Qué deseas hacer?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return TRANSLATING

def start_translation(update: Update, context: CallbackContext) -> int:
    logger.info(f"Translation started by user {update.effective_user.id}")
    user_choice = update.message.text
    if user_choice == 'Traducir al Español':
        context.user_data['target_lang'] = 'es'
        context.user_data['source_lang'] = 'en'
        message = "Has elegido traducir al Español. Ahora puedes enviarme texto en Inglés y lo traduciré al Español."
    elif user_choice == 'Traducir al Inglés':
        context.user_data['target_lang'] = 'en'
        context.user_data['source_lang'] = 'es'
        message = "Has elegido traducir al Inglés. Ahora puedes enviarme texto en Español y lo traduciré al Inglés."
    else:
        message = "Por favor, elige 'Traducir al Español' o 'Traducir al Inglés'."
        return ConversationHandler.END

    update.message.reply_text(message)
    return TRANSLATING

def translate(update: Update, context: CallbackContext) -> int:
    logger.info(f"Translating message for user {update.effective_user.id}")
    text_to_translate = update.message.text.strip()
    
    if text_to_translate in ['Traducir al Español', 'Traducir al Inglés']:
        return start_translation(update, context)
    
    source_lang = context.user_data.get('source_lang', 'auto')
    target_lang = context.user_data.get('target_lang', 'es')

    try:
        translated_text = GoogleTranslator(source=source_lang, target=target_lang).translate(text_to_translate)
        logger.info(f"Translation successful: '{text_to_translate}' -> '{translated_text}'")
        update.message.reply_text(f"{translated_text}")
    except Exception as e:
        logger.error(f"Translation error: {e}")
        update.message.reply_text("Lo siento, ocurrió un error al traducir. Por favor, intenta de nuevo.")

    return TRANSLATING

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port)

def keep_alive_job():
    while True:
        time.sleep(600)  # Espera 10 minutos
        logger.info("Performing keep-alive request")
        try:
            requests.get(f"http://localhost:{os.environ.get('PORT', 5000)}/keep-alive")
        except Exception as e:
            logger.error(f"Error in keep-alive request: {e}")

def main() -> None:
    logger.info("Starting the bot")
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start),
                      MessageHandler(Filters.regex('^(Traducir al Español|Traducir al Inglés)$'), start_translation)],
        states={
            TRANSLATING: [MessageHandler(Filters.text & ~Filters.command, translate)]
        },
        fallbacks=[MessageHandler(Filters.regex('^(Traducir al Español|Traducir al Inglés)$'), start_translation)]
    )

    dispatcher.add_handler(conv_handler)

    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=keep_alive_job, daemon=True).start()

    logger.info("Bot is ready to receive messages")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()