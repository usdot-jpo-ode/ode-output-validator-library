import configparser
import dateutil.parser
import json
import logging
from decimal import Decimal
from pathlib import Path
import queue
from collections.abc import Iterable
import pkg_resources

from .result import ValidationResult, ValidatorException
from .sequential import Sequential

TYPE_DECIMAL = 'decimal'
TYPE_ENUM = 'enum'
TYPE_TIMESTAMP = 'timestamp'
TYPE_STRING = 'string'

def _get_field_value(path_str, data):
    try:
        path_keys = path_str.split(".")
        value = data
        for key in path_keys:
            value = value.get(key)
        return value
    except AttributeError as e:
        raise ValidatorException("Could not find field with path '%s' in message: '%s'" % (path_str, data))

class Field:
    def __init__(self, field):
        # extract required settings
        self.path = field.get('Path')
        if self.path is None:
            raise ValidatorException("Missing required configuration property 'Path' for field '%s'" % field)
        self.type = field.get('Type')
        if self.type is None:
            raise ValidatorException("Missing required configuration property 'Type' for field '%s'" % field)

        # extract constraints
        upper_limit = field.get('UpperLimit')
        if upper_limit is not None:
            self.upper_limit = Decimal(upper_limit)
        lower_limit = field.get('LowerLimit')
        if lower_limit is not None:
            self.lower_limit = Decimal(lower_limit)
        values = field.get('Values')
        if values is not None:
            self.values = json.loads(values)
        increment = field.get('Increment')
        if increment is not None:
            self.increment = int(increment)
        equals_value = field.get('EqualsValue')
        if equals_value is not None:
            self.equals_value = str(equals_value)

    def validate(self, data):
        field_value = _get_field_value(self.path, data)

        if hasattr(self, 'equals_value'):
            result = self.check_value(field_value, data)
            if len(result) > 0:
                return result[0]
        elif field_value is None:
            return ValidationResult(False, "Field missing")
        elif field_value == "":
            return ValidationResult(False, "Field empty")
        elif hasattr(self, 'values') and str(field_value) not in self.values:
            return ValidationResult(False, "Value '%s' not in list of known values: [%s]" % (str(field_value), ', '.join(map(str, self.values))))

        if hasattr(self, 'upper_limit') and Decimal(field_value) > self.upper_limit:
            return ValidationResult(False, "Value '%d' is greater than upper limit '%d'" % (Decimal(field_value), self.upper_limit))
        if hasattr(self, 'lower_limit') and Decimal(field_value) < self.lower_limit:
            return ValidationResult(False, "Value '%d' is less than lower limit '%d'" % (Decimal(field_value), self.lower_limit))


        if self.type == TYPE_TIMESTAMP:
            try:
                if field_value.endswith('[UTC]'):
                    field_value = field_value[:-5]
                dateutil.parser.parse(field_value)
            except Exception as e:
                return ValidationResult(False, "Value could not be parsed as a timestamp, error: %s" % (str(e)))
        return ValidationResult(True, "")

    def check_value(self, data_field_value, data):
        validations = []
        equals_value = json.loads(self.equals_value)

        if isinstance(equals_value, Iterable):
            if 'startsWithField' in equals_value:
                sw_field_name = equals_value['startsWithField']
                sw_field_value = _get_field_value(sw_field_name, data)
                if sw_field_value and not data_field_value.startswith(sw_field_value):
                    validations.append(ValidationResult(False, "Value of Field ('%s') does not start with %s" % (data_field_value, sw_field_value)))

            if 'conditions' in equals_value:
                conditions = equals_value['conditions']
                for cond in conditions:
                    if_part = cond['ifPart']
                    refrenced_field_value = _get_field_value(if_part['fieldName'], data)
                    expected_field_values = if_part['fieldValues']
                    if refrenced_field_value in expected_field_values:
                        # condition is met, so now we can check the value
                        then_part = cond['thenPart']
                        if data_field_value not in then_part:
                            validations.append(ValidationResult(False, "Value of Field ('%s') is not one of the expected values (%s)" % (data_field_value, then_part)))
                        break # since the condition is met, we are done. We should not check other conditions

        return validations


class TestCase:
    def __init__(self, filepath=None):
        self.config = configparser.ConfigParser()
        if filepath is None:
            default_config = pkg_resources.resource_string(__name__, "config.ini")
            self.config.read_string(str(default_config, 'utf-8'))
        else:
            assert Path(filepath).is_file(), "Custom configuration file '%s' could not be found" % filepath
            self.config.read(filepath)

        self.field_list = []
        for key in self.config.sections():
            self.field_list.append(Field(self.config[key]))

    def _validate(self, data):
        validations = []
        for field in self.field_list:
            result = field.validate(data)
            validations.append({
                'Field': field.path,
                'Valid': result.valid,
                'Details': result.error
            })
        return validations

    def validate_queue(self, msg_queue):
        results = []
        msg_list = []
        while not msg_queue.empty():
            line = msg_queue.get()
            if line and not line.startswith('#'):
                current_msg = json.loads(line)
                msg_list.append(current_msg)
                record_id = str(current_msg['metadata']['serialId']['recordId'])
                field_validations = self._validate(current_msg)
                results.append({
                    'RecordID': record_id,
                    'Validations': field_validations,
                    'Record': current_msg
                })

        seq = Sequential()
        sorted_list = sorted(msg_list, key=lambda msg: (msg['metadata']['logFileName'], msg['metadata']['serialId']['recordId']))

        sequential_validations = seq.perform_sequential_validations(sorted_list)
        serialized = []
        for x in sequential_validations:
            serialized.append({
                'Field': "SequentialCheck",
                'Valid': x.valid,
                'Details': x.error
            })

        results.append({
                    'RecordID': -1,
                    'Validations': serialized,
                    'Record': "NA"
                })

        return {'Results': results}

# main function using old functionality
def test(data_file):
    #config_file = "odevalidator/config.ini"
    # Parse test config and create test case
    validator = TestCase()

    results = test_file(validator, data_file)
    print_results(results)

def print_results(results):
    all_good = True
    print("========")
    jsonprint = []
    for res in results['Results']:
        for val in res['Validations']:
            if not val['Valid']:
                all_good = False
                jsonprint.append({"RecordID":res['RecordID'], "Validation":val, "Record": res['Record']})
    if all_good:
        print("Results: SUCCESS")
    else:
        print(jsonprint)
        print("TOTAL FAILURES: %d" % len(jsonprint))

    print("========")


# main function using old functionality
def test_file(validator, data_file):
    print("Testing '%s'." % data_file)

    with open(data_file) as f:
        content = f.readlines()

    # remove whitespace characters like `\n` at the end of each line
    content = [x.strip() for x in content]
    #msgs = [json.loads(line) for line in content]

    q = queue.Queue()
    for msg in content:
        q.put(msg)

    results = validator.validate_queue(q)

    return results
