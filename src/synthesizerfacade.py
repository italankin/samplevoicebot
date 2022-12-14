import concurrent.futures
import logging
import re
import threading
from typing import Optional, Tuple, List, IO

from fileuploader.fileuploader import FileUploader
from synthesizer.synthesizer import Language, Synthesizer, Voices
from util.converter import convert_mp3_ogg_opus
from util.sanitizer import Sanitizer
from util.statistics import Statistics
from util.validator import Validator

logger = logging.getLogger(__name__)

lang_text_pattern = re.compile("!(?P<language>[a-z]{2,3})\\s(?P<text>.*)", re.DOTALL)


class SynthesizedObject:
    object_id: str
    object_url: str
    lang: Language
    voice: str
    text: str

    def __init__(self, object_id: str, object_url: str, lang: Language, voice: str, text: str):
        self.object_id = object_id
        self.object_url = object_url
        self.lang = lang
        self.voice = voice
        self.text = text


class SynthesizerFacade:
    def __init__(self,
                 synthesizer: Synthesizer,
                 validator: Validator,
                 sanitizer: Sanitizer,
                 file_uploader: FileUploader,
                 statistics: Statistics,
                 max_workers: int):
        self._synthesizer = synthesizer
        self._validator = validator
        self._sanitizer = sanitizer
        self._file_uploader = file_uploader
        self._statistics = statistics
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self._request_lock = threading.Lock()
        self._requests = {}

    def prefetch_languages(self, prefetch_languages: list[str]):
        for name in prefetch_languages:
            language = Language.from_name(name)
            if language:
                self._synthesizer.prefetch_voices(language)

    def voices(self, text, language: Optional[Language]) -> Voices:
        return self._synthesizer.voices(text, language)[1]

    def parse_query(self, query: str, inline: bool = False) -> Tuple[Optional[Language], str, bool]:
        text = self._sanitizer.sanitize(query, inline)
        if text.startswith('!'):
            match = lang_text_pattern.fullmatch(text)
            if match:
                language = Language.from_name(match.group('language'))
                if language:
                    query_text = match.group('text')
                    is_valid = self._validator.validate(query_text)
                    return language, match.group('text'), is_valid
                else:
                    logger.debug(f"No supported language found for '{language}'")
        is_valid = self._validator.validate(text)
        return None, text, is_valid

    def synthesize(
            self,
            user_id: str,
            query_id: Optional[str],
            text: str,
            language: Optional[Language],
            inline: bool = False
    ) -> List[SynthesizedObject]:
        self._statistics.report_request()
        if query_id:
            with self._request_lock:
                self._requests[user_id] = query_id
        tasks = []
        lang, voices = self._synthesizer.voices(text, language)
        voices_list = voices.inline_voices if inline else voices.all_voices
        for voice in voices_list:
            tasks.append(self._executor.submit(self._synthesize_request, voice=voice, text=text))
        results = []
        for task in concurrent.futures.as_completed(tasks):
            if query_id:
                with self._request_lock:
                    if user_id not in self._requests or self._requests[user_id] != query_id:
                        logger.debug(f"Stale query_id={query_id}, stop processing")
                        return []
            result = task.result()
            if result is None:
                continue
            (object_id, object_url, voice) = result
            results.append(SynthesizedObject(object_id, object_url, lang, voice, text))
        if query_id:
            with self._request_lock:
                if self._requests[user_id] == query_id:
                    del self._requests[user_id]
                else:
                    logger.warning(f"query_id={query_id} is no longer valid")
                    return []
        return results

    def synthesize_bytes(self, voice: str, text: str) -> Optional[IO]:
        self._statistics.report_request()
        try:
            voice_bytes = self._synthesizer.synthesize(voice_id=voice, text=text)
            return convert_mp3_ogg_opus(voice_bytes)
        except Exception as e:
            self._statistics.report_synthesize_error()
            logger.error(f"Failed to synthesize voice={voice}, text='{text}': {e}", exc_info=e)
            return None

    def _synthesize_request(self, voice: str, text: str) -> Optional[Tuple[str, str, str]]:
        try:
            voice_bytes = self._synthesizer.synthesize(voice_id=voice, text=text)
            with convert_mp3_ogg_opus(voice_bytes) as f:
                result = self._file_uploader.upload(f)
                if result is None:
                    return None
                (object_id, object_url) = result
                return object_id, object_url, voice
        except Exception as e:
            self._statistics.report_synthesize_error()
            logger.error(f"Failed to synthesize voice={voice}, text='{text}': {e}", exc_info=e)
            return None
