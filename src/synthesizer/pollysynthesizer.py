import logging
import threading
from typing import Optional, Tuple

import langdetect
from boto3 import session

from synthesizer.synthesizer import Synthesizer, Language, Voices
from util.statistics import Statistics

logger = logging.getLogger(__name__)


class PollySynthesizer(Synthesizer):
    _voices: dict[str, Voices]

    def __init__(self,
                 aws_session: session.Session,
                 statistics: Statistics,
                 language_mappings: dict[str, str],
                 config_voices: dict[str, list[str]]):
        self._polly = aws_session.client('polly')
        self._fetch_voices_lock = threading.Lock()
        self._statistics = statistics
        self._voices = dict()
        self._config_voices = config_voices
        self._language_mappings = language_mappings
        langdetect.DetectorFactory.seed = 0

    def synthesize(self, voice_id: str, text: str) -> bytes:
        logger.info(f"Synthesize request: voice_id={voice_id}, text='{text}'")
        response = self._polly.synthesize_speech(
            VoiceId=voice_id,
            OutputFormat='mp3',
            Text=text
        )
        if response['AudioStream'] is not None:
            self._statistics.report_synthesized(text)
            return response['AudioStream'].read()
        else:
            raise ValueError(f"Cannot read response for request: voice_id={voice_id}, text='{text[:10]}'")

    def voices(self, text: str, language: Optional[Language] = None) -> Tuple[Language, Voices]:
        lang = language or self._guess_language(text)
        language_code = lang.value['code']
        if language_code in self._voices:
            return lang, self._voices[language_code]
        with self._fetch_voices_lock:
            # check if we just fetched voices for a language
            if language_code in self._voices:
                return lang, self._voices[language_code]
            try:
                voices = self._fetch_voices(language_code)
                self._voices[language_code] = voices
                return lang, voices
            except Exception as e:
                logger.error(f"Failed to fetch voices for language={language_code}: {e}")
                return lang, Voices([], [])

    def prefetch_voices(self, language: Language):
        with self._fetch_voices_lock:
            try:
                language_code = language.value['code']
                logger.info(f"Prefetch voices for language_code={language_code}")
                self._voices[language_code] = self._fetch_voices(language_code)
            except Exception as e:
                logger.error(f"Failed to prefetch voices for language={language_code}: {e}")

    def _fetch_voices(self, language: str) -> Voices:
        if language in self._config_voices:
            logger.info(f"Fetching voices for language={language} from config")
            config_voices = self._config_voices[language]
            return Voices(config_voices, config_voices)
        response = self._polly.describe_voices(LanguageCode=language, IncludeAdditionalLanguageCodes=False)
        voices_list = response['Voices']
        if not voices_list:
            logger.warning(f"Received empty voices for language={language}")
            return Voices([], [])
        available_voices = [(voice['Id'], voice['Gender']) for voice in voices_list]
        inline_voices = PollySynthesizer._choose_inline_voices(available_voices, ['Female', 'Male'])
        voices = Voices([v['Id'] for v in voices_list], inline_voices)
        logger.info(f"Available voices for language={language}: {available_voices}, chosen voices={voices}")
        return voices

    def _guess_language(self, text: str) -> Language:
        try:
            lang_name = langdetect.detect(text)
        except Exception as e:
            logger.error(f"Cannot detect language: {e}", exc_info=e)
            lang_name = None
        logger.debug(f"Detected language name={lang_name} for text='{text}'")
        if lang_name in self._language_mappings:
            lang_name = self._language_mappings[lang_name]
        language = Language.from_name(lang_name) or Language.EN
        logger.info(f"Using language code={language.value['code']} for text='{text}'")
        return language

    @staticmethod
    def _choose_inline_voices(voices: list[Tuple[str, str]], genders: list[str]) -> list[str]:
        # to limit synthesize requests, select only one voice for each gender
        result = []
        for gender in genders:
            g_voices = [voice_id for (voice_id, voice_gender) in voices if voice_gender == gender]
            g_voices.sort()
            if len(g_voices) > 0:
                result.append(g_voices[0])
        return result
