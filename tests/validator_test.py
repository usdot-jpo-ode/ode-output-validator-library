from odevalidator import TestCase, ValidatorException
import unittest
import queue

class ValidatorUnitTest(unittest.TestCase):
    def test_good_file_does_good_things(self):
        validator = TestCase()

        data_file = 'tests/testfiles/good.json'
        with open(data_file) as f:
            content = f.readlines()
        # remove whitespace characters like `\n` at the end of each line
        content = [x.strip() for x in content]
        #msgs = [json.loads(line) for line in content]
        q = queue.Queue()
        for msg in content:
            q.put(msg)
        results = validator.validate_queue(q)

        all_good = True
        # print("========")
        jsonprint = []
        for res in results['Results']:
            for val in res['Validations']:
                if not val['Valid']:
                    all_good = False
                    jsonprint.append({"RecordID":res['RecordID'], "Validation":val, "Record": res['Record']})
        self.assertTrue(all_good)
        return

    def test_good_bsmTx_file_passes_sequential_checks(self):
        validator = TestCase()

        data_file = 'tests/testfiles/good_bsmTx.json'
        with open(data_file) as f:
            content = f.readlines()
        # remove whitespace characters like `\n` at the end of each line
        content = [x.strip() for x in content]
        #msgs = [json.loads(line) for line in content]
        q = queue.Queue()
        for msg in content:
            q.put(msg)
        results = validator.validate_queue(q)

        all_good = True
        # print("========")
        jsonprint = []
        for res in results['Results']:
            for val in res['Validations']:
                if not val['Valid']:
                    all_good = False
                    jsonprint.append({"RecordID":res['RecordID'], "Validation":val, "Record": res['Record']})
        self.assertTrue(all_good)
        return

    def test_bad_file_does_bad_things(self):
        validator = TestCase()

        data_file = 'tests/testfiles/bad.json'
        with open(data_file) as f:
            content = f.readlines()
        # remove whitespace characters like `\n` at the end of each line
        content = [x.strip() for x in content]
        #msgs = [json.loads(line) for line in content]
        q = queue.Queue()
        for msg in content:
            q.put(msg)
        results = validator.validate_queue(q)

        all_good = True
        # print("========")
        jsonprint = []
        for res in results['Results']:
            for val in res['Validations']:
                if not val['Valid']:
                    # print("Field: %s, Details: %s" % (val['Field'], val['Details']))
                    all_good = False
                    jsonprint.append({"RecordID":res['RecordID'], "Validation":val, "Record": res['Record']})
        self.assertFalse(all_good)
        return False

    def test_constructor_raises_exception_config_file_missing(self):
        try:
            TestCase(filepath="thisdoesnotexist.ini")
            self.fail("Expected ValidatorException")
        except ValidatorException as e:
            self.assertEqual("Custom configuration file 'thisdoesnotexist.ini' could not be found", str(e))

    def test_constructor_does_not_raise_exception_config_file_present(self):
        try:
            validator = TestCase(filepath="odevalidator/config.ini")
            self.assertTrue(len(validator.config.sections()) > 0)
        except ValidatorException as e:
            self.fail("Unexpected exception: %s", str(e))
