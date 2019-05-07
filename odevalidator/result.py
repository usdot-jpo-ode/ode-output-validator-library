import json

class ValidatorException(Exception):
    pass

class FieldValidationResult:
    def __init__(self, valid = True, details = "", field = None):
        self.field = field
        self.valid = valid
        self.details = details

    def _print(self):
        print(json.dumps(self.to_json()))

    def to_json(self):
        return {"Field": self.field, "Valid": self.valid, "Details": self.details}

class RecordValidationResult:
    def __init__(self, serial_id, field_validations, record):
        self.serial_id = serial_id
        self.field_validations = field_validations
        self.record = record

    def _print(self):
        print(json.dumps(self.to_json()))

    def to_json(self):
        return {"SerialId": self.serial_id, "Validations": self.field_validations, "Record": self.record}
