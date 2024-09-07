import os
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, CallbackQueryHandler
from deep_translator import GoogleTranslator
from flask import Flask
import threading
import time

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

# ... (resto del código del bot sin cambios)

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port)

def keep_alive_job():
    while True:
        time.sleep(600)  # Espera 10 minutos
        logger.info("Performing keep-alive request")
        try:
            # Realiza una solicitud a tu propia ruta /keep-alive
            import requests
            requests.get(f"http://localhost:{os.environ.get('PORT', 5000)}/keep-alive")
        except Exception as e:
            logger.error(f"Error in keep-alive request: {e}")

def main() -> None:
    logger.info("Starting the bot")
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # ... (configuración del bot sin cambios)

    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=keep_alive_job, daemon=True).start()

    logger.info("Bot is ready to receive messages")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()