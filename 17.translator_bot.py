import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, CallbackQueryHandler
from deep_translator import GoogleTranslator

# Cargar variables de entorno
load_dotenv()

# Obtener el token del archivo .env
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Estados para el ConversationHandler
CHOOSING_LANGUAGE, TRANSLATING = range(2)

def iniciar(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [
        ['Traducir al Español'], 
        ['Traducir al Inglés'],
        ['/start', '/delete']
    ]
    update.message.reply_text(
        'Hola! Por favor, elige el idioma al que quieres traducir:',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return CHOOSING_LANGUAGE

def set_language(update: Update, context: CallbackContext) -> int:
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
        update.message.reply_text("Por favor, elige 'Español' o 'Inglés'.")
        return CHOOSING_LANGUAGE

    context.user_data['message_ids'] = []  # Lista para almacenar los IDs de los mensajes
    update.message.reply_text(message)
    return TRANSLATING

def translate(update: Update, context: CallbackContext) -> int:
    text_to_translate = update.message.text.strip()
    source_lang = context.user_data['source_lang']
    target_lang = context.user_data['target_lang']

    # Guardar el ID del mensaje del usuario
    context.user_data['message_ids'].append(update.message.message_id)

    try:
        translated_text = GoogleTranslator(source=source_lang, target=target_lang).translate(text_to_translate)
        message = update.message.reply_text(f" {translated_text}")
        context.user_data['message_ids'].append(message.message_id)  # Guardar el ID del mensaje de traducción
    except Exception as e:
        print(f"Error de traducción: {e}")
        error_message = update.message.reply_text("Lo siento, ocurrió un error al traducir. Por favor, intenta de nuevo.")
        context.user_data['message_ids'].append(error_message.message_id)

    return TRANSLATING

def delete_history(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    chat_id = update.effective_chat.id
    for message_id in context.user_data.get('message_ids', []):
        try:
            context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            print(f"Error al borrar mensaje {message_id}: {e}")

    context.user_data['message_ids'] = []  # Limpiar la lista de IDs de mensajes
    query.edit_message_text("Historial de traducciones borrado.")

def show_delete_button(update: Update, context: CallbackContext) -> None:
    keyboard = [[InlineKeyboardButton("Borrar historial", callback_data='delete_history')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('¿Quieres borrar el historial de traducciones?', reply_markup=reply_markup)

def main() -> None:
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', iniciar)],
        states={
            CHOOSING_LANGUAGE: [MessageHandler(Filters.regex('^(Traducir al Inglés|Traducir al Español)$'), set_language)],
            TRANSLATING: [MessageHandler(Filters.text & ~Filters.command, translate)]
        },
        fallbacks=[CommandHandler('start', iniciar)]
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler('delete', show_delete_button))
    dispatcher.add_handler(CallbackQueryHandler(delete_history, pattern='^delete_history$'))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()