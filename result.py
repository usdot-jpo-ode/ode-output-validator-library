import json

class ValidatorException(Exception):
    pass

class ValidationResult:
    def __init__(self, valid, error, record=""):
        self.valid = valid
        self.error = error
        self.record = record

    def print(self):
        json_val = {"valid": self.valid, "error": self.error, "record": self.record}
        print(json.dumps(json_val))

