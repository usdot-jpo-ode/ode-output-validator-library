import json
import dateutil.parser
import copy
from .result import FieldValidationResult

SEQUENTIAL_CHECK = "SequentialCheck"

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
            validation_results.append(FieldValidationResult(True, details = "", field_path = SEQUENTIAL_CHECK))

        return validation_results

    ### Iterate messages and check that sequential items are sequential
    def validate_bundle(self, sorted_bundle):
        first_record = sorted_bundle[0]
        old_record_id = int(first_record['metadata']['serialId']['recordId'])
        old_serial_number = int(first_record['metadata']['serialId']['serialNumber'])
        old_record_generated_at = dateutil.parser.parse(first_record['metadata']['recordGeneratedAt'])
        old_ode_received_at = dateutil.parser.parse(first_record['metadata']['odeReceivedAt'])

        record_num = 1
        validation_results = []
        for record in sorted_bundle[1:]:
            record_num += 1
            new_record_id = int(record['metadata']['serialId']['recordId'])
            new_serial_number = int(record['metadata']['serialId']['serialNumber'])
            new_record_generated_at = dateutil.parser.parse(record['metadata']['recordGeneratedAt'])
            new_ode_received_at = dateutil.parser.parse(record['metadata']['odeReceivedAt'])

            if record['metadata']['serialId']['bundleSize'] > 1 and new_record_id != old_record_id+1:
                validation_results.append(FieldValidationResult(False, "Detected incorrectly incremented recordId. Record Number: '%d' Expected recordId '%d' but got '%d'" % (record_num, old_record_id+1, new_record_id), SEQUENTIAL_CHECK))
            if new_serial_number != old_serial_number+1:
                validation_results.append(FieldValidationResult(False, "Detected incorrectly incremented serialNumber. Record Number: '%d' Expected serialNumber '%d' but got '%d'" % (record_num, old_serial_number+1, new_serial_number), SEQUENTIAL_CHECK))
            if new_record_generated_at < old_record_generated_at:
                validation_results.append(FieldValidationResult(False, "Detected non-chronological recordGeneratedAt. Record Number: '%d' Previous timestamp was '%s' but current timestamp is '%s'" % (record_num, old_record_generated_at, new_record_generated_at), SEQUENTIAL_CHECK))
            if new_ode_received_at < old_ode_received_at:
                validation_results.append(FieldValidationResult(False, "Detected non-chronological odeReceivedAt. Record Number: '%d' Previous timestamp was '%s' but current timestamp is '%s'" % (record_num, old_ode_received_at, new_ode_received_at), SEQUENTIAL_CHECK))

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
                    if 'logFileName' in record['metadata'] and len(sorted_bundle) != bundle_size:
                        validation_results.append(FieldValidationResult(False, "bundleSize doesn't match number of records. recordId: '%d' record length: '%d' != bundlSize: '%d'" % (record['metadata']['serialId']['recordId'], len(sorted_bundle), bundle_size), SEQUENTIAL_CHECK))

                bundle_size = int(sorted_bundle[0]['metadata']['serialId']['bundleSize'])
                if last_record_id != bundle_size-1:
                    validation_results.append(FieldValidationResult(False, "bundleSize doesn't match the last recordId of a full set. recordId: '%d' Last recordId: '%d' != bundlSize: '%d'" % (record['metadata']['serialId']['recordId'], last_record_id, bundle_size), SEQUENTIAL_CHECK))
        else:
            # tail of a partial list
            for record in sorted_bundle:
                bundle_size = int(record['metadata']['serialId']['bundleSize'])
                if last_record_id != bundle_size-1:
                    validation_results.append(FieldValidationResult(False, "bundleSize doesn't match last recordId of a tail set. recordId: '%d' last recordId: '%d' != bundleSize: '%d'" % (record['metadata']['serialId']['recordId'], last_record_id, bundle_size), SEQUENTIAL_CHECK))

        return validation_results

    ### Iterate messages and check that sequential items are sequential
    def collect_bundles(self, sorted_record_list):
        first_record = sorted_record_list[0]
        old_log_file_name = first_record['metadata']['logFileName'] if 'logFileName' in first_record['metadata'] else "NA"

        bundles = []
        bundle = []
        bundle.append(first_record)
        for record in sorted_record_list[1:]:
            new_log_file_name = record['metadata']['logFileName'] if 'logFileName' in record['metadata'] else "NA"

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
