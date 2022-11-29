from shared_functions import sources

class InvalidSourceException(Exception):
    def __init__(self, source):
        super().__init__()
        self.source = source
    def __str__(self):
        return f"{self.source} is not a valid source. Must be one of {list(sources.keys())}"