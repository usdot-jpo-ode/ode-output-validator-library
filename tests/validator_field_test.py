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


    # def test_get_field_value_returns_field_value_integer(self):
    #     path_string = "alpha.beta.gamma"
    #     data_object = {
    #         "alpha":{
    #             "beta":{
    #                 "gamma":5
    #             }
    #         }
    #     }
    #
    #     expected_value = 5
    #     actual_value = odevalidator._
    #     pass
