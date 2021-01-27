import concurrent.futures
import datetime
import logging
from typing import Tuple, Optional

from telegram import InlineQueryResultVoice, Update
from telegram.ext import Dispatcher, InlineQueryHandler, CallbackContext

from bot_env import bot_env
from fileuploader.fileuploader import FileUploader
from fileuploader.s3fileploader import S3FileUploader
from synthesizer.pollysynthesizer import PollySynthesizer
from synthesizer.synthesizer import Synthesizer
from util.converter import convert_mp3_ogg_opus
from util.sanitizer import Sanitizer
from util.validator import Validator

logger = logging.getLogger(__name__)

synthesizer: Synthesizer
file_uploader: FileUploader
validator: Validator
sanitizer: Sanitizer
executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)


def register(dispatcher: Dispatcher):
    global synthesizer, file_uploader, validator, sanitizer
    synthesizer = PollySynthesizer(bot_env.aws_session)
    file_uploader = S3FileUploader(bot_env.aws_session, bot_env.config.aws.s3_bucket)
    validator = Validator(bot_env.config.min_message_length, bot_env.config.max_message_length)
    sanitizer = Sanitizer(bot_env.config.max_message_length)
    dispatcher.add_handler(InlineQueryHandler(__command__))


def __command__(update: Update, context: CallbackContext):
    job_name = str(update.effective_user.id)
    had_active_jobs = __remove_active_jobs__(context, job_name)
    text = sanitizer.sanitize(update.inline_query.query)
    if not validator.validate(text):
        logger.debug(f"Invalid query='{update.inline_query.query}', sanitized='{text}'")
        if had_active_jobs:
            update.inline_query.answer(results=[], is_personal=True)
        return
    context.job_queue.run_once(
        __synthesize_callback__,
        when=datetime.timedelta(milliseconds=bot_env.config.inline_debounce_millis),
        name=job_name,
        context={'update': update, 'text': text}
    )


def __remove_active_jobs__(context: CallbackContext, job_name: str) -> bool:
    active_jobs = context.job_queue.get_jobs_by_name(job_name)
    logger.debug(f"Active jobs for job_name={job_name}: {active_jobs}")
    if not active_jobs:
        return False
    for job in active_jobs:
        logger.debug(f"Remove job={job.name}")
        job.schedule_removal()
    return True


def __synthesize_callback__(context: CallbackContext):
    args = context.job.context
    __synthesize__(args['update'], args['text'])


def __synthesize__(update: Update, text: str):
    tasks = []
    for voice in synthesizer.voices(text):
        tasks.append(executor.submit(__synthesize_voice__, voice=voice, text=text))
    inline_results = []
    for task in concurrent.futures.as_completed(tasks):
        result = task.result()
        if result is None:
            continue
        (object_id, object_url, voice) = result
        result_voice = InlineQueryResultVoice(
            id=object_id,
            voice_url=object_url,
            title=f"{voice}:\n{text}"
        )
        inline_results.append(result_voice)
    update.inline_query.answer(results=inline_results, is_personal=True, cache_time=120)


def __synthesize_voice__(voice: str, text: str) -> Optional[Tuple[str, str, str]]:
    try:
        voice_bytes = synthesizer.synthesize(voice_id=voice, text=text)
        with convert_mp3_ogg_opus(voice_bytes) as f:
            result = file_uploader.upload(f)
            if result is None:
                return None
            (object_id, object_url) = result
            return object_id, object_url, voice
    except Exception as e:
        logger.error(f"Failed to synthesize voice={voice}, text='{text}': {e}", exc_info=e)
        return None
