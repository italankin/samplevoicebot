from enum import Enum
from typing import Optional, Tuple


class Synthesizer:
    def synthesize(self, voice_id: str, text: str) -> bytes:
        """
        Synthesize text with a given voice_id
        :param voice_id: a voice from the 'voices()'
        :param text: text to synthesize speech for
        :return: bytes of synthesized speech
        """
        pass

    def voices(self, text: str, language: Optional['Language'] = None) -> Tuple['Language', 'Voices']:
        """
        Get a list of supported voices for a given 'text'.
        Optional parameter 'language' forces synthesizer to use it
        for voice generation.
        :param text:
        :param language:
        :return:
        """
        pass

    def prefetch_voices(self, language: 'Language'):
        """
        Prefetch voices list for a given language
        """
        pass


class Language(Enum):
    EN = {'name': 'en', 'code': 'en-US', 'flag': '🇺🇸'}
    RU = {'name': 'ru', 'code': 'ru-RU', 'flag': '🇷🇺'}
    FR = {'name': 'fr', 'code': 'fr-FR', 'flag': '🇫🇷'}
    DE = {'name': 'de', 'code': 'de-DE', 'flag': '🇩🇪'}
    IT = {'name': 'it', 'code': 'it-IT', 'flag': '🇮🇹'}
    NL = {'name': 'nl', 'code': 'nl-NL', 'flag': '🇳🇱'}

    @staticmethod
    def from_name(name: str) -> Optional['Language']:
        for language in Language:
            if name == language.value['name']:
                return language
        return None


class Voices:
    all_voices: list[str]
    inline_voices: list[str]

    def __init__(self, all_voices: list[str], inline_voices: list[str]):
        self.all_voices = all_voices
        self.inline_voices = inline_voices
