import os
from typing import Optional


class Config:
    bot_token: str
    inline_debounce_millis: int
    min_message_length: int
    max_message_length: int
    developer_char_id: int
    language_mappings: dict[str, str]

    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.inline_debounce_millis = int(os.getenv('TELEGRAM_INLINE_DEBOUNCE_MILLIS', "1000"))
        self.min_message_length = int(os.getenv('TELEGRAM_MIN_MESSAGE_LENGTH', "1"))
        self.max_message_length = int(os.getenv('TELEGRAM_MAX_MESSAGE_LENGTH', "255"))
        self.developer_char_id = int(os.getenv('TELEGRAM_DEVELOPER_CHAT_ID', "-1"))
        self.language_mappings = Config._parse_lang_mappings(os.getenv('LANGUAGE_DETECT_MAPPINGS'))
        self.aws = Config.Aws()

    @staticmethod
    def _parse_lang_mappings(mappings: Optional[str]) -> dict[str, str]:
        if mappings:
            result = {}
            for pair in mappings.split(','):
                l_from, l_to = pair.split('=', 2)
                if l_from and l_to:
                    result[l_from] = l_to
                else:
                    raise ValueError(f"Incorrect language mappings='{mappings}'")
            return result
        else:
            return {}

    class Aws:
        access_key_id: str
        secret_access_key: str
        region_name: str
        s3_bucket: str

        def __init__(self):
            self.access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
            self.secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            self.region_name = os.getenv('AWS_REGION_NAME')
            self.s3_bucket = os.getenv('AWS_S3_BUCKET')
