import json

class ValidatorException(Exception):
    pass

class ValidationResult:
    def __init__(self, valid, error=""):
        self.valid = valid
        self.error = error

    def _print(self):
        print(json.dumps(self.toJson()))

    def toJson(self):
        return {"Valid": self.valid, "Error": self.error}
