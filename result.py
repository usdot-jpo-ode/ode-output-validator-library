import json

class ValidatorException(Exception):
    pass

class ValidationResult:
    def __init__(self, valid, error, record):
        self.json = {"valid": valid, "error": error, "record": record}

    def print(self):
        print(json.dumps(self.json))

