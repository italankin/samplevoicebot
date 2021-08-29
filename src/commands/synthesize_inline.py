import datetime
import logging
from typing import Optional

from telegram import InlineQueryResultVoice, Update
from telegram.error import BadRequest
from telegram.ext import Dispatcher, InlineQueryHandler, CallbackContext

from commands.command import Command
from synthesizer.synthesizer import Language
from synthesizerfacade import SynthesizerFacade
from util.statistics import Statistics

logger = logging.getLogger(__name__)


class SynthesizeInlineCommand(Command):
    def __init__(self,
                 synthesizer_facade: SynthesizerFacade,
                 statistics: Statistics,
                 prefetch_languages: list[str],
                 inline_debounce_millis: int):
        self._synthesizer_facade = synthesizer_facade
        self._statistics = statistics
        self._prefetch_languages_list = prefetch_languages
        self._inline_debounce_millis = inline_debounce_millis

    def register(self, dispatcher: Dispatcher):
        dispatcher.add_handler(InlineQueryHandler(self._command, run_async=True))
        if len(self._prefetch_languages_list) > 0:
            dispatcher.job_queue.run_once(self._prefetch_languages, 0)

    def _command(self, update: Update, context: CallbackContext):
        query = update.inline_query.query
        job_name = str(update.effective_user.id)
        had_active_jobs = self._remove_active_jobs(context, job_name)
        language, text, is_valid = self._synthesizer_facade.parse_query(query, inline=True)
        if not is_valid:
            logger.debug(f"Invalid query='{query}', language='{language}' sanitized='{text}'")
            if had_active_jobs:
                update.inline_query.answer(results=[], is_personal=True)
            return
        context.job_queue.run_once(
            self._synthesize_callback,
            when=datetime.timedelta(milliseconds=self._inline_debounce_millis),
            name=job_name,
            context={'update': update, 'text': text, 'language': language}
        )

    def _remove_active_jobs(self, context: CallbackContext, job_name: str) -> bool:
        active_jobs = context.job_queue.get_jobs_by_name(job_name)
        logger.debug(f"Active jobs for job_name={job_name}: {active_jobs}")
        if not active_jobs:
            return False
        for job in active_jobs:
            logger.debug(f"Remove job={job.name}")
            job.schedule_removal()
        return True

    def _synthesize_callback(self, context: CallbackContext):
        args: dict = context.job.context
        update: Update = args['update']
        text: str = args['text']
        language: Optional[Language] = args['language']
        self._statistics.report_request()
        user_id = update.effective_user.id
        query_id = update.inline_query.id
        synthesized = self._synthesizer_facade.synthesize(user_id, query_id, text, language)
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

    def _prefetch_languages(self, _):
        self._synthesizer_facade.prefetch_languages(self._prefetch_languages_list)
        self._prefetch_languages_list = None
