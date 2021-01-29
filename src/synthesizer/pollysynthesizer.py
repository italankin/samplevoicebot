import logging
import threading
from typing import Optional, Tuple

import langdetect
from boto3 import session

from bot_env import bot_env
from synthesizer.synthesizer import Synthesizer, Language

logger = logging.getLogger(__name__)


class PollySynthesizer(Synthesizer):
    __voices__: dict[str, Optional[list[str]]]

    def __init__(self, aws_session: session.Session):
        self.__polly__ = aws_session.client('polly')
        self.__lock__ = threading.Lock()
        self.__voices__ = dict()
        langdetect.DetectorFactory.seed = 0

    def synthesize(self, voice_id: str, text: str) -> bytes:
        logger.info(f"Synthesize request: voice_id={voice_id}, text='{text}'")
        response = self.__polly__.synthesize_speech(
            VoiceId=voice_id,
            OutputFormat='mp3',
            Text=text
        )
        if response['AudioStream'] is not None:
            return response['AudioStream'].read()
        else:
            raise ValueError(f"Cannot read response for request: voice_id={voice_id}, text='{text[:10]}'")

    def voices(self, text: str, language: Optional[Language] = None) -> list[str]:
        language_code = (language or PollySynthesizer.__guess_language__(text)).value['code']
        if language_code in self.__voices__:
            return self.__voices__[language_code]
        with self.__lock__:
            try:
                voices = self.__fetch_voices__(language_code)
                self.__voices__[language_code] = voices
                return voices
            except Exception as e:
                logger.error(f"Failed to fetch voices for language={language_code}: {e}")
                return []

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
    def __guess_language__(text: str) -> Language:
        lang_name = langdetect.detect(text)
        logger.debug(f"Detected language name={lang_name} for text='{text}'")
        if lang_name in bot_env.config.language_mappings:
            lang_name = bot_env.config.language_mappings[lang_name]
        language = Language.from_name(lang_name) or Language.EN
        logger.info(f"Using language code={language.value['code']} for text='{text}'")
        return language

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
