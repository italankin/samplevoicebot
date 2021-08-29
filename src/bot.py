from boto3 import session
from telegram.ext import Updater

import commands.error_handler
import commands.start
import commands.stats
import commands.synthesize
import commands.synthesize_inline
from config import Config
from fileuploader.s3fileploader import S3FileUploader
from synthesizer.pollysynthesizer import PollySynthesizer
from synthesizerfacade import SynthesizerFacade
from util.sanitizer import Sanitizer
from util.statistics import Statistics
from util.validator import Validator


class Bot:
    def __init__(self, config: Config):
        self._updater = Updater(token=config.bot_token, workers=config.max_workers)
        self._dispatcher = self._updater.dispatcher
        self._statistics = Statistics()
        self._aws_session = session.Session(
            aws_access_key_id=config.aws.access_key_id,
            aws_secret_access_key=config.aws.secret_access_key,
            region_name=config.aws.region_name
        )
        self._synthesizer_facade = SynthesizerFacade(
            PollySynthesizer(self._aws_session, self._statistics, config.language_mappings, config.voices),
            Validator(config.min_message_length, config.max_message_length),
            Sanitizer(config.max_message_length),
            S3FileUploader(self._aws_session, config.aws.s3_bucket),
            self._statistics,
            config.max_workers
        )
        self._commands = [
            commands.start.StartCommand(),
            commands.synthesize.SynthesizeCommand(self._synthesizer_facade),
            commands.synthesize_inline.SynthesizeInlineCommand(
                self._synthesizer_facade, self._statistics, config.prefetch_languages, config.inline_debounce_millis
            ),
            commands.stats.StatsCommand(self._statistics, config.admin_id),
            commands.error_handler.ErrorCommand(config.developer_chat_id)
        ]

    def run(self):
        for command in self._commands:
            command.register(self._dispatcher)
        self._updater.start_polling()
        self._updater.idle()
