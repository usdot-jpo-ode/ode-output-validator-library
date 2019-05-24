import json
import unittest
from odevalidator import FieldValidationResult, RecordValidationResult

class ResultTest(unittest.TestCase):

    def testFieldValidationResult(self):
        f = FieldValidationResult()
        self.assertTrue(f.valid)
        self.assertEqual("", f.details)
        self.assertEqual(None, f.field_path)
        self.assertEqual('{"Field": null, "Valid": true, "Details": "", "SerialId": null}', json.dumps(f.to_json()))
        self.assertEqual('{"Field": null, "Valid": true, "Details": "", "SerialId": null}', str(f))

    def testRecordValidationResult(self):
        f = RecordValidationResult("serial_id", [FieldValidationResult()], "record")
        self.assertEqual("serial_id", f.serial_id)
        self.assertEqual("record", f.record)
        self.assertEqual('{"SerialId": "serial_id", "Validations": [{"Field": null, "Valid": true, "Details": "", "SerialId": null}], "Record": "record"}', json.dumps(f.to_json()))
        self.assertEqual('{"SerialId": "serial_id", "Validations": [{"Field": null, "Valid": true, "Details": "", "SerialId": null}], "Record": "record"}', str(f))
