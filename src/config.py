import os
from enum import Enum


class Config:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.inline_debounce_millis = int(os.getenv('TELEGRAM_INLINE_DEBOUNCE_MILLIS', "1000"))
        self.min_message_length = int(os.getenv('TELEGRAM_MIN_MESSAGE_LENGTH', "1"))
        self.max_message_length = int(os.getenv('TELEGRAM_MAX_MESSAGE_LENGTH', "255"))
        self.output_format = Config.OutputFormat.MP3.value
        output_format = os.getenv('TELEGRAM_AUDIO_OUTPUT_FORMAT')
        for f in Config.OutputFormat:
            if f.value['name'] == output_format:
                self.output_format = f.value
        self.aws = Config.Aws()

    class Aws:
        def __init__(self):
            self.access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
            self.secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            self.region_name = os.getenv('AWS_REGION_NAME')
            self.s3_bucket = os.getenv('AWS_S3_BUCKET')

    class OutputFormat(Enum):
        MP3 = dict(name='mp3', ext='mp3', mime_type='audio/mpeg')
        OGG = dict(name='ogg_vorbis', ext='ogg', mime_type='audio/ogg')
