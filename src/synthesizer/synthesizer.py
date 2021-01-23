class Synthesizer:
    def synthesize(self, voice_id: str, text: str) -> object:
        """
        Synthesize text with a given voice_id
        :param voice_id: a voice from the 'voices()'
        :param text: text to synthesize speech for
        :return: stream of synthesized speech
        """
        pass

    def voices(self) -> list[str]:
        pass
