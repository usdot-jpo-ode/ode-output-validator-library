import json
import dateutil.parser
import copy

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
        is_valid = True
        record_num = 1
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
                    is_valid = False
                    print("WARNING! Detected incorrectly incremented recordId. Record Number: '%d' Expected '%d' but got '%d'" % (record_num, old_record_id+1, new_record_id))
                    print(record)
                if new_serial_number != old_serial_number+1:
                    is_valid = False
                    print("WARNING! Detected incorrectly incremented serialNumber. Record Number: '%d' Expected '%d' but got '%d'" % (record_num, old_serial_number+1, new_serial_number))
                    print(record)
                if new_record_generated_at < old_record_generated_at:
                    is_valid = False
                    print("WARNING! Detected non-chronological recordGeneratedAt. Record Number: '%d' Previous timestamp was '%s' but current timestamp is '%s'" % (record_num, old_record_generated_at, new_record_generated_at))
                if new_ode_received_at < old_ode_received_at:
                    is_valid = False
                    print("WARNING! Detected non-chronological odeReceivedAt. Record Number: '%d' Previous timestamp was '%s' but current timestamp is '%s'" % (record_num, old_ode_received_at, new_ode_received_at))
                    print(record)
            else:
                print("New log file detected. Resetting old item values. Record Number: '%d' Old filename: '%s', new filename: '%s'" % (record_num, old_log_file_name, new_log_file_name))
                if not self.validate_bundle_size(one_list):
                    is_valid = False
                    break
                one_list.clear()
                one_list.append(record)

            old_log_file_name = new_log_file_name
            old_record_id = new_record_id
            old_serial_number = new_serial_number
            old_record_generated_at = new_record_generated_at
            old_ode_received_at = new_ode_received_at

            if not is_valid:
                break
            
        return is_valid

    def validate_bundle_size(self, sorted_record_list):
        is_valid = True
        first_record_id = int(sorted_record_list[0]['metadata']['serialId']['recordId'])
        last_record_id = int(sorted_record_list[-1]['metadata']['serialId']['recordId'])

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
                        print("WARNING! buldleSize doesn't match number of records. Record Number: '%d' record length: '%d' != bundlSize: '%d'" % (record_num, sorted_record_list.len(), bundle_size))
                        is_valid = False
                        break

                bundle_size = int(sorted_record_list[0]['metadata']['serialId']['bundleSize'])
                if last_record_id != bundle_size:
                    print("WARNING! buldleSize doesn't match the last recordId. Record Number: '%d' Last recordId: '%d' != bundlSize: '%d'" % (record_num, last_record_id, bundle_size))
                    is_valid = False
        else:
            # tail of a partial list
            record_num = 0
            for record in sorted_record_list:
                record_num += 1
                bundle_size = int(record['metadata']['serialId']['bundleSize'])
                if last_record_id != bundle_size:
                    print("WARNING! buldleSize doesn't match last recordId. Record Number: '%d' last recordId: '%d' != bundleSize: '%d'" % (record_num, last_record_id, bundle_size))
                    is_valid = False
                    break

        return is_valid

def main():
    seq = Sequential()

    seed_record = '{"metadata":{"logFileName":"rxMsg_1553540811_2620:31:40e0:843::1.csv","serialId":{"streamId":"8a4773d8-ae01-4b86-beae-7cd954a32e06","bundleSize":9,"bundleId":864,"recordId":2,"serialNumber":1000},"odeReceivedAt":"2019-03-25T19:21:06.407Z","recordGeneratedAt":"2019-03-14T14:54:21.596Z"}}'
    json_seed = json.loads(seed_record)

    # test happy path
    record_list = build_happy_path(json_seed)
    result = seq.perform_sequential_validations(record_list)
    print("Happy Path result: %s" %(result))

    # test missing/duplicate recordId
    record_list_missing = copy.deepcopy(record_list)
    prev_record = record_list_missing[0]
    for record in record_list_missing[1:]:
        record['metadata']['serialId']['recordId'] = prev_record['metadata']['serialId']['recordId']
    result = seq.perform_sequential_validations(record_list_missing)
    print("Missing/dups result: %s" %(result))

    # test invalid bundleSize
    record_list_invalid_buncldeSize = copy.deepcopy(record_list)
    for record in record_list_invalid_buncldeSize:
        record['metadata']['serialId']['bundleSize'] = 9999
    result = seq.perform_sequential_validations(record_list_invalid_buncldeSize)
    print("Invalid Bundle Size result: %s" %(result))


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