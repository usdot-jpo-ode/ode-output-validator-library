import json

class ValidatorException(Exception):
    pass

class ValidationResult:
    def __init__(self, valid, error=""):
        self.valid = valid
        self.error = error

    def _print(self):
        print(json.dumps(self.to_json()))

    def to_json(self):
        return {"Valid": self.valid, "Error": self.error}
