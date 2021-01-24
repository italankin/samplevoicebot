class Validator:
    def __init__(self, min_length, max_length):
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, text: str) -> bool:
        return self.min_length <= len(text) <= self.max_length
