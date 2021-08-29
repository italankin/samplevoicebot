import logging

from telegram import ParseMode
from telegram.ext import Dispatcher, CallbackContext

from commands.command import Command

logger = logging.getLogger(__name__)


class ErrorCommand(Command):
    def __init__(self, admin_id: int):
        self._admin_id = admin_id

    def register(self, dispatcher: Dispatcher):
        dispatcher.add_error_handler(self._command)

    def _command(self, _, context: CallbackContext):
        logger.error(f"Cannot handle update: {context.error}", exc_info=context.error)
        if self._admin_id != -1:
            message = (
                f"I got an error: <i>{context.error}</i>\n"
            )
            context.bot.send_message(
                chat_id=self._admin_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
