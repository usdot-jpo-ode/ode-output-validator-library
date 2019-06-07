from odevalidator import TestCase, ValidatorException
import unittest
import queue

class ValidatorUnitTest(unittest.TestCase):
    def test_constructor_raises_exception_config_file_missing(self):
        try:
            TestCase(filepath="thisdoesnotexist.ini")
            self.fail("Expected ValidatorException")
        except ValidatorException as e:
            self.assertEqual("Custom configuration file 'thisdoesnotexist.ini' could not be found", str(e))

    def test_constructor_does_not_raise_exception_config_file_present(self):
        try:
            validator = TestCase(filepath="odevalidator/configs/config.ini")
            self.assertTrue(len(validator.config.sections()) > 0)
        except ValidatorException as e:
            self.fail("Unexpected exception: %s" % str(e))
