import json

class ValidatorException(Exception):
    pass

class ValidationResult:
    def __init__(self, valid, error="", record=""):
        self.valid = valid
        self.error = error
        self.record = record

    def print(self):
        json_val = {"Valid": self.valid, "Error": self.error, "Record": self.record}
        print(json.dumps(json_val))

