from configparser import ConfigParser, ExtendedInterpolation
import dateutil.parser
from datetime import datetime, timezone, timedelta
import json
import logging
import pkg_resources
import queue
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path
from .result import FieldValidationResult, RecordValidationResult, ValidatorException
from .sequential import Sequential, SEQUENTIAL_CHECK

TYPE_DECIMAL = 'decimal'
TYPE_ENUM = 'enum'
TYPE_TIMESTAMP = 'timestamp'
TYPE_STRING = 'string'

class Field:
    def __init__(self, key, field_config = None, test_case = None):
        # extract required settings
        self.path = key
        if not self.path:
            raise ValidatorException("Invalid configuration property definition for field %s=%s" % (key, field_config))

        if field_config is None:
            return

        self.test_case = test_case

        self.type = field_config.get('Type')
        if not self.type:
            raise ValidatorException("Missing required configuration property 'Type' for field %s=%s" % (key, field_config))

        # extract constraints
        upper_limit = field_config.get('UpperLimit')
        if upper_limit is not None:
            self.upper_limit = Decimal(upper_limit)
        lower_limit = field_config.get('LowerLimit')
        if lower_limit is not None:
            self.lower_limit = Decimal(lower_limit)
        values = field_config.get('Values')
        if values is not None:
            self.values = json.loads(values)
        equals_value = field_config.get('EqualsValue')
        if equals_value is not None:
            self.equals_value = json.loads(str(equals_value))
        earliest_time = field_config.get('EarliestTime')
        if earliest_time is not None:
            try:
                self.earliest_time = dateutil.parser.parse(earliest_time)
            except Exception as e:
                raise ValidatorException("Unable to parse configuration file timestamp EarliestTime for field %s=%s, error: %s" % (key, field_config, str(e)))
        latest_time = field_config.get('LatestTime')
        if latest_time is not None:
            if latest_time == 'NOW':
                self.latest_time = datetime.now(timezone.utc)
            else:
                try:
                    self.latest_time = dateutil.parser.parse(latest_time)
                except Exception as e:
                    raise ValidatorException("Unable to parse configuration file timestamp LatestTime for field %s=%s, error: %s" % (key, field_config, str(e)))

        self.allow_empty = False
        allow_empty = field_config.get('AllowEmpty')
        if allow_empty is not None:
            self.allow_empty = True if allow_empty == "True" else False


    def validate(self, data):
        field_value = self._get_field_value(self.path, data)

        if hasattr(self, 'equals_value'):
            validation = self._check_value(field_value, data)
        else:
            validation = self._check_unconditional(field_value)

        return validation if validation else FieldValidationResult(True, "", self.path)

    def _check_value(self, data_field_value, data):
        validation = None

        if isinstance(self.equals_value, Iterable):
            if 'conditions' in self.equals_value:
                conditions = self.equals_value['conditions']
                field_validation_condition_met = False
                for cond in conditions:
                    if_part = cond['ifPart']
                    refrenced_field_value = self._get_field_value(if_part['fieldName'], data)
                    expected_field_values = if_part['fieldValues'] if 'fieldValues' in if_part else None
                    then_part = cond['thenPart'] if 'thenPart' in cond else None

                    if self._is_condition_met(refrenced_field_value, expected_field_values, data_field_value):
                        # condition is met, now if there is a non-'optional' then_part,
                        # check the value against it. Otherwise, carry on without a validation error
                        validation = self._process_then_part(then_part, data_field_value, data)

                        if validation and validation.field_path != SEQUENTIAL_CHECK:
                            # This means that this is NOT a skipSequentialValidation condition and 
                            # therefore a field validation condition is met. If it is skipSequentialValidation
                            # we don't consider it a condition for field calidation.
                            field_validation_condition_met = True
                
                if not field_validation_condition_met:
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
        if then_part:
            # then_part is not blank, missing nor 'optional'
            if data_field_value == None:
                # required field is missing
                validation = FieldValidationResult(False, "Required Field is missing.", self.path)
            else:
                if 'startsWithField' in then_part:
                    # data_field_value must starts with the value of the given data field
                    sw_field_name = then_part['startsWithField']
                    sw_field_value = self._get_field_value(sw_field_name, data)
                    if sw_field_value and not data_field_value.startswith(sw_field_value):
                        validation = FieldValidationResult(False, "Value of Field ('%s') does not start with %s" % (data_field_value, sw_field_value), self.path)
                elif 'matchAgainst' in then_part and isinstance(then_part['matchAgainst'], list):
                    # then_part is expected to be an array of strings, one of which should match the data_field_value
                    if data_field_value not in then_part['matchAgainst']:
                        # the existing field value is not among the expected values
                        validation = FieldValidationResult(False, "Value of Field ('%s') is not one of the expected values (%s)" % (data_field_value, then_part['matchAgainst']), self.path)
                elif self.test_case and 'skipSequentialValidation' in then_part and then_part['skipSequentialValidation']:
                    self.test_case.skip_sequential_checks.add(self.path)
                    validation = FieldValidationResult(field_path = SEQUENTIAL_CHECK)
        
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
            return FieldValidationResult(False, "Field missing", self.path)
        else:
            if data_field_value == "":
                if self.allow_empty:
                    return None
                else:
                    return FieldValidationResult(False, "Field empty", self.path)
            else:
                if self.type == TYPE_ENUM and str(data_field_value) not in self.values:
                    return FieldValidationResult(False, "Value '%s' not in list of known values: [%s]" % (str(data_field_value), ', '.join(map(str, self.values))), self.path)
                elif self.type == TYPE_DECIMAL:
                    if hasattr(self, 'upper_limit') and Decimal(data_field_value) > self.upper_limit:
                        return FieldValidationResult(False, "Value '%d' is greater than upper limit '%d'" % (Decimal(data_field_value), self.upper_limit), self.path)
                    if hasattr(self, 'lower_limit') and Decimal(data_field_value) < self.lower_limit:
                        return FieldValidationResult(False, "Value '%d' is less than lower limit '%d'" % (Decimal(data_field_value), self.lower_limit), self.path)
                elif self.type == TYPE_TIMESTAMP:
                    try:
                        time_value = dateutil.parser.parse(data_field_value)
                        if hasattr(self, 'earliest_time') and time_value < self.earliest_time:
                            return FieldValidationResult(False, "Timestamp value '%s' occurs before earliest limit '%s'" % (time_value, self.earliest_time), self.path)

                        if hasattr(self, 'latest_time') and time_value > (self.latest_time + timedelta(minutes=1)):
                            return FieldValidationResult(False, "Timestamp value '%s' occurs after latest limit '%s'" % (time_value, self.latest_time), self.path)
                    except Exception as e:
                        return FieldValidationResult(False, "Failed to perform timestamp validation, error: %s" % (str(e)), self.path)

    def __str__(self):
        return json.dumps(self.to_json())

    def to_json(self):
        return {
            'Path': self.path, 
            'Type': self.type if hasattr(self, 'type') else None, 
            'UpperLimit': self.upper_limit if hasattr(self, 'upper_limit') else None, 
            'LowerLimit': self.lower_limit if hasattr(self, 'lower_limit') else None,
            'Values': self.values if hasattr(self, 'values') else None,
            'EqualsValue': self.equals_value if hasattr(self, 'equals_value') else None,
            'EarliestTime': self.earliest_time.isoformat() if hasattr(self, 'earliest_time') else None,
            'LatestTime': self.latest_time.isoformat() if hasattr(self, 'latest_time') else None,
            'AllowEmpty': self.allow_empty if hasattr(self, 'allow_empty') else None}

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
        self.skip_sequential_checks = set()
        for key in self.config.sections():
            self.field_list.append(Field(key, self.config[key], self))

    def _validate(self, data):
        validations = []
        for field in self.field_list:
            result = field.validate(data)
            validations.append(result)
        return validations

    def validate_queue(self, msg_queue):
        results = []
        msg_list = []
        while not msg_queue.empty():
            line = msg_queue.get()
            current_msg = json.loads(line)
            msg_list.append(current_msg)
            serial_id = str(current_msg['metadata']['serialId'])
            field_validations = self._validate(current_msg)
            results.append(RecordValidationResult(serial_id, field_validations, current_msg))

        seq = Sequential(self.skip_sequential_checks)
        sorted_list = sorted(msg_list, key=lambda msg: msg['metadata']['serialId']['serialNumber'])

        sequential_validation = seq.perform_sequential_validations(sorted_list)

        results.extend(sequential_validation)

        return results

