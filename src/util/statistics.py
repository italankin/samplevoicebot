class Statistics:
    """
    Simple in-memory bot usage statistics
    """
    errors: int
    requests: int
    synthesized_chars: int

    def __init__(self):
        self.reset()

    def report_synthesize_error(self):
        self.errors += 1

    def report_synthesized(self, text: str):
        self.synthesized_chars += len(text)

    def report_request(self):
        self.requests += 1

    def reset(self):
        self.errors = 0
        self.requests = 0
        self.synthesized_chars = 0
