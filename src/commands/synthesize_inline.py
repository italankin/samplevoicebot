import datetime
import logging
from typing import Optional

from telegram import InlineQueryResultVoice, Update
from telegram.error import BadRequest
from telegram.ext import Dispatcher, InlineQueryHandler, CallbackContext

from bot_env import bot_env
from synthesizer.synthesizer import Language
from synthesizerfacade import synthesizer_facade

logger = logging.getLogger(__name__)


def register(dispatcher: Dispatcher):
    dispatcher.add_handler(InlineQueryHandler(_command, run_async=True))
    if len(bot_env.config.prefetch_languages) > 0:
        dispatcher.job_queue.run_once(_prefetch_languages, 0)


def _command(update: Update, context: CallbackContext):
    query = update.inline_query.query
    job_name = str(update.effective_user.id)
    had_active_jobs = _remove_active_jobs(context, job_name)
    language, text, is_valid = synthesizer_facade.parse_query(query, inline=True)
    if not is_valid:
        logger.debug(f"Invalid query='{query}', language='{language}' sanitized='{text}'")
        if had_active_jobs:
            update.inline_query.answer(results=[], is_personal=True)
        return
    context.job_queue.run_once(
        _synthesize_callback,
        when=datetime.timedelta(milliseconds=bot_env.config.inline_debounce_millis),
        name=job_name,
        context={'update': update, 'text': text, 'language': language}
    )


def _remove_active_jobs(context: CallbackContext, job_name: str) -> bool:
    active_jobs = context.job_queue.get_jobs_by_name(job_name)
    logger.debug(f"Active jobs for job_name={job_name}: {active_jobs}")
    if not active_jobs:
        return False
    for job in active_jobs:
        logger.debug(f"Remove job={job.name}")
        job.schedule_removal()
    return True


def _synthesize_callback(context: CallbackContext):
    args = context.job.context
    update: Update = args['update']
    text: str = args['text']
    language: Optional[Language] = args['language']
    bot_env.statistics.report_request()
    user_id = update.effective_user.id
    query_id = update.inline_query.id
    synthesized = synthesizer_facade.synthesize(user_id, query_id, text, language)
    inline_results = []
    for s in synthesized:
        result_voice = InlineQueryResultVoice(id=s.object_id, voice_url=s.object_url,
                                              title=f"{s.lang.value['flag']} {s.voice}:\n{s.text}")
        inline_results.append(result_voice)
    try:
        update.inline_query.answer(results=inline_results, is_personal=True, cache_time=30)
    except BadRequest as e:
        # we probably did not fit into 10s window
        logger.error(f"Failed to answer inline query query_id={query_id}", exc_info=e)


def _prefetch_languages(_):
    synthesizer_facade.prefetch_languages()
