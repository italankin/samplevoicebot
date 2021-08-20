import datetime
import logging

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, Dispatcher

from bot_env import bot_env

logger = logging.getLogger(__name__)


def register(dispatcher: Dispatcher):
    dispatcher.add_handler(CommandHandler('stats', _command))
    dispatcher.job_queue.run_daily(_stats, time=datetime.time(0))


def _command(update: Update, context: CallbackContext):
    if bot_env.config.admin_id == -1 or update.effective_user.id != bot_env.config.admin_id:
        return
    context.bot.send_message(chat_id=update.effective_chat.id, text=_get_stats())


def _stats(context: CallbackContext):
    logger.info(f"Daily stats:\n{_get_stats()}")
    logger.debug("Clearing stats for yesterday")
    bot_env.statistics.reset()


def _get_stats() -> str:
    return (
        f"Requests: {bot_env.statistics.requests}\n"
        f"Synthesized chars: {bot_env.statistics.synthesized_chars}\n"
        f"Errors: {bot_env.statistics.errors}"
    )
