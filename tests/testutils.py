import unittest

def assert_results(testcase, results, expected_fail_count):        
        fail_count = 0
        record_num = 0
        # print("========")
        for res in results:
            record_num += 1
            for val in res.field_validations:
                if not val.valid:
                    print("Record #: %d, SerialId: %s, Field: %s, Details: %s, \n=====\n%s" % (record_num, res.serial_id, val.field_path, val.details, res.record))
                    fail_count += 1

        testcase.assertEquals(expected_fail_count, fail_count, "Expected %s failures, got %s failures." % (expected_fail_count, fail_count))
