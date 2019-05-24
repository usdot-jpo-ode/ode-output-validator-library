import copy
import json
import unittest
import dateutil.parser
from datetime import datetime, timezone, timedelta

from odevalidator import Sequential, Field
from tests import assert_results

class SequentialUnitTest(unittest.TestCase):

    def setUp(self):
        self.seq = Sequential()

        seed_record = '{"metadata":{"logFileName":"rxMsg_1553540811_2620:31:40e0:843::1.csv","serialId":{"streamId":"8a4773d8-ae01-4b86-beae-7cd954a32e06","bundleSize":9,"bundleId":864,"recordId":2,"serialNumber":1000},"odeReceivedAt":"2019-03-25T19:21:06.407Z","recordGeneratedAt":"2019-03-14T14:54:21.596Z"}}'
        self.json_seed = json.loads(seed_record)
        self.record_list = self.build_happy_path(self.json_seed)

    def test_happy_path(self):
        # print("Testing Happy Path ...")
        record_list = self.build_happy_path(self.json_seed)
        results = self.seq.perform_sequential_validations(record_list)
        assert_results(self, results, 0)

    def test_missing_records(self):
        # print("Testing Missing recordId, serialNumber ...")
        self.record_list.remove(self.record_list[19])
        self.record_list.remove(self.record_list[8])
        self.record_list.remove(self.record_list[2])
        results = self.seq.perform_sequential_validations(self.record_list)
        assert_results(self, results, 7)

    def test_invalid_bundle_size(self):
        # print("Testing invalid bundleSize ...")
        self.record_list.remove(self.record_list[15])
        self.record_list.remove(self.record_list[6])
        results = self.seq.perform_sequential_validations(self.record_list)
        # Even though we have removed the last record of a full bundle, the validator can't detect if this is a head of a full list or a full list.
        # Therefore, we should get only one validation error
        assert_results(self, results, 1)

    def test_dup_and_chronological(self):
        # print("Testing Duplicate recordId and serialNumber and non-chronological odeReceivedAt and recordGeneratedAt ...")
        self.record_list[18] = copy.deepcopy(self.record_list[16])
        self.record_list[9] = copy.deepcopy(self.record_list[7])
        self.record_list[2] = copy.deepcopy(self.record_list[0])
        results = self.seq.perform_sequential_validations(self.record_list)
        assert_results(self, results, 18)


    def build_happy_path(self, json_seed):
        record_list = []

        #setting up for recordId 3-8 (tail end of a bundle of 9 records)
        self.json_seed['metadata']['logFileName'] = 'rxMsg_tail'
        self.json_seed['metadata']['serialId']['bundleId'] = 101
        self.json_seed['metadata']['serialId']['serialNumber'] = 1001

        self.json_seed['metadata']['serialId']['recordId'] = 2
        cur_record = self.json_seed
        bundle = self._build_bundle(cur_record, 7)
        record_list.extend(bundle)

        #setting up for recordId 0-9 (full bundle of 9 records)
        cur_record = self._next_record(record_list[-1])
        cur_record['metadata']['logFileName'] = 'rxMsg_Full'
        cur_record['metadata']['serialId']['bundleId'] = 102
        cur_record['metadata']['serialId']['recordId'] = 0
        bundle = self._build_bundle(cur_record, 9)
        record_list.extend(bundle)

        #setting up for recordId 0-6 (front end of a bundle of 9 records)
        cur_record = self._next_record(record_list[-1])
        cur_record['metadata']['logFileName'] = 'rxMsg_head'
        cur_record['metadata']['serialId']['bundleId'] = 103
        cur_record['metadata']['serialId']['recordId'] = 0
        bundle = self._build_bundle(cur_record, 7)
        record_list.extend(bundle)

        #for record in record_list:
        #    print(json.dumps(record))

        return record_list

    def _build_bundle(self, seed_record, count):
        bundle = []
        cur_record = copy.deepcopy(seed_record)
        while count > 0:
            bundle.append(cur_record)
            cur_record = self._next_record(cur_record)
            count -= 1

        return bundle

    def _next_record(self, cur_record):
        next_record = copy.deepcopy(cur_record)
        next_record['metadata']['serialId']['recordId'] += 1
        next_record['metadata']['serialId']['serialNumber'] += 1
        received_at = dateutil.parser.parse(next_record['metadata']['odeReceivedAt']) + timedelta(seconds=1)
        generated_at = dateutil.parser.parse(next_record['metadata']['recordGeneratedAt']) + timedelta(seconds=1)
        next_record['metadata']['odeReceivedAt'] = received_at.isoformat()
        next_record['metadata']['recordGeneratedAt'] = generated_at.isoformat()
        return next_record
