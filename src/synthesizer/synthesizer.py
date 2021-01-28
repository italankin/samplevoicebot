from enum import Enum
from typing import Optional


class Synthesizer:
    def synthesize(self, voice_id: str, text: str) -> bytes:
        """
        Synthesize text with a given voice_id
        :param voice_id: a voice from the 'voices()'
        :param text: text to synthesize speech for
        :return: bytes of synthesized speech
        """
        pass

    def voices(self, text: str, language: Optional['Language'] = None) -> list[str]:
        pass


class Language(Enum):
    EN = {'name': 'en', 'code': 'en-US'}
    RU = {'name': 'ru', 'code': 'ru-RU'}
    FR = {'name': 'fr', 'code': 'fr-FR'}
    DE = {'name': 'de', 'code': 'de-DE'}
    IT = {'name': 'it', 'code': 'it-IT'}
    NL = {'name': 'nl', 'code': 'nl-NL'}

    @staticmethod
    def from_name(name: str) -> Optional['Language']:
        for language in Language:
            if name == language.value['name']:
                return language
        return None
