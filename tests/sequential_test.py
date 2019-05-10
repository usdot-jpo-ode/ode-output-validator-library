import copy
import json
import unittest
import dateutil.parser
from datetime import datetime, timezone, timedelta

from odevalidator import Sequential, Field
from odevalidator_testutils import assert_results

class SequentialUnitTest(unittest.TestCase):

    def runTest(self):
        seq = Sequential()

        seed_record = '{"metadata":{"logFileName":"rxMsg_1553540811_2620:31:40e0:843::1.csv","serialId":{"streamId":"8a4773d8-ae01-4b86-beae-7cd954a32e06","bundleSize":9,"bundleId":864,"recordId":2,"serialNumber":1000},"odeReceivedAt":"2019-03-25T19:21:06.407Z","recordGeneratedAt":"2019-03-14T14:54:21.596Z"}}'
        json_seed = json.loads(seed_record)

        # test happy path
        print("Testing Happy Path ...")
        record_list = self.build_happy_path(json_seed)
        results = seq.perform_sequential_validations(record_list)
        assert_results(self, results, 0)

        print("Testing Missing recordId, serialNumber and bundleSize ...")
        record_list_missing = []
        record_list_missing = copy.deepcopy(record_list)
        record_list_missing.remove(record_list_missing[19])
        record_list_missing.remove(record_list_missing[8])
        record_list_missing.remove(record_list_missing[2])
        results = seq.perform_sequential_validations(record_list_missing)
        assert_results(self, results, 14)

        print("Testing Duplicate recordId and serialNumber and non-chronological odeReceivedAt and recordGeneratedAt ...")
        record_list_dup = copy.deepcopy(record_list)
        record_list_dup[19] = copy.deepcopy(record_list_dup[17])
        record_list_dup[8] = copy.deepcopy(record_list_dup[6])
        record_list_dup[2] = copy.deepcopy(record_list_dup[0])
        results = seq.perform_sequential_validations(record_list_dup)
        assert_results(self, results, 18)


    def build_happy_path(self, json_seed):
        record_list = []

        #setting up for recordId 3-8 (tail end of a bundle of 9 records)
        json_seed['metadata']['logFileName'] = 'rxMsg_partial_1'
        cur_record = json_seed
        cur_record['metadata']['serialId']['recordId'] = 2
        n = 5
        while n >= 0:
            cur_record = self._next_record(cur_record)
            record_list.append(cur_record)
            n -= 1

        #setting up for recordId 0-9 (full bundle of 9 records)
        json_seed['metadata']['logFileName'] = 'rxMsg_Full'
        cur_record = json_seed
        cur_record['metadata']['serialId']['recordId'] = -1
        n = 8
        while n >= 0:
            cur_record = self._next_record(cur_record)
            record_list.append(cur_record)
            n -= 1

        #setting up for recordId 0-6 (front end of a bundle of 9 records)
        json_seed['metadata']['logFileName'] = 'rxMsg_partial_2'
        cur_record = json_seed
        cur_record['metadata']['serialId']['recordId'] = -1
        n = 5
        while n >= 0:
            cur_record = self._next_record(cur_record)
            record_list.append(cur_record)
            n -= 1

        #for record in record_list:
        #    print(json.dumps(record))

        return record_list

    def _next_record(self, cur_record):
        next_record = copy.deepcopy(cur_record)
        next_record['metadata']['serialId']['recordId'] += 1
        next_record['metadata']['serialId']['serialNumber'] += 1
        received_at = dateutil.parser.parse(next_record['metadata']['odeReceivedAt']) + timedelta(seconds=1)
        generated_at = dateutil.parser.parse(next_record['metadata']['recordGeneratedAt']) + timedelta(seconds=1)
        next_record['metadata']['odeReceivedAt'] = received_at.isoformat()
        next_record['metadata']['recordGeneratedAt'] = generated_at.isoformat()
        return next_record

