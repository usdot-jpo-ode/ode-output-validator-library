from configparser import ConfigParser, ExtendedInterpolation
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
THEN_PART_OPTIONAL = 'optional'

class Field:
    def __init__(self, key, field):
        # extract required settings
        self.path = key
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
            self.equals_value = json.loads(str(equals_value))
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

        self.allow_empty = False
        allow_empty = field.get('AllowEmpty')
        if allow_empty is not None:
            self.allow_empty = True if allow_empty == "True" else False
            

    def validate(self, data):
        field_value = self._get_field_value(self.path, data)

        if hasattr(self, 'equals_value'):
            validation = self.check_value(field_value, data)
        else:
            validation = self._check_unconditional(field_value)

        return validation if validation else ValidationResult(True, "", self)

    def check_value(self, data_field_value, data):
        validation = None

        if isinstance(self.equals_value, Iterable):
            if 'conditions' in self.equals_value:
                conditions = self.equals_value['conditions']
                condition_met = False
                for cond in conditions:
                    if_part = cond['ifPart']
                    refrenced_field_value = self._get_field_value(if_part['fieldName'], data)
                    expected_field_values = if_part['fieldValues'] if 'fieldValues' in if_part else None
                    then_part = cond['thenPart'] if 'thenPart' in cond else None

                    if self._is_condition_met(refrenced_field_value, expected_field_values, data_field_value):
                        condition_met = True
                        # condition is met, now if there is a non-'optional' then_part,
                        # check the value against it. Otherwise, carry on without a validation error
                        validation = self._process_then_part(then_part, data_field_value, data)

                        break # since the condition is met, we are done. We should not check other conditions
                
                if not condition_met:
                    validation = self._check_unconditional(data_field_value)
            else:
                validation = self._check_unconditional(data_field_value)


        return validation

    def _is_condition_met(self, refrenced_field_value, expected_field_values, data_field_value):
        condition_met = False
        if expected_field_values is None:
            # a None for expected_field_values means that refrenced field ('fieldName') may or may not exist
            # If it does not exist, condition is met. If id does exist, condition is not met and value must be checked.
            if not data_field_value:
                condition_met = True
        else:
            # expected_field_values exist so refrenced_field_value must be cheched to decide if condition is met
            if refrenced_field_value in expected_field_values:
                # a None for expected_field_values means that refrenced field ('fieldName') must merely exist
                # condition is met, so now we can check the value
                condition_met = True

        return condition_met

    def _process_then_part(self, then_part, data_field_value, data):
        validation = None
        if then_part and then_part != THEN_PART_OPTIONAL:
            # then_part is not blank, missing nor 'optional'
            if not data_field_value:
                # required field is missing
                validation = ValidationResult(False, "Required Field is missing.", self)
            elif isinstance(then_part, list):
                # then_part must be an array of strings, one of which should match the data_field_value
                if data_field_value not in then_part:
                    # the existing field value is not among the expected values
                    validation = ValidationResult(False, "Value of Field ('%s') is not one of the expected values (%s)" % (data_field_value, then_part), self)
            else:
                # then_part is an object with instruction on how to match the data_field_value
                if 'startsWithField' in then_part:
                    sw_field_name = then_part['startsWithField']
                    sw_field_value = self._get_field_value(sw_field_name, data)
                    if sw_field_value and not data_field_value.startswith(sw_field_value):
                        validation = ValidationResult(False, "Value of Field ('%s') does not start with %s" % (data_field_value, sw_field_value), self)
        
        return validation

    def _get_field_value(self, path_str, data):
        path_keys = path_str.split(".")
        value = data
        for key in path_keys:
            if key in value:
                value = value.get(key)
            else:
                value = None
                break
        return value

    def _check_unconditional(self, data_field_value):
        if data_field_value is None:
            return ValidationResult(False, "Field missing", self)
        else:
            if data_field_value == "":
                if self.allow_empty:
                    return None
                else:
                    return ValidationResult(False, "Field empty", self)
            else:
                if self.type == TYPE_ENUM and str(data_field_value) not in self.values:
                    return ValidationResult(False, "Value '%s' not in list of known values: [%s]" % (str(data_field_value), ', '.join(map(str, self.values))), self)
                elif self.type == TYPE_DECIMAL:
                    if hasattr(self, 'upper_limit') and Decimal(data_field_value) > self.upper_limit:
                        return ValidationResult(False, "Value '%d' is greater than upper limit '%d'" % (Decimal(data_field_value), self.upper_limit), self)
                    if hasattr(self, 'lower_limit') and Decimal(data_field_value) < self.lower_limit:
                        return ValidationResult(False, "Value '%d' is less than lower limit '%d'" % (Decimal(data_field_value), self.lower_limit), self)
                elif self.type == TYPE_TIMESTAMP:
                    try:
                        time_value = dateutil.parser.parse(data_field_value)
                        if hasattr(self, 'earliest_time') and time_value < self.earliest_time:
                            return ValidationResult(False, "Timestamp value '%s' occurs before earliest limit '%s'" % (time_value, self.earliest_time), self)

                        if hasattr(self, 'latest_time') and time_value > self.latest_time:
                            return ValidationResult(False, "Timestamp value '%s' occurs after latest limit '%s'" % (time_value, self.latest_time), self)
                    except Exception as e:
                        return ValidationResult(False, "Failed to perform timestamp validation, error: %s" % (str(e)), self)

class TestCase:
    def __init__(self, filepath=None):
        self.config = ConfigParser(interpolation=ExtendedInterpolation())
        if filepath is None:
            default_config = pkg_resources.resource_string(__name__, "config.ini")
            self.config.read_string(str(default_config, 'utf-8'))
        else:
            if not Path(filepath).is_file():
                raise ValidatorException("Custom configuration file '%s' could not be found" % filepath)
            self.config.read(filepath)

        self.field_list = []
        for key in self.config.sections():
            self.field_list.append(Field(key, self.config[key]))

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
            current_msg = json.loads(line)
            msg_list.append(current_msg)
            serial_id = str(current_msg['metadata']['serialId'])
            sanitized = current_msg['metadata']['sanitized']
            if 'recordType' in current_msg['metadata']:
                record_type = current_msg['metadata']['recordType']
                if sanitized or record_type == 'rxMsg':
                    skip_sequential_checks = True
            field_validations = self._validate(current_msg)
            results.append({
                'SerialId': serial_id,
                'Validations': field_validations,
                'Record': current_msg
            })

        if skip_sequential_checks:
            return {'Results': results}

        seq = Sequential()
        sorted_list = sorted(msg_list, key=lambda msg: msg['metadata']['serialId']['serialNumber'])

        sequential_validations = seq.perform_sequential_validations(sorted_list)
        serialized = []
        for x in sequential_validations:
            serialized.append({
                'Field': "SequentialCheck",
                'Valid': x.valid,
                'Details': x.error
            })

        results.append({
                    'SerialId': None,
                    'Validations': serialized,
                    'Record': "NA"
                })

        return {'Results': results}

