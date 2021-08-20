import re

pattern = re.compile('\\s{2,}')

MAX_INLINE_LENGTH = 256


class Sanitizer:
    def __init__(self, max_length):
        self.max_length = max_length

    def sanitize(self, text: str, inline=False) -> str:
        text = text.strip()
        text = pattern.sub(' ', text)
        max_len = MAX_INLINE_LENGTH if inline else self.max_length
        return text[:max_len]
