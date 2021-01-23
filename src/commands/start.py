from telegram import Update, ParseMode
from telegram.ext import CommandHandler, CallbackContext


def register(dispatcher):
    dispatcher.add_handler(CommandHandler('start', __command__))


def __command__(update: Update, context: CallbackContext):
    text = f"Hello, I am {context.bot.name}\\!\n" \
           f"I can convert text into speech\\.\n" \
           f"To use me, start by typing `{context.bot.name}`\\."
    context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode=ParseMode.MARKDOWN_V2)
