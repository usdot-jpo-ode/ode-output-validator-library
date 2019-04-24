from odevalidator import TestCase
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
