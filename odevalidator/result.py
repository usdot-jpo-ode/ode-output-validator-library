import json

class ValidatorException(Exception):
    pass

class FieldValidationResult:
    def __init__(self, valid = True, details = "", field_path = None, serial_id = None):
        self.field_path = field_path
        self.valid = valid
        self.details = details
        self.serial_id = serial_id

    def __str__(self):
        return json.dumps(self.to_json())

    def to_json(self):
        return {"Field": self.field_path, "Valid": self.valid, "Details": self.details, "SerialId": self.serial_id}

class RecordValidationResult:
    def __init__(self, serial_id, field_validations, record):
        self.serial_id = serial_id
        self.field_validations = field_validations
        self.record = record

    def __str__(self):
        return json.dumps(self.to_json())

    def to_json(self):
        json_field_validations = []
        for field_val in self.field_validations:
            json_field_validations.append(field_val.to_json())
        return {"SerialId": self.serial_id, "Validations": json_field_validations, "Record": self.record}
