from configparser import ConfigParser, ExtendedInterpolation
import dateutil.parser
from datetime import datetime, timezone, timedelta
import json
import logging
import pkg_resources
import queue
import re
import copy

from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path
from .result import FieldValidationResult, RecordValidationResult, ValidatorException
from .sequential import Sequential, SEQUENTIAL_CHECK

TYPE_DECIMAL = 'decimal'
TYPE_ENUM = 'enum'
TYPE_CHOICE = 'choice'
TYPE_TIMESTAMP = 'timestamp'
TYPE_STRING = 'string'


class Field:
    def __init__(self, key, field_config=None, test_case=None):
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
        if self.type == 'timestamp':
            self.date_format = field_config.get('DateFormat')

        if self.type == 'decimal' or self.type == 'timestamp':
            self.alt = field_config.get('Alt')

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
        choices = field_config.get('Choices')
        if choices is not None:
            self.choices = json.loads(choices)
        equals_value = field_config.get('EqualsValue')
        if equals_value is not None:
            self.equals_value = json.loads(str(equals_value))
        earliest_time = field_config.get('EarliestTime')
        if earliest_time is not None:
            try:
                self.earliest_time = dateutil.parser.parse(earliest_time).replace(microsecond=0)
            except Exception as e:
                raise ValidatorException("Unable to parse configuration file timestamp EarliestTime for field %s=%s, error: %s" % (key, field_config, str(e)))
        latest_time = field_config.get('LatestTime')
        if latest_time is not None:
            if latest_time == 'NOW':
                self.latest_time = datetime.now(timezone.utc)
            else:
                try:
                    self.latest_time = dateutil.parser.parse(latest_time).replace(microsecond=0)
                except Exception as e:
                    raise ValidatorException("Unable to parse configuration file timestamp LatestTime for field %s=%s, error: %s" % (key, field_config, str(e)))
        
        regex = field_config.get('RegularExpression')
        if regex is not None:
            self.regex = regex
        
        self.allow_empty = False
        allow_empty = field_config.get('AllowEmpty')
        if allow_empty is not None:
            self.allow_empty = True if allow_empty == "True" else False

    def validate(self, data):
        field_value = self._get_field_value(self.path, data)
        """if hasattr(self, 'list')
            validation = self.check_list(field_value, data)
        """
        if hasattr(self, 'equals_value'):
            validation = self._check_value(field_value, data)
        else:
            validation = self._check_unconditional(field_value, data)

        return validation if validation else FieldValidationResult(True, "", self.path)

    def _check_value(self, data_field_value, data):
        validation = None

        if isinstance(self.equals_value, Iterable):
            if 'conditions' in self.equals_value:
                conditions = self.equals_value['conditions']
                field_validation_condition_met = False
                for cond in conditions:
                    if_part = cond['ifPart']
                    referenced_field_value = self._get_field_value(if_part['fieldName'], data)
                    expected_field_values = if_part['fieldValues'] if 'fieldValues' in if_part else None
                    then_part = cond['thenPart'] if 'thenPart' in cond else None

                    if self._is_condition_met(referenced_field_value, expected_field_values, data_field_value):
                        if self.test_case and then_part and 'skipSequentialValidation' in then_part and then_part['skipSequentialValidation']:
                            # For skipSequentialValidation, we don't need to do any field validation. We just save this field path for sequential check to use.
                            self.test_case.skip_sequential_checks.add(self.path)
                        elif not field_validation_condition_met:
                            # It's a field validation condition is met, now if there is a non-'optional' then_part,
                            # check the value against it. Otherwise, carry on without a validation error
                            validation = self._check_conditional(then_part, data_field_value, data)

                            # This is NOT a skipSequentialValidation condition and
                            # therefore a field validation condition is met. If it is skipSequentialValidation
                            # we don't consider it a condition for field validation. Also,
                            field_validation_condition_met = True

                if not field_validation_condition_met:
                    validation = self._check_unconditional(data_field_value, data)
            else:
                validation = self._check_unconditional(data_field_value, data)

        return validation

    def _is_condition_met(self, referenced_field_value, expected_field_values, data_field_value):
        condition_met = False
        if expected_field_values is None:
            # a None for expected_field_values means that referenced field ('fieldName') may or may not exist
            # If it does not exist, condition is met. If id does exist, condition is not met and value must be checked.
            if not referenced_field_value and not data_field_value:
                condition_met = True
        else:
            # expected_field_values exist so referenced_field_value must be cheched to decide if condition is met
            if referenced_field_value in expected_field_values:
                # a None for expected_field_values means that referenced field ('fieldName') must merely exist
                # condition is met, so now we can check the value
                condition_met = True
        # if expected_field_values == [] and not referenced_field_value:
        #    condition_met = True

        return condition_met

    def _check_conditional(self, then_part, data_field_value, data):
        validation = None
        if then_part:
            # then_part is not blank, missing nor 'optional'
            if data_field_value == None:
                # required field is missing
                validation = FieldValidationResult(False, "Required Field is missing.", self.path)
            elif 'startsWithField' in then_part:
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

        return validation

    def _get_field_value(self, path_str, data):
        path_keys = path_str.split(".")
        value = data
        for key in path_keys:
            if key in value:
                value = value.get(key)
            elif key.count('{') == 1:
                index_begin = key.index('{')
                index_end = key.index('}')
                index = int(key[(index_begin + 1):index_end])
                try:
                    if value.get(key[:index_begin]):
                        value = value[key[:index_begin]][index]  # access list element of dictionary value
                    else:
                        return None
                except Exception as e:
                    return None
            else:
                return None
        if value is None:
            value = ''
        return value

    def _check_unconditional(self, data_field_value, data):
        if data_field_value is None:
            return FieldValidationResult(False, ("Field missing: " + self.path), self.path)
        else:
            data_field_value = str(data_field_value).strip('"')
            if data_field_value == "":
                if self.allow_empty:
                    return None
                else:
                    return FieldValidationResult(False, "Field empty", self.path)
            else:
                if self.type == TYPE_ENUM and str(data_field_value).lower() not in [x.lower() for x in self.values]:
                    return FieldValidationResult(False, "Value '%s' not in list of known values: [%s]" % (str(data_field_value), ', '.join(map(str, self.values))), self.path)
                elif self.type == TYPE_DECIMAL:
                    try:
                        if hasattr(self, 'upper_limit') and Decimal(str(data_field_value).strip(' %')) > self.upper_limit:
                            return FieldValidationResult(False, "Value '%d' is greater than upper limit '%d'" % (Decimal(str(data_field_value).strip(' %')), self.upper_limit), self.path)
                        if hasattr(self, 'lower_limit') and Decimal(str(data_field_value).strip(' %')) < self.lower_limit:
                            return FieldValidationResult(False, "Value '%d' is less than lower limit '%d'" % (Decimal(str(data_field_value).strip(' %')), self.lower_limit), self.path)
                    except Exception as e:
                        if (self.alt != data_field_value):
                            return FieldValidationResult(False, "Failed to perform decimal validation, error: %s" % (str(e)), self.path)
                elif self.type == TYPE_TIMESTAMP:
                    try:
                        if not self.date_format:
                            time_value = dateutil.parser.parse(data_field_value)
                        else:
                            time_value = datetime.strptime(data_field_value, self.date_format)

                        if hasattr(self, 'earliest_time') and time_value < self.earliest_time:
                            return FieldValidationResult(False, "Timestamp value '%s' occurs before earliest limit '%s'" % (time_value, self.earliest_time), self.path)

                        if hasattr(self, 'latest_time') and time_value > (self.latest_time + timedelta(minutes=1)):
                            return FieldValidationResult(False, "Timestamp value '%s' occurs after latest limit '%s'" % (time_value, self.latest_time), self.path)
                    except Exception as e:
                        if (self.alt != data_field_value):
                            return FieldValidationResult(False, "Failed to perform timestamp validation, error: %s" % (str(e)), self.path)
                elif self.type == TYPE_CHOICE:
                    try:
                        count = 0
                        for choice in self.choices:
                            value = self._get_field_value(self.path + '.' + choice, data)
                            if value is not None:
                                count += 1
                        if count == 0:
                            return FieldValidationResult(False, "No choices found in '%s'" % self.path)
                        if count > 1:
                            return FieldValidationResult(False, "Found '%d' choices in '%s'" % count, self.path)
                    except Exception as e:
                        return FieldValidationResult(False, "Failed to perform choice validation, error: %s" % (str(e)), self.path)
                elif self.type == TYPE_STRING:
                    try:
                        if hasattr(self, 'regex'):
                            match = re.match(self.regex, data_field_value)
                            if match is None:
                                return FieldValidationResult(False, "Regular Expressions found no match in '%s'" % self.path) 
                            elif not(match.group() == data_field_value):
                                return FieldValidationResult(False, "Regular Expressions do not completely match in '%s'" % self.path)
                    except Exception as e:
                        return FieldValidationResult(False, "failure to perform string validation, error: %s" % (str(e)), self.path)

    def __str__(self):
        return json.dumps(self.to_json())

    def to_json(self):
        return {
            'Path': self.path,
            'Type': self.type if hasattr(self, 'type') else None,
            'UpperLimit': self.upper_limit if hasattr(self, 'upper_limit') else None,
            'LowerLimit': self.lower_limit if hasattr(self, 'lower_limit') else None,
            'Values': self.values if hasattr(self, 'values') else None,
            'Choices': self.choices if hasattr(self, 'choices') else None,
            'EqualsValue': self.equals_value if hasattr(self, 'equals_value') else None,
            'EarliestTime': self.earliest_time.isoformat() if hasattr(self, 'earliest_time') else None,
            'LatestTime': self.latest_time.isoformat() if hasattr(self, 'latest_time') else None,
            'AllowEmpty': self.allow_empty if hasattr(self, 'allow_empty') else None}


class TestCase:
    def __init__(self, filepath=pkg_resources.resource_filename('odevalidator', 'configs/config.ini')):
        self.config = ConfigParser(interpolation=ExtendedInterpolation())
        self.record_parser = {"json": json.loads, "csv": self.parse_csv}

        if not Path(filepath).is_file():
            raise ValidatorException("Custom configuration file '%s' could not be found" % filepath)
        self.config.read(filepath)

        if self.config.has_section("_settings"):
            self.data_type = self.config.get("_settings", "DataType")
            self.SequentialValidation = self.config.getboolean("_settings", "Sequential")
            if self.data_type == "csv":
                self.has_header = self.config.getboolean("_settings", "HasHeader")
            else:
                self.has_header = False
        else:
            raise ValidatorException("Invalid config ini file, '_settings' field not defined.")

        self.field_list = []
        self.skip_sequential_checks = set()
        for key in self.config.sections():  # Iterate through config file sections
            if key != "_settings" and key.count('.list') == 0:
                self.field_list.append(Field(key, self.config[key], self))  # Adds field name and parameters to field_list

    def _validate(self, data):
        validations = []
        self.field_list_temp = []
        self.populate_field_list(data)
        field_list = self.field_list + self.field_list_temp
        for field in field_list:
            result = field.validate(data)
            validations.append(result)
        return validations

    def populate_field_list(self, data):  # iniates recurcive function
        field_list = []
        for path in self.config.sections():  # Iterate through config file sections
            if path.count('.list') != 0:
                keys = path.split(".")
                indexes = []
                self.populate_list_validations(keys, data, '', path, indexes)
        return field_list

    def populate_list_validations(self, keys, data, path, path_init, indexes):  # Recurcive function to loop through data and populate
        # list indexes. This works on any number of nested lists.
        if not keys:
            equals_value, new_config = self.set_config_equals_value(path_init, path, indexes)
            self.field_list_temp.append(Field(path, new_config, self))  # Adds field name and parameters to field_list
            if equals_value:
                self.config[path_init]['EqualsValue'] = str(equals_value)
            return

        if keys[0] == 'list':  # List found
            length = len(data)
            if data == '':
                path = path + '{0}'
                keys = self.set_keys(keys)
                indexes.append('{0}')
                self.populate_list_validations(keys, data, path, path_init, copy.deepcopy(indexes))
            if type(data) != list:
                keys = self.set_keys(keys)
                indexes.append('')
                self.populate_list_validations(keys, data, path, path_init, copy.deepcopy(indexes))
            else:
                for i in (range(length)):
                    path_temp = path + '{' + str(i) + '}'
                    keys_temp = keys[1:]
                    data_temp = data[i]
                    indexes.append('{' + str(i) + '}')
                    self.populate_list_validations(keys_temp, data_temp, path_temp, path_init, copy.deepcopy(indexes))  # Recurcive functionality
                    indexes = indexes[:-1]
        elif keys[0] in data:
            try:
                data = data.get(keys[0])
            except Exception as e:
                    print('Non-dictionary encountered with value of: ' + str(data))
                    raise e
            path = self.set_path(path, keys[0])
            keys = self.set_keys(keys)
            self.populate_list_validations(keys, data, path, path_init, copy.deepcopy(indexes))
        elif keys[0].count('{') == 1:  # Index of list hardcoded
            index_begin = keys[0].index('{')
            index_end = keys[0].index('}')
            index = int(keys[0][(index_begin + 1):index_end])
            if keys[0][:index_begin] not in data:
                path = self.set_path(path, keys[0])
                keys = self.set_keys(keys)
                self.populate_list_validations(keys, '', path, path_init, copy.deepcopy(indexes))
            elif type(data[keys[0][:index_begin]]) != list:
                if data.get(keys[0][:index_begin]):
                    data = data[keys[0][:index_begin]]
                else:
                    data = ''
                path = self.set_path(path, keys[0][:index_begin])
                keys = self.set_keys(keys)
                self.populate_list_validations(keys, data, path, path_init, copy.deepcopy(indexes))
            else:
                if data.get(keys[0][:index_begin]):
                    try:
                        data = data[keys[0][:index_begin]][index]
                    except:
                        data = ''
                path = self.set_path(path, keys[0])
                keys = self.set_keys(keys)
                self.populate_list_validations(keys, data, path, path_init, copy.deepcopy(indexes))
        else:  # key not found in data
            path = self.set_path(path, keys[0])
            keys = self.set_keys(keys)
            self.populate_list_validations(keys, '', path, path_init, copy.deepcopy(indexes))

    def set_path(self, path, key):
        if not path:
            path = key
        else:
            path = path + '.' + key
        return path

    def set_keys(self, keys):
        if len(keys) != 1:
            keys = keys[1:]
        else:
            keys = []
        return keys

    def set_config_equals_value(self, path_init, path, indexes):
        config = self.config[path_init]
        equals_value = config.get('EqualsValue')
        if equals_value is not None:
            keys = path_init.split('.')
            embedded_path = keys[0]
            keys = keys[1:]
            for key in keys:
                if embedded_path + '.' + key in equals_value:
                    embedded_path += '.' + key
                else:
                    break
            new_path = embedded_path
            i = 0
            while '.list' in new_path:
                i = new_path.find('.list')
                new_path = new_path[:i] + indexes.pop(0)  + new_path[(i+5):]
            new_equals_value = equals_value.replace(embedded_path, new_path)
            config['EqualsValue'] = new_equals_value
        return equals_value, config

    def validate_queue(self, msg_queue):
        results = []
        msg_list = []
        msg_count = 1
        # if header, skip over it
        if self.has_header:
            header = msg_queue.get()
            self.check_headers(header)

        while not msg_queue.empty():
            line = msg_queue.get().strip()
            current_msg = self.record_parser[self.data_type](line)
            msg_list.append(current_msg)

            # if json data log, serial_id is set to data log's serial_id
            # otherwise, serial_id is set to the log number due to potential lack of actual serial_id
            serial_id = msg_count
            msg_count += 1
            # if self.data_type == "json":
            # serial_id = str(current_msg['metadata']['serialId'])

            field_validations = self._validate(current_msg)
            results.append(RecordValidationResult(serial_id, field_validations, current_msg))

        if self.SequentialValidation:
            seq = Sequential(self.skip_sequential_checks)
            sorted_list = sorted(msg_list, key=lambda msg: msg['metadata']['serialId']['serialNumber'])

            sequential_validation = seq.perform_sequential_validations(sorted_list)

            results.extend(sequential_validation)

        return results

    def parse_csv(self, line):
        csv_dict = {}
        csv_fields = line.split(",")
        index = 0

        for field in self.field_list:
            try:
                csv_dict[field.path] = csv_fields[index]
                index += 1
            except Exception as e:
                raise

        return csv_dict

    def check_headers(self, headers):
        csv_fields = [x.strip() for x in headers.split(",")]
        index = 0
        logger = logging.getLogger("header-logger")
        for field in self.field_list:
            if not str.lower(field.path) == str.lower(csv_fields[index]).strip('"'):
                logger.warning("Warning: The data file CSV header '" + str.lower(csv_fields[index]) + "' does not match the config file field '" + str.lower(field.path) + "'")
            index += 1
