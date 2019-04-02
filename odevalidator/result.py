import json

class ValidatorException(Exception):
    pass

class ValidationResult:
    def __init__(self, valid, error="", record=""):
        self.valid = valid
        self.error = error
        self.record = record

    def _print(self):
        print(json.dumps(self.toJson()))

    def toJson(self):
        return {"Valid": self.valid, "Error": self.error, "Record": self.record}
