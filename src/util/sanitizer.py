import re


class Sanitizer:
    def __init__(self, max_length):
        self.max_length = max_length

    def sanitize(self, text: str) -> str:
        text = text.strip()
        p = re.compile('(\\s){2,}')
        text = p.sub('\1', text)
        return text[:self.max_length]
