from enum import Enum


class ValidatorResult(Enum):
    OK = 0
    TOO_LONG = 1
    TOO_SHORT = 2


class Validator:
    def __init__(self, min_length, max_length):
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, text: str) -> ValidatorResult:
        if len(text) < self.min_length:
            return ValidatorResult.TOO_SHORT
        if len(text) > self.max_length:
            return ValidatorResult.TOO_LONG
        return ValidatorResult.OK
