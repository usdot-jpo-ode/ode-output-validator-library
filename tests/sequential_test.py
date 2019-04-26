import copy
import json
import unittest
from odevalidator import Sequential

class SequentialUnitTest(unittest.TestCase):
    def test(self):
        seq = Sequential()

        seed_record = '{"metadata":{"logFileName":"rxMsg_1553540811_2620:31:40e0:843::1.csv","serialId":{"streamId":"8a4773d8-ae01-4b86-beae-7cd954a32e06","bundleSize":10,"bundleId":864,"recordId":2,"serialNumber":1000},"odeReceivedAt":"2019-03-25T19:21:06.407Z","recordGeneratedAt":"2019-03-14T14:54:21.596Z"}}'
        json_seed = json.loads(seed_record)

        # test happy path
        print("Testing Happy Path ...")
        record_list = self.build_happy_path(json_seed)
        result = seq.perform_sequential_validations(record_list)
        for x in result: x._print()

        # test missing/duplicate recordId
        print("Testing Missing/Duplicate recordIds ...")
        record_list_missing = copy.deepcopy(record_list)
        prev_record = record_list_missing[0]
        for record in record_list_missing[1:]:
            record['metadata']['serialId']['recordId'] = prev_record['metadata']['serialId']['recordId']
        result = seq.perform_sequential_validations(record_list_missing)
        for x in result: x._print()

        # test invalid bundleSize
        print("Testing Invalid bundleSize ...")
        record_list_invalid_bundleSize = copy.deepcopy(record_list)
        for record in record_list_invalid_bundleSize:
            record['metadata']['serialId']['bundleSize'] = 9999
        result = seq.perform_sequential_validations(record_list_invalid_bundleSize)
        for x in result: x._print()


    def build_happy_path(self, json_seed):
        record_list = []
        json_seed['metadata']['logFileName'] = 'rxMsg_partial_1'
        for i in range(3, 10):
            json_record = copy.deepcopy(json_seed)
            json_record['metadata']['serialId']['recordId'] = i
            json_record['metadata']['serialId']['serialNumber'] = json_seed['metadata']['serialId']['serialNumber'] + i
            record_list.append(json_record)

        json_seed['metadata']['logFileName'] = 'rxMsg_Full'
        for i in range(0, 10):
            json_record = copy.deepcopy(json_seed)
            json_record['metadata']['serialId']['recordId'] = i
            json_record['metadata']['serialId']['serialNumber'] = json_seed['metadata']['serialId']['serialNumber'] + i
            record_list.append(json_record)

        json_seed['metadata']['logFileName'] = 'rxMsg_partial_2'
        for i in range(0, 7):
            json_record = copy.deepcopy(json_seed)
            json_record['metadata']['serialId']['recordId'] = i
            json_record['metadata']['serialId']['serialNumber'] = json_seed['metadata']['serialId']['serialNumber'] + i
            record_list.append(json_record)

        #for record in record_list:
        #    print(json.dumps(record))

        return record_list
