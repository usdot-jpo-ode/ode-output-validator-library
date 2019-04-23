# def test(self, data_file):
#         validator = TestCase()
#         results = self.test_file(validator, data_file)
#         self.print_results(results)
#
# def print_results(self, results):
#     all_good = True
#     print("========")
#     jsonprint = []
#     for res in results['Results']:
#         for val in res['Validations']:
#             if not val['Valid']:
#                 all_good = False
#                 jsonprint.append({"RecordID":res['RecordID'], "Validation":val, "Record": res['Record']})
#     if all_good:
#         print("Results: SUCCESS")
#     else:
#         print(jsonprint)
#         print("TOTAL FAILURES: %d" % len(jsonprint))
#     print("========")
#
# # main function using old functionality
# def test_file(self, validator, data_file):
#     print("Testing '%s'." % data_file)
#     with open(data_file) as f:
#         content = f.readlines()
#     # remove whitespace characters like `\n` at the end of each line
#     content = [x.strip() for x in content]
#     #msgs = [json.loads(line) for line in content]
#     q = queue.Queue()
#     for msg in content:
#         q.put(msg)
#     results = validator.validate_queue(q)
#
#     return results

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
                    all_good = False
                    jsonprint.append({"RecordID":res['RecordID'], "Validation":val, "Record": res['Record']})
        self.assertFalse(all_good)
        return False
