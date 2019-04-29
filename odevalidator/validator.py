import configparser
import dateutil.parser
import json
import logging
import pkg_resources
import queue
from collections.abc import Iterable
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from .result import ValidationResult, ValidatorException
from .sequential import Sequential

TYPE_DECIMAL = 'decimal'
TYPE_ENUM = 'enum'
TYPE_TIMESTAMP = 'timestamp'
TYPE_STRING = 'string'

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
        equals_value = field.get('EqualsValue')
        if equals_value is not None:
            self.equals_value = str(equals_value)
        earliest_time = field.get('EarliestTime')
        if earliest_time is not None:
            try:
                self.earliest_time = dateutil.parser.parse(earliest_time)
            except Exception as e:
                raise ValidatorException("Unable to parse configuration file timestamp EarliestTime for field %s, error: %s" % (field, str(e)))
        latest_time = field.get('LatestTime')
        if latest_time is not None:
            if latest_time == 'NOW':
                self.latest_time = datetime.now(timezone.utc)
            else:
                try:
                    self.latest_time = dateutil.parser.parse(latest_time)
                except Exception as e:
                    raise ValidatorException("Unable to parse configuration file timestamp LatestTime for field %s, error: %s" % (field, str(e)))

    def validate(self, data):
        field_value = self._get_field_value(self.path, data)

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
                time_value = dateutil.parser.parse(field_value)
                if hasattr(self, 'earliest_time') and time_value < self.earliest_time:
                    return ValidationResult(False, "Timestamp value '%s' occurs before earliest limit '%s'" % (time_value, self.earliest_time))
                if hasattr(self, 'latest_time') and time_value > self.latest_time:
                    return ValidationResult(False, "Timestamp value '%s' occurs after latest limit '%s'" % (time_value, self.latest_time))
            except Exception as e:
                return ValidationResult(False, "Failed to perform timestamp validation, error: %s" % (str(e)))
        return ValidationResult(True, "")

    def check_value(self, data_field_value, data):
        validations = []
        equals_value = json.loads(self.equals_value)

        if isinstance(equals_value, Iterable):
            if 'startsWithField' in equals_value:
                sw_field_name = equals_value['startsWithField']
                sw_field_value = self._get_field_value(sw_field_name, data)
                if sw_field_value and not data_field_value.startswith(sw_field_value):
                    validations.append(ValidationResult(False, "Value of Field ('%s') does not start with %s" % (data_field_value, sw_field_value)))

            if 'conditions' in equals_value:
                conditions = equals_value['conditions']
                for cond in conditions:
                    if_part = cond['ifPart']
                    refrenced_field_value = self._get_field_value(if_part['fieldName'], data)
                    expected_field_values = if_part['fieldValues']
                    if refrenced_field_value in expected_field_values:
                        # condition is met, so now we can check the value
                        then_part = cond['thenPart']
                        if data_field_value not in then_part:
                            validations.append(ValidationResult(False, "Value of Field ('%s') is not one of the expected values (%s)" % (data_field_value, then_part)))
                        break # since the condition is met, we are done. We should not check other conditions

        return validations

    def _get_field_value(self, path_str, data):
        path_keys = path_str.split(".")
        value = data
        for key in path_keys:
            value = value.get(key)
        return value

class TestCase:
    def __init__(self, filepath=None):
        self.config = configparser.ConfigParser()
        if filepath is None:
            default_config = pkg_resources.resource_string(__name__, "config.ini")
            self.config.read_string(str(default_config, 'utf-8'))
        else:
            if not Path(filepath).is_file():
                raise ValidatorException("Custom configuration file '%s' could not be found" % filepath)
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
        skip_sequential_checks = False
        while not msg_queue.empty():
            line = msg_queue.get()
            if line and not line.startswith('#'):
                current_msg = json.loads(line)
                msg_list.append(current_msg)
                record_id = str(current_msg['metadata']['serialId']['recordId'])
                sanitized = current_msg['metadata']['sanitized']
                record_type = current_msg['metadata']['recordType']
                if sanitized or record_type == 'rxMsg':
                    skip_sequential_checks = True
                field_validations = self._validate(current_msg)
                results.append({
                    'RecordID': record_id,
                    'Validations': field_validations,
                    'Record': current_msg
                })

        if skip_sequential_checks:
            return {'Results': results}

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
