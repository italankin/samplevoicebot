import concurrent.futures
import datetime
import logging
import re
import threading
from typing import Tuple, Optional

from telegram import InlineQueryResultVoice, Update
from telegram.error import BadRequest
from telegram.ext import Dispatcher, InlineQueryHandler, CallbackContext

from bot_env import bot_env
from fileuploader.fileuploader import FileUploader
from fileuploader.s3fileploader import S3FileUploader
from synthesizer.pollysynthesizer import PollySynthesizer
from synthesizer.synthesizer import Synthesizer, Language
from util.converter import convert_mp3_ogg_opus
from util.sanitizer import Sanitizer
from util.validator import Validator

logger = logging.getLogger(__name__)

synthesizer: Synthesizer
file_uploader: FileUploader
validator: Validator
sanitizer: Sanitizer
executor = concurrent.futures.ThreadPoolExecutor(max_workers=bot_env.config.max_workers)
request_lock = threading.Lock()
requests = {}
lang_text_pattern = re.compile("!(?P<language>[a-z]{2,3})\\s(?P<text>.*)")


def register(dispatcher: Dispatcher):
    global synthesizer, file_uploader, validator, sanitizer
    synthesizer = PollySynthesizer(bot_env.aws_session)
    file_uploader = S3FileUploader(bot_env.aws_session, bot_env.config.aws.s3_bucket)
    validator = Validator(bot_env.config.min_message_length, bot_env.config.max_message_length)
    sanitizer = Sanitizer(bot_env.config.max_message_length)
    dispatcher.add_handler(InlineQueryHandler(_command, run_async=True))
    if len(bot_env.config.prefetch_languages) > 0:
        dispatcher.job_queue.run_once(_prefetch_languages, 0)


def _command(update: Update, context: CallbackContext):
    query = update.inline_query.query
    job_name = str(update.effective_user.id)
    had_active_jobs = _remove_active_jobs(context, job_name)
    language, text = _parse_query(query)
    if not validator.validate(text):
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


def _parse_query(query: str) -> Tuple[Optional[Language], str]:
    text = sanitizer.sanitize(query)
    if text.startswith('!'):
        match = lang_text_pattern.fullmatch(text)
        if match:
            language = Language.from_name(match.group('language'))
            if language:
                return language, match.group('text')
            else:
                logger.debug(f"No supported language found for '{language}'")
    return None, text


def _synthesize_callback(context: CallbackContext):
    args = context.job.context
    _synthesize(args['update'], args['text'], args['language'])


def _synthesize(update: Update, text: str, language: Optional[Language]):
    bot_env.statistics.report_request()
    user_id = update.effective_user.id
    query_id = update.inline_query.id
    with request_lock:
        requests[user_id] = query_id
    tasks = []
    for voice in synthesizer.voices(text, language):
        tasks.append(executor.submit(_synthesize_request, voice=voice, text=text))
    inline_results = []
    for task in concurrent.futures.as_completed(tasks):
        with request_lock:
            if requests[user_id] != query_id:
                logger.debug(f"Stale query_id={query_id}, stop processing")
                return
        result = task.result()
        if result is None:
            continue
        (object_id, object_url, voice) = result
        result_voice = InlineQueryResultVoice(id=object_id, voice_url=object_url, title=f"{voice}:\n{text}")
        inline_results.append(result_voice)
    with request_lock:
        if requests[user_id] == query_id:
            del requests[user_id]
        else:
            logger.warning(f"query_id={query_id} is no longer valid")
            return
    try:
        update.inline_query.answer(results=inline_results, is_personal=True, cache_time=30)
    except BadRequest as e:
        # we probably did not fit into 10s window
        logger.error(f"Failed to answer inline query query_id={query_id}", exc_info=e)
        pass


def _synthesize_request(voice: str, text: str) -> Optional[Tuple[str, str, str]]:
    try:
        voice_bytes = synthesizer.synthesize(voice_id=voice, text=text)
        with convert_mp3_ogg_opus(voice_bytes) as f:
            result = file_uploader.upload(f)
            if result is None:
                return None
            (object_id, object_url) = result
            return object_id, object_url, voice
    except Exception as e:
        bot_env.statistics.report_synthesize_error()
        logger.error(f"Failed to synthesize voice={voice}, text='{text}': {e}", exc_info=e)
        return None


def _prefetch_languages(_):
    for name in bot_env.config.prefetch_languages:
        language = Language.from_name(name)
        if language:
            synthesizer.prefetch_voices(language)
