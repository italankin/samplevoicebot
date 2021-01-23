import re


def sanitize(text: str) -> str:
    text = text.strip()
    p = re.compile('(\\s){2,}')
    return p.sub('\1', text)
