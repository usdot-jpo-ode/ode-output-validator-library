from odevalidator import TestCase, ValidatorException
import unittest
import queue
from tests import assert_results

class ValidatorIntegrationTest(unittest.TestCase):
    
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
        assert_results(self, results, 0)
        
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
        assert_results(self, results, 0)

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
        assert_results(self, results, 29)

        return
