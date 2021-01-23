from telegram import Update
from telegram.ext import CommandHandler, CallbackContext


def register(dispatcher):
    dispatcher.add_handler(CommandHandler('start', __command__))


def __command__(update: Update, context: CallbackContext):
    text = "Hello, I am Polly Speaker Bot!"
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)
