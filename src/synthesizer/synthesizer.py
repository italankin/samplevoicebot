class Synthesizer:
    def synthesize(self, voice_id: str, text: str) -> bytes:
        """
        Synthesize text with a given voice_id
        :param voice_id: a voice from the 'voices()'
        :param text: text to synthesize speech for
        :return: bytes of synthesized speech
        """
        pass

    def voices(self, text: str) -> list[str]:
        pass
