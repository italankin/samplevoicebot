import html
import logging
import traceback

from telegram import ParseMode
from telegram.ext import Dispatcher, CallbackContext

from commands.command import Command

logger = logging.getLogger(__name__)


class ErrorCommand(Command):
    def __init__(self, developer_chat_id: int):
        self._developer_chat_id = developer_chat_id

    def register(self, dispatcher: Dispatcher):
        dispatcher.add_error_handler(self._command)

    def _command(self, _, context: CallbackContext):
        logger.error(f"Cannot handle update: {context.error}", exc_info=context.error)
        if self._developer_chat_id != -1:
            tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
            tb_string = ''.join(tb_list)
            message = (
                f"I got an error: <i>{context.error}</i>\n"
                f"<pre>{html.escape(tb_string)}</pre>"
            )
            context.bot.send_message(
                chat_id=self._developer_chat_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
