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
            if msg and not msg.startswith('#'):
                q.put(msg)

        results = validator.validate_queue(q)

        # print("========")
        record_num = 0
        for res in results:
            record_num += 1
            for val in res.field_validations:
                if not val.valid:
                    print("Record #: %d, SerialId: %s, Field: %s, Details: %s, \n=====\n%s" % (record_num, res.serial_id, val.field, val.details, res.record))
                self.assertTrue(val.valid, val)
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
            if msg and not msg.startswith('#'):
                q.put(msg)

        results = validator.validate_queue(q)

        # print("========")
        for res in results:
            for val in res.field_validations:
                self.assertTrue(val.valid)
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
            if msg and not msg.startswith('#'):
                q.put(msg)

        results = validator.validate_queue(q)

        fail_count = 0
        expected_fail_count = 29
        record_num = 0
        # print("========")
        for res in results:
            record_num += 1
            for val in res.field_validations:
                if not val.valid:
                    print("Record #: %d, SerialId: %s, Field: %s, Details: %s, \n=====\n%s" % (record_num, res.serial_id, val.field, val.details, res.record))
                    fail_count += 1
        self.assertEquals(expected_fail_count, fail_count, "Expected %s faluires, got %s failures." % (expected_fail_count, fail_count))
        return True
