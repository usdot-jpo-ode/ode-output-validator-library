import json
import dateutil.parser
import copy
from __init__ import ValidationResult

class Sequential:
    def __init__(self):
        return

    ### Iterate messages and check that sequential items are sequential
    def perform_sequential_validations(self, sorted_record_list):
        firstRecord = sorted_record_list[0]
        old_log_file_name = firstRecord['metadata']['logFileName']
        old_record_id = int(firstRecord['metadata']['serialId']['recordId'])
        old_serial_number = int(firstRecord['metadata']['serialId']['serialNumber'])
        old_record_generated_at = dateutil.parser.parse(firstRecord['metadata']['recordGeneratedAt'])
        old_ode_received_at = dateutil.parser.parse(firstRecord['metadata']['odeReceivedAt'])

        one_list = []
        one_list.append(firstRecord)
        record_id = 0
        record_num = 1
        validation_result = []
        for record in sorted_record_list[1:]:
            record_num += 1
            new_log_file_name = record['metadata']['logFileName']
            new_record_id = int(record['metadata']['serialId']['recordId'])
            new_serial_number = int(record['metadata']['serialId']['serialNumber'])
            new_record_generated_at = dateutil.parser.parse(record['metadata']['recordGeneratedAt'])
            new_ode_received_at = dateutil.parser.parse(record['metadata']['odeReceivedAt'])
            
            if old_log_file_name == new_log_file_name:
                one_list.append(record)
                if new_record_id != old_record_id+1:
                    record_id = new_record_id
                    validation_result.append(ValidationResult(False, "Detected incorrectly incremented recordId. Record Number: '%d' Expected '%d' but got '%d'" % (record_num, old_record_id+1, new_record_id), record))
                if new_serial_number != old_serial_number+1:
                    record_id = new_record_id
                    validation_result.append(ValidationResult(False, "Detected incorrectly incremented serialNumber. Record Number: '%d' Expected '%d' but got '%d'" % (record_num, old_serial_number+1, new_serial_number), record))
                if new_record_generated_at < old_record_generated_at:
                    record_id = new_record_id
                    validation_result.append(ValidationResult(False, "Detected non-chronological recordGeneratedAt. Record Number: '%d' Previous timestamp was '%s' but current timestamp is '%s'" % (record_num, old_record_generated_at, new_record_generated_at), record))
                if new_ode_received_at < old_ode_received_at:
                    record_id = new_record_id
                    validation_result.append(ValidationResult(False, "Detected non-chronological odeReceivedAt. Record Number: '%d' Previous timestamp was '%s' but current timestamp is '%s'" % (record_num, old_ode_received_at, new_ode_received_at), record))
            else:
                #validation_result.append(ValidationResult(True, "New log file detected. Resetting old item values. Record Number: '%d' Old filename: '%s', new filename: '%s'" % (record_num, old_log_file_name, new_log_file_name)))
                bundle_size_validation_result = self.validate_bundle_size(one_list)
                if bundle_size_validation_result.__len__() > 0:
                    validation_result.extend(bundle_size_validation_result)
                    record_id = new_record_id
                    break
                one_list.clear()
                one_list.append(record)

            old_log_file_name = new_log_file_name
            old_record_id = new_record_id
            old_serial_number = new_serial_number
            old_record_generated_at = new_record_generated_at
            old_ode_received_at = new_ode_received_at

            if record_id == 0:
                break
            
        return validation_result

    def validate_bundle_size(self, sorted_record_list):
        record_id = 0
        first_record_id = int(sorted_record_list[0]['metadata']['serialId']['recordId'])
        last_record_id = int(sorted_record_list[-1]['metadata']['serialId']['recordId'])

        validation_result = []
        # partial or full list?
        if first_record_id == 1:
            # head of a partial list?
            if last_record_id == first_record_id:
                # full list
                record_num = 0
                for record in sorted_record_list:
                    record_num += 1
                    bundle_size = int(record['metadata']['serialId']['bundleSize'])
                    if sorted_record_list.len() != bundle_size:
                        validation_result.append(ValidationResult(False, "buldleSize doesn't match number of records. Record Number: '%d' record length: '%d' != bundlSize: '%d'" % (record_num, sorted_record_list.len(), bundle_size)))
                        record_id = int(record['metadata']['serialId']['recordId'])
                        break

                bundle_size = int(sorted_record_list[0]['metadata']['serialId']['bundleSize'])
                if last_record_id != bundle_size:
                    validation_result.append(ValidationResult(False, "buldleSize doesn't match the last recordId. Record Number: '%d' Last recordId: '%d' != bundlSize: '%d'" % (record_num, last_record_id, bundle_size)))
                    record_id = last_record_id
        else:
            # tail of a partial list
            record_num = 0
            for record in sorted_record_list:
                record_num += 1
                bundle_size = int(record['metadata']['serialId']['bundleSize'])
                if last_record_id != bundle_size:
                    validation_result.append(ValidationResult(False, "buldleSize doesn't match last recordId. Record Number: '%d' last recordId: '%d' != bundleSize: '%d'" % (record_num, last_record_id, bundle_size), record))
                    record_id = last_record_id
                    break

        return validation_result

def main():
    seq = Sequential()

    seed_record = '{"metadata":{"logFileName":"rxMsg_1553540811_2620:31:40e0:843::1.csv","serialId":{"streamId":"8a4773d8-ae01-4b86-beae-7cd954a32e06","bundleSize":9,"bundleId":864,"recordId":2,"serialNumber":1000},"odeReceivedAt":"2019-03-25T19:21:06.407Z","recordGeneratedAt":"2019-03-14T14:54:21.596Z"}}'
    json_seed = json.loads(seed_record)

    # test happy path
    record_list = build_happy_path(json_seed)
    result = seq.perform_sequential_validations(record_list)
    for x in result: x.print()

    # test missing/duplicate recordId
    record_list_missing = copy.deepcopy(record_list)
    prev_record = record_list_missing[0]
    for record in record_list_missing[1:]:
        record['metadata']['serialId']['recordId'] = prev_record['metadata']['serialId']['recordId']
    result = seq.perform_sequential_validations(record_list_missing)
    for x in result: x.print()

    # test invalid bundleSize
    record_list_invalid_bundleSize = copy.deepcopy(record_list)
    for record in record_list_invalid_bundleSize:
        record['metadata']['serialId']['bundleSize'] = 9999
    result = seq.perform_sequential_validations(record_list_invalid_bundleSize)
    for x in result: x.print()


def build_happy_path(json_seed):
    record_list = []
    json_seed['metadata']['logFileName'] = 'rxMsg_partial_1'
    for i in range(3, 10):
        json_record = copy.deepcopy(json_seed)
        json_record['metadata']['serialId']['recordId'] = i
        json_record['metadata']['serialId']['serialNumber'] = json_seed['metadata']['serialId']['serialNumber'] + i
        record_list.append(json_record)

    json_seed['metadata']['logFileName'] = 'rxMsg_Full'
    for i in range(1, 10):
        json_record = copy.deepcopy(json_seed)
        json_record['metadata']['serialId']['recordId'] = i
        json_record['metadata']['serialId']['serialNumber'] = json_seed['metadata']['serialId']['serialNumber'] + i
        record_list.append(json_record)

    json_seed['metadata']['logFileName'] = 'rxMsg_partial_2'
    for i in range(1, 7):
        json_record = copy.deepcopy(json_seed)
        json_record['metadata']['serialId']['recordId'] = i
        json_record['metadata']['serialId']['serialNumber'] = json_seed['metadata']['serialId']['serialNumber'] + i
        record_list.append(json_record)

    #for record in record_list:
    #    print(json.dumps(record))

    return record_list


main()