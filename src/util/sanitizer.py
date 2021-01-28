import re

pattern = re.compile('\\s{2,}')


class Sanitizer:
    def __init__(self, max_length):
        self.max_length = max_length

    def sanitize(self, text: str) -> str:
        text = text.strip()
        text = pattern.sub(' ', text)
        return text[:self.max_length]
