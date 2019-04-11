import json
import dateutil.parser
import copy
from .result import ValidationResult

class Sequential:
    def __init__(self):
        return

    ### Iterate messages and check that sequential items are sequential
    def perform_sequential_validations(self, sorted_record_list):
        bundles = self.collect_bundles(sorted_record_list)

        validation_results = []
        for bundle in bundles:
            result = self.validate_bundle(bundle)
            validation_results.extend(result)

        if len(validation_results) == 0:
            validation_results.append(ValidationResult(True))

        return validation_results

    ### Iterate messages and check that sequential items are sequential
    def validate_bundle(self, sorted_bundle):
        firstRecord = sorted_bundle[0]
        old_record_id = int(firstRecord['metadata']['serialId']['recordId'])
        old_serial_number = int(firstRecord['metadata']['serialId']['serialNumber'])
        old_record_generated_at_string = firstRecord['metadata']['recordGeneratedAt']
        if old_record_generated_at_string.endswith('[UTC]'):
            old_record_generated_at_string = old_record_generated_at_string[:-5]
        old_record_generated_at = dateutil.parser.parse(old_record_generated_at_string)
        old_ode_received_at_string = firstRecord['metadata']['odeReceivedAt']
        if old_ode_received_at_string.endswith('[UTC]'):
            old_ode_received_at_string = old_ode_received_at_string[:-5]
        old_ode_received_at = dateutil.parser.parse(old_ode_received_at_string)

        record_num = 1
        validation_results = []
        for record in sorted_bundle[1:]:
            record_num += 1
            new_record_id = int(record['metadata']['serialId']['recordId'])
            new_serial_number = int(record['metadata']['serialId']['serialNumber'])
            new_record_generated_at_string = record['metadata']['recordGeneratedAt']
            if new_record_generated_at_string.endswith('[UTC]'):
                new_record_generated_at_string = new_record_generated_at_string[:-5]
            new_record_generated_at = dateutil.parser.parse(new_record_generated_at_string)
            new_ode_received_at_string = record['metadata']['odeReceivedAt']
            if new_ode_received_at_string.endswith('[UTC]'):
                new_ode_received_at_string = new_ode_received_at_string[:-5]
            new_ode_received_at = dateutil.parser.parse(new_ode_received_at_string)

            if new_record_id != old_record_id+1:
                validation_results.append(ValidationResult(False, "Detected incorrectly incremented recordId. Record Number: '%d' Expected recordId '%d' but got '%d'" % (record_num, old_record_id+1, new_record_id)))
            if new_serial_number != old_serial_number+1:
                validation_results.append(ValidationResult(False, "Detected incorrectly incremented serialNumber. Record Number: '%d' Expected serialNumber '%d' but got '%d'" % (record_num, old_serial_number+1, new_serial_number)))
            if new_record_generated_at < old_record_generated_at:
                validation_results.append(ValidationResult(False, "Detected non-chronological recordGeneratedAt. Record Number: '%d' Previous timestamp was '%s' but current timestamp is '%s'" % (record_num, old_record_generated_at, new_record_generated_at)))
            if new_ode_received_at < old_ode_received_at:
                validation_results.append(ValidationResult(False, "Detected non-chronological odeReceivedAt. Record Number: '%d' Previous timestamp was '%s' but current timestamp is '%s'" % (record_num, old_ode_received_at, new_ode_received_at)))

            old_record_id = new_record_id
            old_serial_number = new_serial_number
            old_record_generated_at = new_record_generated_at
            old_ode_received_at = new_ode_received_at

        validation_results.extend(self.validate_bundle_size(sorted_bundle))

        return validation_results

    def validate_bundle_size(self, sorted_bundle):
        first_record_id = int(sorted_bundle[0]['metadata']['serialId']['recordId'])
        last_record_id = int(sorted_bundle[-1]['metadata']['serialId']['recordId'])
        bundle_size = int(sorted_bundle[0]['metadata']['serialId']['bundleSize'])

        validation_results = []
        # partial or full list?
        if first_record_id == 0:
            # head of a partial list?
            if last_record_id == bundle_size - 1:
                # full list
                for record in sorted_bundle:
                    bundle_size = int(record['metadata']['serialId']['bundleSize'])
                    if len(sorted_bundle) != bundle_size:
                        validation_results.append(ValidationResult(False, "bundleSize doesn't match number of records. recordId: '%d' record length: '%d' != bundlSize: '%d'" % (record['metadata']['serialId']['recordId'], len(sorted_bundle), bundle_size)))

                bundle_size = int(sorted_bundle[0]['metadata']['serialId']['bundleSize'])
                if last_record_id != bundle_size-1:
                    validation_results.append(ValidationResult(False, "bundleSize doesn't match the last recordId of a full set. recordId: '%d' Last recordId: '%d' != bundlSize: '%d'" % (record['metadata']['serialId']['recordId'], last_record_id, bundle_size)))
        else:
            # tail of a partial list
            for record in sorted_bundle:
                bundle_size = int(record['metadata']['serialId']['bundleSize'])
                if last_record_id != bundle_size-1:
                    validation_results.append(ValidationResult(False, "bundleSize doesn't match last recordId of a tail set. recordId: '%d' last recordId: '%d' != bundleSize: '%d'" % (record['metadata']['serialId']['recordId'], last_record_id, bundle_size)))

        return validation_results

    ### Iterate messages and check that sequential items are sequential
    def collect_bundles(self, sorted_record_list):
        firstRecord = sorted_record_list[0]
        old_log_file_name = firstRecord['metadata']['logFileName']

        bundles = []
        bundle = []
        bundle.append(firstRecord)
        for record in sorted_record_list[1:]:
            new_log_file_name = record['metadata']['logFileName']

            if old_log_file_name == new_log_file_name:
                bundle.append(record)
            else:
                bundles.append(bundle)
                bundle = []
                bundle.append(record)

            old_log_file_name = new_log_file_name

        if len(bundle) > 0:
            bundles.append(bundle)

        return bundles

def test():
    seq = Sequential()

    seed_record = '{"metadata":{"logFileName":"rxMsg_1553540811_2620:31:40e0:843::1.csv","serialId":{"streamId":"8a4773d8-ae01-4b86-beae-7cd954a32e06","bundleSize":10,"bundleId":864,"recordId":2,"serialNumber":1000},"odeReceivedAt":"2019-03-25T19:21:06.407Z","recordGeneratedAt":"2019-03-14T14:54:21.596Z"}}'
    json_seed = json.loads(seed_record)

    # test happy path
    print("Testing Happy Path ...")
    record_list = build_happy_path(json_seed)
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


def build_happy_path(json_seed):
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


if __name__ == '__main__':
    test()
