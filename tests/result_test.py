import json
import unittest
from odevalidator import FieldValidationResult, RecordValidationResult

class ResultTest(unittest.TestCase):

    def testFieldValidationResult(self):
        f = FieldValidationResult()
        self.assertTrue(f.valid)
        self.assertEquals("", f.details)
        self.assertEquals(None, f.field_path)
        self.assertEquals('{"Field": null, "Valid": true, "Details": ""}', json.dumps(f.to_json()))
        self.assertEquals('{"Field": null, "Valid": true, "Details": ""}', str(f))

    def testRecordValidationResult(self):
        f = RecordValidationResult("serial_id", [FieldValidationResult()], "record")
        self.assertEquals("serial_id", f.serial_id)
        self.assertEquals("record", f.record)
        self.assertEquals('{"SerialId": "serial_id", "Validations": [{"Field": null, "Valid": true, "Details": ""}], "Record": "record"}', json.dumps(f.to_json()))
        self.assertEquals('{"SerialId": "serial_id", "Validations": [{"Field": null, "Valid": true, "Details": ""}], "Record": "record"}', str(f))
