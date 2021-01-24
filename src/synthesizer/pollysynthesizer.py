import logging

from boto3 import session

from bot_env import bot_env
from synthesizer.synthesizer import Synthesizer

logger = logging.getLogger(__name__)


class PollySynthesizer(Synthesizer):
    def __init__(self, aws_session: session.Session):
        self.__polly__ = aws_session.client('polly')

    def synthesize(self, voice_id: str, text: str) -> object:
        logger.debug(f"Synthesize request: voice_id={voice_id}, text='{text}'")
        response = self.__polly__.synthesize_speech(
            VoiceId=voice_id,
            OutputFormat=bot_env.config.output_format['name'],
            Text=text
        )
        if response['AudioStream'] is not None:
            return response['AudioStream']
        else:
            raise ValueError(f'Cannot read response for request: voice_id={voice_id}, text={text[:10]}')

    def voices(self) -> list[str]:
        return ['Maxim', 'Tatyana']  # TODO fetch actual voice_ids from Polly
