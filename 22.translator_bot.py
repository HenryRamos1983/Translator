import os
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, CallbackQueryHandler
from deep_translator import GoogleTranslator
from flask import Flask
import threading

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

    context.user_data['message_ids'] = []
    reply_keyboard = [
        ['Traducir al Español'], 
        ['Traducir al Inglés'],
        ['/delete']
    ]
    update.message.reply_text(
        message,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    )
    return TRANSLATING

def translate(update: Update, context: CallbackContext) -> int:
    logger.info(f"Translating message for user {update.effective_user.id}")
    text_to_translate = update.message.text.strip()
    
    if text_to_translate in ['Traducir al Español', 'Traducir al Inglés']:
        return start_translation(update, context)
    
    source_lang = context.user_data['source_lang']
    target_lang = context.user_data['target_lang']

    context.user_data['message_ids'].append(update.message.message_id)

    try:
        translated_text = GoogleTranslator(source=source_lang, target=target_lang).translate(text_to_translate)
        logger.info(f"Translation successful: '{text_to_translate}' -> '{translated_text}'")
        message = update.message.reply_text(f"{translated_text}")
        context.user_data['message_ids'].append(message.message_id)
    except Exception as e:
        logger.error(f"Translation error: {e}")
        error_message = update.message.reply_text("Lo siento, ocurrió un error al traducir. Por favor, intenta de nuevo.")
        context.user_data['message_ids'].append(error_message.message_id)

    return TRANSLATING

def delete_history(update: Update, context: CallbackContext) -> None:
    logger.info(f"Deleting history for user {update.effective_user.id}")
    query = update.callback_query
    query.answer()

    chat_id = update.effective_chat.id
    for message_id in context.user_data.get('message_ids', []):
        try:
            context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            logger.error(f"Error deleting message {message_id}: {e}")

    context.user_data['message_ids'] = []
    query.edit_message_text("Historial de traducciones borrado.")

def show_delete_button(update: Update, context: CallbackContext) -> None:
    logger.info(f"Showing delete button for user {update.effective_user.id}")
    keyboard = [[InlineKeyboardButton("Borrar historial", callback_data='delete_history')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('¿Quieres borrar el historial de traducciones?', reply_markup=reply_markup)

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port)

def main() -> None:
    logger.info("Starting the bot")
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

    threading.Thread(target=run_flask, daemon=True).start()

    logger.info("Bot is ready to receive messages")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
