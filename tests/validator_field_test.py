import unittest
import queue
import json
from odevalidator import Field, ValidatorException

class FieldUnitTest(unittest.TestCase):
    def test_constructor_fails_no_key(self):
        input_field_object = {'Type': 'string'}
        try:
            Field("", input_field_object)
            self.fail("Expected ValidatorException")
        except ValidatorException as e:
            self.assertEqual("Invalid configuration property definition for field ={'Type': 'string'}", str(e))

    def test_constructor_fails_no_type(self):
        input_field_object = {}
        try:
            Field("a.b.c", input_field_object)
            self.fail("Expected ValidatorException")
        except ValidatorException as e:
            self.assertEqual("Missing required configuration property 'Type' for field a.b.c={}", str(e))

    def test_constructor_fails_no_field_config(self):
        self.assertEqual('{"Path": "a.b.c", "Type": null, "UpperLimit": null, "LowerLimit": null, "Values": null, "Choices": null, "EqualsValue": null, "EarliestTime": null, "LatestTime": null, "AllowEmpty": null}', str(Field("a.b.c")))

    def test_constructor_fails_invalid_earliesttime(self):
        input_field_object = {"Type":"timestamp", "EarliestTime":"invalidtimestamp"}
        try:
            Field("a.b.c", input_field_object)
            self.fail("Expected ValidatorException")
        except ValidatorException as e:
            self.assertEqual("Unable to parse configuration file timestamp EarliestTime for field a.b.c={'Type': 'timestamp', 'EarliestTime': 'invalidtimestamp'}, error: ('Unknown string format:', 'invalidtimestamp')", str(e))

    def test_constructor_succeeds_valid_earliesttime(self):
        input_field_object = {"Type":"timestamp", "EarliestTime":"2019-03-14T14:54:21.596Z"}
        actual_field = Field("a.b.c", input_field_object)
        self.assertEqual("2019-03-14 14:54:21+00:00", str(actual_field.earliest_time))

    def test_constructor_fails_invalid_latesttime(self):
        input_field_object = {"Type":"timestamp", "LatestTime":"invalidtimestamp"}
        try:
            Field("a.b.c", input_field_object)
            self.fail("Expected ValidatorException")
        except ValidatorException as e:
            self.assertEqual("Unable to parse configuration file timestamp LatestTime for field a.b.c={'Type': 'timestamp', 'LatestTime': 'invalidtimestamp'}, error: ('Unknown string format:', 'invalidtimestamp')", str(e))

    def test_constructor_succeeds_valid_latesttime(self):
        input_field_object = {"Type":"timestamp", "LatestTime":"2019-03-14T14:54:21.596Z"}
        actual_field = Field("a.b.c", input_field_object)
        self.assertEqual("2019-03-14 14:54:21+00:00", str(actual_field.latest_time))

    def test_constructor_succeeds_latesttime_now_keyword(self):
        input_field_object = {"Type":"timestamp", "LatestTime":"NOW"}
        actual_field = Field("a.b.c", input_field_object)
        self.assertTrue(actual_field.latest_time != None)

    def test_validate_returns_error_field_missing(self):
        test_field_object = {"Type":"decimal"}
        test_field = Field("a.b", test_field_object)
        test_data = {"a":{}}
        validation_result = test_field.validate(test_data)
        self.assertFalse(validation_result.valid)
        self.assertEqual("Field missing: a.b", validation_result.details)

    def test_validate_returns_error_field_empty(self):
        test_field_object = {"Type":"decimal"}
        test_field = Field("a.b", test_field_object)
        test_data = {"a":{"b":""}}
        validation_result = test_field.validate(test_data)
        self.assertFalse(validation_result.valid)
        self.assertEqual("Field empty", validation_result.details)

    def test_validate_returns_error_enum_value_not_in_set(self):
        test_field_object = {"Type":"enum", "Values":"[\"alpha\", \"beta\", \"gamma\"]"}
        test_field = Field("a.b", test_field_object)
        test_data = {"a":{"b":"delta"}}
        validation_result = test_field.validate(test_data)
        self.assertFalse(validation_result.valid)
        self.assertEqual("Value 'delta' not in list of known values: [alpha, beta, gamma]", validation_result.details)

    def test_validate_returns_succeeds_enum_value_in_set(self):
        test_field_object = {"Type":"enum", "Values":"[\"alpha\", \"beta\", \"gamma\"]"}
        test_field = Field("a.b", test_field_object)
        test_data = {"a":{"b":"alpha"}}
        validation_result = test_field.validate(test_data)
        self.assertTrue(validation_result.valid)

    def test_validate_returns_error_decimal_value_above_upper_limit(self):
        test_field_object = {"Type":"decimal", "UpperLimit":100}
        test_field = Field("a.b", test_field_object)
        test_data = {"a":{"b":101}}
        validation_result = test_field.validate(test_data)
        self.assertFalse(validation_result.valid)
        self.assertEqual("Value '101' is greater than upper limit '100'", validation_result.details)

    def test_validate_returns_succeeds_value_equals_upper_limit(self):
        test_field_object = {"Type":"decimal", "UpperLimit":100}
        test_field = Field("a.b", test_field_object)
        test_data = {"a":{"b":100}}
        validation_result = test_field.validate(test_data)
        self.assertTrue(validation_result.valid)

    def test_validate_returns_error_decimal_value_below_lower_limit(self):
        test_field_object = {"Type":"decimal", "LowerLimit":50}
        test_field = Field("a.b", test_field_object)
        test_data = {"a":{"b":49}}
        validation_result = test_field.validate(test_data)
        self.assertFalse(validation_result.valid)
        self.assertEqual("Value '49' is less than lower limit '50'", validation_result.details)

    def test_validate_returns_success_value_equals_lower_limit(self):
        test_field_object = {"Type":"decimal", "LowerLimit":50}
        test_field = Field("a.b", test_field_object)
        test_data = {"a":{"b":50}}
        validation_result = test_field.validate(test_data)
        self.assertTrue(validation_result.valid)

    def test_get_field_value_succeeds(self):
        test_field_object = {"Type":"decimal"}
        test_field = Field("a.b", test_field_object)
        test_data = {"a":{"b":50}}
        field_value = test_field._get_field_value("a.b", test_data)
        self.assertEqual(50, field_value)

    def test_get_field_value_returns_none_invalid_path(self):
        test_field_object = {"Type":"decimal"}
        test_field = Field("a.b.c", test_field_object)
        test_data = {"a":{"c":50}}
        self.assertIsNone(test_field._get_field_value("a.b", test_data))

    def test_validate_returns_error_timestamp_before_earliest_time(self):
        test_field_object = {"Type":"timestamp", "EarliestTime":"2019-03-14T14:54:21.000Z"}
        test_field = Field("a.b", test_field_object)
        test_data = {"a":{"b":"2019-03-14T14:54:20.000Z"}}
        validation_result = test_field.validate(test_data)
        self.assertFalse(validation_result.valid)
        self.assertEqual("Timestamp value '2019-03-14 14:54:20+00:00' occurs before earliest limit '2019-03-14 14:54:21+00:00'", validation_result.details)

    def test_validate_returns_error_timestamp_after_latest_time(self):
        test_field_object = {"Type":"timestamp", "LatestTime":"2019-03-14T14:54:20.000Z"}
        test_field = Field("a.b", test_field_object)
        test_data = {"a":{"b":"2019-03-14T14:56:20.000Z"}}
        validation_result = test_field.validate(test_data)
        self.assertFalse(validation_result.valid)
        self.assertEqual("Timestamp value '2019-03-14 14:56:20+00:00' occurs after latest limit '2019-03-14 14:54:20+00:00'", validation_result.details)

    def test_validate_returns_error_unparsable_timestamp(self):
        test_field_object = {"Type":"timestamp", "LatestTime":"2019-03-14T14:54:20.000Z"}
        test_field = Field("a.b", test_field_object)
        test_data = {"a":{"b":"invalidTimeStamp"}}
        validation_result = test_field.validate(test_data)
        self.assertFalse(validation_result.valid)
        self.assertEqual("Failed to perform timestamp validation, error: ('Unknown string format:', 'invalidTimeStamp')", validation_result.details)

    def test_validate_returns_success_timestamp_before_latest_time(self):
        test_field_object = {"Type":"timestamp", "LatestTime":"2019-03-14T14:54:21.000Z"}
        test_field = Field("a.b", test_field_object)
        test_data = {"a":{"b":"2019-03-14T14:54:20.000Z"}}
        validation_result = test_field.validate(test_data)
        self.assertTrue(validation_result.valid)

    def test_validate_returns_success_timestamp_after_earliest_time(self):
        test_field_object = {"Type":"timestamp", "EarliestTime":"2019-03-14T14:54:20.000Z"}
        test_field = Field("a.b", test_field_object)
        test_data = {"a":{"b":"2019-03-14T14:54:21.000Z"}}
        validation_result = test_field.validate(test_data)
        self.assertTrue(validation_result.valid)

    def testFieldSerialization(self):
        test_field_object = {"Type":"timestamp", "EarliestTime":"2019-03-14T14:54:20.000Z"}
        test_field = Field("a.b.c", test_field_object)
        self.assertEqual('{"Path": "a.b.c", "Type": "timestamp", "UpperLimit": null, "LowerLimit": null, "Values": null, "Choices": null, "EqualsValue": null, "EarliestTime": "2019-03-14T14:54:20+00:00", "LatestTime": null, "AllowEmpty": false}', json.dumps(test_field.to_json()))
        self.assertEqual('{"Path": "a.b.c", "Type": "timestamp", "UpperLimit": null, "LowerLimit": null, "Values": null, "Choices": null, "EqualsValue": null, "EarliestTime": "2019-03-14T14:54:20+00:00", "LatestTime": null, "AllowEmpty": false}', str(test_field))
