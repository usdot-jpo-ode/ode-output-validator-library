from odevalidator import Field, ValidatorException
import unittest
import queue

class FieldUnitTest(unittest.TestCase):
    def test_constructor_fails_no_path(self):
        input_field_object = {}
        try:
            Field(input_field_object)
            self.fail("Expected ValidatorException")
        except ValidatorException as e:
            self.assertEqual("Missing required configuration property 'Path' for field '{}'", str(e))

    def test_constructor_fails_no_type(self):
        input_field_object = {"Path":"a.b.c"}
        try:
            Field(input_field_object)
            self.fail("Expected ValidatorException")
        except ValidatorException as e:
            self.assertEqual("Missing required configuration property 'Type' for field '{'Path': 'a.b.c'}'", str(e))

    def test_constructor_fails_invalid_earliesttime(self):
        input_field_object = {"Path":"a.b.c", "Type":"timestamp", "EarliestTime":"invalidtimestamp"}
        try:
            Field(input_field_object)
            self.fail("Expected ValidatorException")
        except ValidatorException as e:
            self.assertEqual("Unable to parse configuration file timestamp EarliestTime for field {'Path': 'a.b.c', 'Type': 'timestamp', 'EarliestTime': 'invalidtimestamp'}, error: ('Unknown string format:', 'invalidtimestamp')", str(e))

    def test_constructor_succeeds_valid_earliesttime(self):
        input_field_object = {"Path":"a.b.c", "Type":"timestamp", "EarliestTime":"2019-03-14T14:54:21.596Z"}
        actual_field = Field(input_field_object)
        self.assertEqual("2019-03-14 14:54:21.596000+00:00", str(actual_field.earliest_time))

    def test_constructor_fails_invalid_latesttime(self):
        input_field_object = {"Path":"a.b.c", "Type":"timestamp", "LatestTime":"invalidtimestamp"}
        try:
            Field(input_field_object)
            self.fail("Expected ValidatorException")
        except ValidatorException as e:
            self.assertEqual("Unable to parse configuration file timestamp LatestTime for field {'Path': 'a.b.c', 'Type': 'timestamp', 'LatestTime': 'invalidtimestamp'}, error: ('Unknown string format:', 'invalidtimestamp')", str(e))

    def test_constructor_succeeds_valid_latesttime(self):
        input_field_object = {"Path":"a.b.c", "Type":"timestamp", "LatestTime":"2019-03-14T14:54:21.596Z"}
        actual_field = Field(input_field_object)
        self.assertEqual("2019-03-14 14:54:21.596000+00:00", str(actual_field.latest_time))

    def test_constructor_succeeds_latesttime_now_keyword(self):
        input_field_object = {"Path":"a.b.c", "Type":"timestamp", "LatestTime":"NOW"}
        actual_field = Field(input_field_object)
        self.assertTrue(actual_field.latest_time != None)

    def test_validate_returns_error_field_missing(self):
        test_field_object = {"Path":"a.b", "Type":"decimal"}
        test_field = Field(test_field_object)
        test_data = {"a":{}}
        validation_result = test_field.validate(test_data)
        self.assertFalse(validation_result.valid)
        self.assertEqual("Field missing", validation_result.error)

    def test_validate_returns_error_field_empty(self):
        test_field_object = {"Path":"a.b", "Type":"decimal"}
        test_field = Field(test_field_object)
        test_data = {"a":{"b":""}}
        validation_result = test_field.validate(test_data)
        self.assertFalse(validation_result.valid)
        self.assertEqual("Field empty", validation_result.error)

    def test_validate_returns_error_enum_value_not_in_set(self):
        test_field_object = {"Path":"a.b", "Type":"enum", "Values":"[\"alpha\", \"beta\", \"gamma\"]"}
        test_field = Field(test_field_object)
        test_data = {"a":{"b":"delta"}}
        validation_result = test_field.validate(test_data)
        self.assertFalse(validation_result.valid)
        self.assertEqual("Value 'delta' not in list of known values: [alpha, beta, gamma]", validation_result.error)

    def test_validate_returns_succeeds_enum_value_in_set(self):
        test_field_object = {"Path":"a.b", "Type":"enum", "Values":"[\"alpha\", \"beta\", \"gamma\"]"}
        test_field = Field(test_field_object)
        test_data = {"a":{"b":"alpha"}}
        validation_result = test_field.validate(test_data)
        self.assertTrue(validation_result.valid)

    def test_validate_returns_error_decimal_value_above_upper_limit(self):
        test_field_object = {"Path":"a.b", "Type":"decimal", "UpperLimit":100}
        test_field = Field(test_field_object)
        test_data = {"a":{"b":101}}
        validation_result = test_field.validate(test_data)
        self.assertFalse(validation_result.valid)
        self.assertEqual("Value '101' is greater than upper limit '100'", validation_result.error)

    def test_validate_returns_succeeds_value_equals_upper_limit(self):
        test_field_object = {"Path":"a.b", "Type":"decimal", "UpperLimit":100}
        test_field = Field(test_field_object)
        test_data = {"a":{"b":100}}
        validation_result = test_field.validate(test_data)
        self.assertTrue(validation_result.valid)

    def test_validate_returns_error_decimal_value_below_lower_limit(self):
        test_field_object = {"Path":"a.b", "Type":"decimal", "LowerLimit":50}
        test_field = Field(test_field_object)
        test_data = {"a":{"b":49}}
        validation_result = test_field.validate(test_data)
        self.assertFalse(validation_result.valid)
        self.assertEqual("Value '49' is less than lower limit '50'", validation_result.error)

    def test_validate_returns_succeeds_value_equals_lower_limit(self):
        test_field_object = {"Path":"a.b", "Type":"decimal", "LowerLimit":50}
        test_field = Field(test_field_object)
        test_data = {"a":{"b":50}}
        validation_result = test_field.validate(test_data)
        self.assertTrue(validation_result.valid)

    def test_get_field_value_succeeds(self):
        test_field_object = {"Path":"a.b", "Type":"decimal"}
        test_field = Field(test_field_object)
        test_data = {"a":{"b":50}}
        field_value = test_field._get_field_value("a.b", test_data)
        self.assertEqual(50, field_value)

    def test_get_field_value_returns_none_invalid_path(self):
        test_field_object = {"Path":"a.b.c", "Type":"decimal"}
        test_field = Field(test_field_object)
        test_data = {"a":{"c":50}}
        self.assertIsNone(test_field._get_field_value("a.b", test_data))
