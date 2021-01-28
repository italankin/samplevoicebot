from telegram import Update, ParseMode
from telegram.ext import CommandHandler, CallbackContext, Dispatcher

from synthesizer.synthesizer import Language

supported_languages = ", ".join([f"`{lang.value['name']}`" for lang in Language])


def register(dispatcher: Dispatcher):
    dispatcher.add_handler(CommandHandler('start', __command__))


def __command__(update: Update, context: CallbackContext):
    text = (
        f"Hello, I am {context.bot.name}\\!\n"
        f"I can convert text into speech\\.\n"
        f"To use me, start typing `{context.bot.name}` in any chat\\."
    )
    context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode=ParseMode.MARKDOWN_V2)
    text = (
        f"If you want me to read text in a specific language, "
        f"you can insert `!` followed by language code, for example: "
        f"`{context.bot.name} !ru 12345`\n"
        f"Supported languages are: {supported_languages}"
    )
    context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode=ParseMode.MARKDOWN_V2)
