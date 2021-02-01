import html
import logging
import traceback

from telegram import Update, ParseMode
from telegram.ext import Dispatcher, CallbackContext

from bot_env import bot_env

logger = logging.getLogger(__name__)


def register(dispatcher: Dispatcher):
    dispatcher.add_error_handler(_command)


def _command(update: Update, context: CallbackContext):
    logger.error(f"Cannot handle update: {context.error}", exc_info=context.error)
    if bot_env.config.developer_char_id != -1:
        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = ''.join(tb_list)
        message = (
            f"I got an error: <i>{context.error}</i>\n"
            f"<pre>{html.escape(tb_string)}</pre>"
        )
        context.bot.send_message(
            chat_id=bot_env.config.developer_char_id,
            text=message,
            parse_mode=ParseMode.HTML
        )
