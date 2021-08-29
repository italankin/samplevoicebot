import datetime
import logging

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, Dispatcher

from commands.command import Command
from util.statistics import Statistics

logger = logging.getLogger(__name__)


class StatsCommand(Command):
    def __init__(self, statistics: Statistics, admin_id: int):
        self._admin_id = admin_id
        self._statistics = statistics

    def register(self, dispatcher: Dispatcher):
        dispatcher.add_handler(CommandHandler('stats', self._command))
        dispatcher.job_queue.run_daily(self._stats, time=datetime.time(0))

    def _command(self, update: Update, context: CallbackContext):
        if self._admin_id == -1 or update.effective_user.id != self._admin_id:
            return
        context.bot.send_message(chat_id=update.effective_chat.id, text=self._get_stats())

    def _stats(self, _):
        logger.info(f"Daily stats:\n{self._get_stats()}")
        logger.debug("Clearing stats for yesterday")
        self._statistics.reset()

    def _get_stats(self) -> str:
        return (
            f"Requests: {self._statistics.requests}\n"
            f"Synthesized chars: {self._statistics.synthesized_chars}\n"
            f"Errors: {self._statistics.errors}"
        )
