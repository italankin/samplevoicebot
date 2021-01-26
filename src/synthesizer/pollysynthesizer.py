import logging
import re
import threading
from typing import Optional, Tuple

from boto3 import session

from bot_env import bot_env
from synthesizer.synthesizer import Synthesizer

logger = logging.getLogger(__name__)


class PollySynthesizer(Synthesizer):
    __voices__: dict[str, Optional[list[str]]]

    def __init__(self, aws_session: session.Session):
        self.__polly__ = aws_session.client('polly')
        self.__lock__ = threading.Lock()
        self.__voices__ = dict()

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

    def voices(self, text: str) -> list[str]:
        language = PollySynthesizer.__guess_language__(text)
        if language in self.__voices__:
            return self.__voices__[language]
        try:
            self.__lock__.acquire()
            voices = self.__fetch_voices__(language)
            self.__voices__[language] = voices
            return voices
        except Exception as e:
            logger.error(f"Failed to fetch voices for language={language}: {e}")
            return []
        finally:
            self.__lock__.release()

    def __fetch_voices__(self, language: str) -> list[str]:
        response = self.__polly__.describe_voices(LanguageCode=language, IncludeAdditionalLanguageCodes=False)
        voices_list = response['Voices']
        if not voices_list:
            logger.warning(f"Received empty voices for language={language}")
            self.__voices__[language] = []
            return []
        available_voices = [(voice['Id'], voice['Gender']) for voice in voices_list]
        voices = PollySynthesizer.__choose_voices__(available_voices, ['Female', 'Male'])
        logger.info(f"Available voices for language={language}: {available_voices}, chosen voices={voices}")
        return voices

    @staticmethod
    def __guess_language__(text: str) -> str:
        p = re.compile("[А-я]")
        if p.search(text):
            return 'ru-RU'
        return 'en-US'

    @staticmethod
    def __choose_voices__(voices: list[Tuple[str, str]], genders: list[str]) -> list[str]:
        # to limit synthesize requests, select only one voice for each gender
        result = []
        for gender in genders:
            sorted_voices = [voice_id for (voice_id, voice_gender) in voices if voice_gender == gender]
            sorted_voices.sort()
            if len(sorted_voices) > 0:
                result.append(sorted_voices[0])
        return result
