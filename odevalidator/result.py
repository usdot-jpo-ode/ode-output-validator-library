import json

class ValidatorException(Exception):
    pass

class ValidationResult:
    def __init__(self, valid = True, error = "", field = None):
        self.field = field
        self.valid = valid
        self.error = error

    def _print(self):
        print(json.dumps(self.to_json()))

    def to_json(self):
        return {"Field": self.field, "Valid": self.valid, "Error": self.error}
