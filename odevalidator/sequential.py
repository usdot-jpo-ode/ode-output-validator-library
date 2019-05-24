import json
import dateutil.parser
import copy
from .result import FieldValidationResult, RecordValidationResult

SEQUENTIAL_CHECK = "SequentialCheck"

class Sequential:
    def __init__(self, skip_validations=[]):
        self.skip_validations = skip_validations
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

        return [RecordValidationResult(serial_id = None, field_validations = validation_results, record = None)]

    ### Iterate messages and check that sequential items are sequential
    def validate_bundle(self, sorted_bundle):
        first_record = sorted_bundle[0]
        old_record_id = int(first_record['metadata']['serialId']['recordId'])
        old_serial_number = int(first_record['metadata']['serialId']['serialNumber'])
        old_record_generated_at = dateutil.parser.parse(first_record['metadata']['recordGeneratedAt']).replace(microsecond=0)
        old_ode_received_at = dateutil.parser.parse(first_record['metadata']['odeReceivedAt']).replace(microsecond=0)

        validation_results = []
        for record in sorted_bundle[1:]:
            new_record_id = int(record['metadata']['serialId']['recordId'])
            new_serial_number = int(record['metadata']['serialId']['serialNumber'])
            new_record_generated_at = dateutil.parser.parse(record['metadata']['recordGeneratedAt']).replace(microsecond=0)
            new_ode_received_at = dateutil.parser.parse(record['metadata']['odeReceivedAt']).replace(microsecond=0)

            if 'metadata.serialId.recordId' not in self.skip_validations and record['metadata']['serialId']['bundleSize'] > 1 and new_record_id != old_record_id+1:
                validation_results.append(FieldValidationResult(False, "Detected incorrectly incremented recordId. Expected recordId '%d' but got '%d'" % (old_record_id+1, new_record_id), serial_id = record['metadata']['serialId']))
            if 'metadata.serialId.serialNumber' not in self.skip_validations and new_serial_number != old_serial_number+1:
                validation_results.append(FieldValidationResult(False, "Detected incorrectly incremented serialNumber. Expected serialNumber '%d' but got '%d'" % (old_serial_number+1, new_serial_number), serial_id = record['metadata']['serialId']))
            if 'metadata.recordGeneratedAt' not in self.skip_validations and new_record_generated_at < old_record_generated_at:
                validation_results.append(FieldValidationResult(False, "Detected non-chronological recordGeneratedAt. Previous timestamp was '%s' but current timestamp is '%s'" % (old_record_generated_at, new_record_generated_at), serial_id = record['metadata']['serialId']))
            if 'metadata.odeReceivedAt' not in self.skip_validations and new_ode_received_at < old_ode_received_at:
                validation_results.append(FieldValidationResult(False, "Detected non-chronological odeReceivedAt. Previous timestamp was '%s' but current timestamp is '%s'" % (old_ode_received_at, new_ode_received_at), serial_id = record['metadata']['serialId']))

            old_record_id = new_record_id
            old_serial_number = new_serial_number
            old_record_generated_at = new_record_generated_at
            old_ode_received_at = new_ode_received_at

        if 'metadata.serialId.bundleSize' not in self.skip_validations:
            validation_results.extend(self.validate_bundle_size(sorted_bundle))

        return validation_results

    def validate_bundle_size(self, sorted_bundle):
        first_record_id = int(sorted_bundle[0]['metadata']['serialId']['recordId'])
        last_record_id = int(sorted_bundle[-1]['metadata']['serialId']['recordId'])
        cur_bundle_size = int(sorted_bundle[0]['metadata']['serialId']['bundleSize'])
        prev_bundle_size = None

        validation_results = []
        # partial or full list?
        if first_record_id == 0:
            # head of a partial list?
            if last_record_id == cur_bundle_size - 1:
                # full list
                for record in sorted_bundle:
                    cur_bundle_size = int(record['metadata']['serialId']['bundleSize'])
                    if prev_bundle_size != cur_bundle_size and 'logFileName' in record['metadata'] and len(sorted_bundle) != cur_bundle_size:
                        prev_bundle_size = cur_bundle_size
                        validation_results.append(FieldValidationResult(False, "bundleSize doesn't match number of records. Number of records: '%d' != bundlSize: '%d'" % (len(sorted_bundle), cur_bundle_size), serial_id = sorted_bundle[-1]['metadata']['serialId']))
        else:
            # tail of a partial list
            for record in sorted_bundle:
                cur_bundle_size = int(record['metadata']['serialId']['bundleSize'])
                if prev_bundle_size != cur_bundle_size and last_record_id != cur_bundle_size-1:
                    prev_bundle_size = cur_bundle_size
                    validation_results.append(FieldValidationResult(False, "bundleSize doesn't match last recordId. Last recordId: '%d' != (bundleSize-1: '%d')" % (last_record_id, cur_bundle_size-1), serial_id = sorted_bundle[-1]['metadata']['serialId']))

        return validation_results

    ### Iterate messages and check that sequential items are sequential
    def collect_bundles(self, sorted_record_list):
        first_record = sorted_record_list[0]
        old_bundle_id = first_record['metadata']['serialId']['bundleId']

        bundles = []
        bundle = []
        bundle.append(first_record)
        for record in sorted_record_list[1:]:
            new_bundle_id = record['metadata']['serialId']['bundleId']

            if old_bundle_id == new_bundle_id:
                bundle.append(record)
            else:
                bundles.append(bundle)
                bundle = []
                bundle.append(record)

            old_bundle_id = new_bundle_id

        if len(bundle) > 0:
            bundles.append(bundle)

        return bundles
