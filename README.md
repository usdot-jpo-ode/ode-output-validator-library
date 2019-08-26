[![Build Status](https://travis-ci.org/usdot-jpo-ode/ode-output-validator-library.svg?branch=master)](https://travis-ci.org/usdot-jpo-ode/ode-output-validator-library)  [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=ode-output-validator-library&metric=alert_status)](https://sonarcloud.io/dashboard?id=ode-output-validator-library)  [![Coverage](https://sonarcloud.io/api/project_badges/measure?project=ode-output-validator-library&metric=coverage)](https://sonarcloud.io/dashboard?id=ode-output-validator-library)
# ode-output-validator-library

Contains shared library functions for validating ODE message output schemas and constraints.

## Table of Contents

1.  [Summary](#summary)
2.  [Quick Start Guide](#quick-start-guide)
3.  [Validation Details and Limitations](#validation-details-and-limitations)
4.  [Configuration](#configuration)
5.  [Unit Testing](#unit-testing)
6.  [Where Used](#where-used)
7.  [Release Notes](#release-notes)

<a name="summary"/>

## Summary

Messages produced by the ODE have a specific structure, the purpose of this library is to check that the actual messages produced match that structure. This is a black box tool that takes a list of messages, processes them internally, and returns a results object containing validation details of each field of each message.

The constraints on the messages can be considered in two categories as outlined in the **Validation Details and Limitations** section: stateless and stateful checks. Stateless checks are user-configured using the configuration file as detailed in the **Configuration** section, and stateful checks are performed automatically.

<a name="quick-start-guide"/>

## Quick Start Guide

This library comes ready to use right out of the box. To get started testing quickly:

1. Clone this repository and run `install.sh`
2. Run the library as a python module and pass your file (with records separated by newlines) using the `--data-file` and `--config` arguments:

```bash
python -m odevalidator --data-file tests/testfiles/good.json --config odevalidator/configs/config.ini
```

If everything worked, you should see these messages:

```bash
Executing local tests...
Testing 'tests/testfiles/good.json'.
========
Results: SUCCESS
========
```

<a name="validation-details-and-limitations"/>

## Validation Details and Limitations

### Validation Details

There are two general types of validation checks: stateless and stateful checks. Users may configure the stateless checks and may invoke the stateful checks by passing a list of messages.

#### 1. Configurable, explicit, stateless checks

A stateless check is the most simple form of check. Simple constraints are defined for single fields in single messages. One of the most basic checks is the EqualsValue check, which looks at a single field in the message and makes sure that it equals something specific. For example if you define your field like this:

```editor-config
[logFileName]
Path = metadata.logFileName
Type = string
EqualsValue = bsmLogDuringEvent.gz
```

And if you receive a message that looks like this:

```json
{
	"metadata": {
		"logFileName": "bsmLogDuringEvent.gz"
	}
}
```

Then the validation library will search the message using the path `metadata.logFileName`, where it will find that the value is set to `bsmLogDuringEvent.gz`. This is exactly equal to the value set in the configuration, so the validation will pass.

Supported stateless checks:

1. Field exists and is not empty (implicit)
3. Field is a specific value
4. Field is one of several specific values
5. Field contains one of several specific objects
6. Field value is in a certain range


The library is designed to encapsulate functionality that is most useful for all users.
1. `odevalidator` requires only one configuration file.
2. Test cases declare conditional fields or fields that are only checked if some other condition is met.
3. Data files with multiple types of messages will be processed based on the conditional statements in the config file.
4. Test cases can have optional fields. If fields are declared in the configuration file, they are considered as required
   fields *unless* an `EqualsValue` declaration exists for that field and it provides a conditional and/or optional value for that field.
   
##### Config File Implementation Examples
```
"pathHistory": {
              "crumbData": [
                {
                  "elevationOffset": 0,
                  "latOffset": 0.0000769,
                  "lonOffset": 0.0000093,
                  "timeOffset": 1.3
                },
                {
                  "elevationOffset": -0.2,
                  "latOffset": 0.0002333,
                  "lonOffset": 0.0001138,
                  "timeOffset": 4.2
                },
                {
                  "elevationOffset": -0.4,
                  "latOffset": 0.0003688,
                  "lonOffset": 0.0001856,
                  "timeOffset": 7.4
                },
                {
                  "elevationOffset": -1.5,
                  "latOffset": 0.0008193,
                  "lonOffset": 0.0001893,
                  "timeOffset": 14.69
                }]
	}
```
	
Above is shown some sample json data, from a BSM log.
The config sections for part of the above data are as follows:

```
[pathHistory.crumbData.list.elevationOffset]
Type = decimal
LowerLimit = 100
EqualsValue = {"conditions":[{"ifPart":{"fieldName":"pathHistory.crumbData.list.elevationOffset"}}]}
```

```
[pathHistory.crumbData.list.latOffset]
Type = decimal
UpperLimit = 100
EqualsValue = {"conditions":[{"ifPart":{"fieldName":"pathHistory.crumbData"}}]}
```

```
[pathHistory.crumbData{0}.timeOffset]
Type = decimal
UpperLimit = 100
```

###### Lists
The existence of a list is specified by adding .list to the field path where the list breaks out into entries. This format can be utilized in both the field name/path and EqualsValue fieldName. If a specific index of a list is desired, utilize curly brackets with the index inside after the name of the list to specif the index. This is shown in the timeOffset config field. 


###### Optional/Mandatory Fields
The EqualsValue fieldName references the optional field that the field depends on. If the field is optional, the fieldName should reference itself. If the field is manditory assuming another field exists (usually its parent), then that field should be referenced in the fieldName. If the field is manditory regardless of other fields then the EqualsValue condition is not necessary.

In the example above, elevationOffset is optional, latOffset is mandatory if crumbData exists, and crumbData{0}.timeOffset is always mandatory. 


###### Choice Type
Some elements in the TIM messages require a choice of 1 object from a set of objects. This is different from an enumeration because an enum is from a set of strings, not a set of objects. An example choice config section is listed below

```
[payload.data.MessageFrame.value.TravelerInformation.dataFrames.TravelerDataFrame.frameType]
Type = choice
Choices = ["unknown", "advisory", "roadSignage", "commercialStorage"]
```

This section describes a series of objects that may exist as children of frameType. The type is specified as choice and the names of these objects are listed in the Choices parameter. This will pass validation if and only if one of the listed objects exists under the parent object.

###### Timestamps
To resolve the issue of unusual timestamp notation in datafiles causing errors in the validation code the addition of a new property has been added to the configuration files. This optional property is called ‘DateFormat’ and can only be specified for a timestamp field. The value provided to the ‘DateFormat’ field is a python strftime expression string that specifies the format of the irregular timestamp in the datafile. Specific documentation on how to make one of these expressions can be found at http://strftime.org/. This property allows previously invalid date formats to be valid if they meet the defined format the data provider can now create for each timestamp field. This is especially useful for data providers that may not be able to change how they are formatting their timestamps but have a consistent format to timestamps for a specific field.

Example Previously Invalid Format: `01-APR-17 12.02.17.833000000 AM`

Example ‘DateFormat’ Value to Validate Format: `%d-%b-%y %I.%M.%S.%f000 %p`

###### Regular Expression
The content of strings of text can be validated by providing a regular expression. This requires a very specific regular expression that will be used for all of the data type's fields that it was provided for. In order t provide the regular expression for a specific string field, the 'RegularExpression' will be defined with the value of the regular expression.

The below example would validate a 7-digit string of numbers such as '1234567':

[fieldName]
Type = string
RegularExpression = \d\d\d\d\d\d\d

This feature can be used to validate uuids and unique dates that might not be so easily validated by the timestamp and its DateFormat property.

#### 2. Non-configurable, implicit, stateful checks

The validation library accepts messages in a list format so that it may validate properties of the list as a whole. These checks include:

1. Message serial numbers and record IDs increment by 1 between messages without gaps or duplication
2. Timestamps from sequential messages are also chronological
3. Number of records in a complete list of records from one specific log file is equal to the `bundleSize`.
If the tail end of a partial list of records from a log file are being analyzed, the number of records in that partial bundle must be less that the `bundleSize`.

These checks require a whole list to be passed in and will vacuously pass when the list has only one message.

**Important note: Messages will NOT be sequentially validated if the library detects that they are either rxMsg type or they have been sanitized by the PPM.**


## Installation

Install the library using the `install.sh` script.

Once you have the package installed, import the TestCase class.

```
from odevalidator import TestCase
```

## Functional Interface

### `TestCase(**kwargs)`

Creates a configured test case object that can be used for validation.

**Request Syntax**

```
test_case = TestCase()
```
or

```
test_case = TestCase(
  filepath='string'
)
```

**Parameters**

- **filepath** (_string_) \[_optional_\] Relative or absolute path to the configuration file (see more information in the configuration section below). If not specified, the library will use the [default validation configuration](odevalidator/config.ini).

**Return Type**

`TestCase` object

**Usage Example**
```
test_case = TestCase()
```
or

```
test_case = TestCase("./config/bsmLogDuringEvent.ini")
```

### `.validate_queue(**kwargs)`

Iterates a message queue and performs validations on each message, returning the results.

**Request Syntax**

```
results = test_case.validate(
  msg_queue=queue.Queue()
)
```

**Parameters**

- **msg_queue** (_queue.Queue_) \[REQUIRED\] A [`queue`](https://docs.python.org/3/library/queue.html) containing messages to be validated.

**Return Type**

Array of `RecordValidationResult` objects:
```
class RecordValidationResult:
    def __init__(self, serial_id, field_validations, record):
        self.serial_id = serial_id
        self.field_validations = field_validations
        self.record = record
```

**Response Syntax**
The following is a truncated examples of the `validate_queue` response. Full sample can be
viewed by following the provided link:

```
[
    {
      "SerialId": "{'recordId': 0, 'serialNumber': 597, 'streamId': '78a7d3a0-8578-496a-85b6-c5796034eaef', 'bundleSize': 1, 'bundleId': 26}",
	"Validations": [{
			"Field": "metadata.recordGeneratedAt",
			"Valid": true,
			"Details": ""
		}, {
			"Field": "metadata.recordGeneratedBy",
			"Valid": true,
			"Details": ""
		},
		...
	],
	"Record": {
		"metadata": {
			"securityResultCode": "success",
			"recordGeneratedBy": "OBU",
		...
	}, {
		"SerialId": null,
		"Validations": [{
				"Field": "SequentialCheck",
				"Valid": true,
				"Details": ""
			}
		],
		"Record": null
	}
]
```

[validate_queue() response Full Sample](validate_queue_response_full_sample.json)


**Response Structure**

- (_list_)
    - (_dict_)
      - **SerialId** (_string_) SerialId field in the message metadata serves as a `key` to uniquely identify the record._
      - **Validations** (_list_) List of validation results for each analyzed field.
        - (_dict_)
          - **Field** (_string_) JSON path of the analyzed field. _For stateful contextual checks, the value of this field will be `SequentialCheck`._
          - **Valid** (_boolean_) Whether the field passed validation (True) or failed (False).
          - **Details** (_string_) Further information about the check, including error messages if the check failed.
      - **Record** (_string_) The full record in JSON string format. _For stateful contextual checks, the value of this field will be `null`._

**Usage Example**
```
msg_queue = queue.Queue()
for msg in my_message_list:
  msg_queue.put(msg)

validation_results = test_case.validate_queue(msg_queue)
```

<a name="configuration"/>

## Configuration

The configuration file is a standard `.ini` file where each field is configured by setting the properties from the list below.

**Field configuration syntax:**

```
[json.path.to.field]
Type = decimal|enum|string|timestamp
Values = ["list", "of", "possible", "values"]
EqualsValue = json
UpperLimit = 123
LowerLimit = -123
AllowEmpty = True
```

**Field configuration structure:**

- `[json.path.to.field]` \[**REQUIRED**\]
  - Summary: Identifies the field location within the message
  - Value: JSON path to the field, separated using periods
  - Example matching `json.path.to.field`:
  ```
  {
    "json": {
      "path": {
        "to": {
          "field": "value"
        }
      }
    }
  }
  ```
- `Type` \[**REQUIRED**\]
  - Summary: Identifies the type of the field
  - Value: One of `enum`, `decimal`, `string`, or `timestamp`
    - enum
      - Specifies that the field must be one of a certain set of values
    - decimal
      - Specifies that the field is a number
    - string
      - Specifies that the field is a string
    - timestamp
      - Values of this type will be validated by testing for parsability
- `AllowEmpty` _[Optional]_
  - Summary: Fields can be specified to allow empty value by setting `AllowEmpty = True`.
  - Value: True or False
- `EqualsValue` \[_optional_\]
  - Summary: Sets the expected value of this field based on the given specifications in json format.
    Validation check for the field will fail if the value does not comply with at least one of the given conditions.
  - Value: Expected value: A json string with the following schema:
```
"$schema": http://json-schema.org/draft-04/schema#
title: Schema for EqualsValue field of the odevalidator config file.
type: object
additionalProperties: false
properties:
  conditions:
    description: This object specifies an array of conditions to be evaluated and
      matched with the value of this field validation. The specification is in the
      form of a `if-then` statement. `ifPart` references another data field (`fieldName`)
      and a list of values (`fieldValues`). `thenPart` provides the valid values for
      this field validation if the `ifPart` condition is satisfied. If the `ifPart`
      condition is not satisied, the logic will check the next `condition` until one
      is satisfied or none are satisfied. If no condition is satisfied, the field validation
      is considered optional. Therefore, if a field is required but conditional, all
      possible values should be provided as conditions. Search for conditions `short-circuit`
      as soon as a condition is met.
    type: array
    items:
      "$ref": "#/definitions/Conditions"

definitions:
  Conditions:
    ifPart:
      description: This object specifies a condition to be evaluated and matched with
        the value of the field validation. This specification references another data
        field (`fieldName`) and a list of paossible valid values (`fieldValues`) to
        be matched.
      type: object
      additionalProperties: false
      properties:
        fieldName:
          description: This object specifies data field. This condition is met if
            the value of the field given by the `fieldName` equals one of the values
            given by `fieldValues`
          type: string
        fieldValues:
          description: This element of the `ifPart`a list of values for `fieldName`
            that would satisfy this condition.
          type: array
          items:
            type: string
    thenPart:
      description: This element provides the valid values for this field validation
        given that one of conditions is met. If no condition is satisfied, the field
        validation is considered optional. Therefore, if a field is required but conditional,
        all possible values should be provided in the `fieldValues` of all the conditions,
        collectively. If a possible value is not included in a condition, the field
        will be treated as required for that value. Python configuration file variable
        dereferencing (for example, ${Values} or ${metadata.recordType:Values}) can
        be used to reference any the value of any configuration item when specifying
        the condition. `then_part` can be an empty array or completely missing which
        would mean that the field is optional if the `if_part` condition is met. The
        `fieldValue` of the `ifPart` can also be eliminated which would mean that
        if the field identified by the `fieldName` of the `ifPart` exists, the field
        has to be validated. If it the field doesn't exist, it is considered optional
        and no validation error is issued.
      type: array
      items:
        type:
          "$ref": "#/definitions/ThenPart"

  ThenPart:
    description: This is the data schema for `thenPart` component of `EqualsValue` config option
    type: object
    properties:
      startsWithField:
        description: The value of this property is a fully qualified path to another data field.
          The value of this field is expected to `start` with the value of
          the referenced data field.
        type: string

      matchAgainst:	  
        description: The value of this property is an array of values. The data fields
          value should match one of the values in this array to be considered valid.
        type: array
        items:
          type: string

      skipSequentialValidation:
        description: This boolean property specifies if this sequential or chronological field should take part in sequential validation or not.
          set the value of this property to True if you would like to skip sequential validation of this field.
        type: boolean
```

The following conditional field validation states that the value of `metadata.payloadType` must be equal `us.dot.its.jpo.ode.model.OdeBsmPayload` if
`metadata.recordType` field is equal `bsmLogDuringEvent` or `bsmTx`.
```
[payloadType]
Path = metadata.payloadType
Type = string
EqualsValue = {"conditions":[{"ifPart":{"fieldName":"metadata.recordType","fieldValues":["bsmLogDuringEvent","bsmTx"]},"thenPart":["us.dot.its.jpo.ode.model.OdeBsmPayload"]},{"ifPart":{"fieldName":"metadata.recordType","fieldValues":["dnMsg"]},"thenPart":["us.dot.its.jpo.ode.model.OdeTimPayload"]},{"ifPart":{"fieldName":"metadata.recordType","fieldValues":["driverAlert"]},"thenPart":["us.dot.its.jpo.ode.model.OdeDriverAlertPayload"]},{"ifPart":{"fieldName":"metadata.receivedMessageDetails.rxSource","fieldValues":["RV"]},"thenPart":["us.dot.its.jpo.ode.model.OdeBsmPayload"]},{"ifPart":{"fieldName":"metadata.receivedMessageDetails.rxSource","fieldValues":["RSU","SAT","SNMP","NA"]},"thenPart":["us.dot.its.jpo.ode.model.OdeTimPayload"]}]}

```

Below is the EqualsValue in a more readable JSON format. This specifies that
`payloadType` must match the value given in `thenPart` depending on the value of
`metadata.recordType`. So
- if `metadata.recordType` is either `bsmLogDuringEvent` or `bsmTx`,
`payloadType` must be `us.dot.its.jpo.ode.model.OdeBsmPayload`.
- if `metadata.recordType` is `dnMsg`,
`payloadType` must be `us.dot.its.jpo.ode.model.OdeTimPayload`.
- if `metadata.recordType` is `driverAlert`,
`payloadType` must be `us.dot.its.jpo.ode.model.OdeDriverAlertPayload`.
- if `metadata.receivedMessageDetails.rxSource` is `RV`,
`payloadType` must be `us.dot.its.jpo.ode.model.OdeTimPayload`.

```
{
  "conditions": [
    {
      "ifPart": {
        "fieldName": "metadata.recordType",
        "fieldValues": [
          "bsmLogDuringEvent",
          "bsmTx"
        ]
      },
      "thenPart": [
        "us.dot.its.jpo.ode.model.OdeBsmPayload"
      ]
    },
    {
      "ifPart": {
        "fieldName": "metadata.recordType",
        "fieldValues": [
          "dnMsg"
        ]
      },
      "thenPart": [
        "us.dot.its.jpo.ode.model.OdeTimPayload"
      ]
    },
    {
      "ifPart": {
        "fieldName": "metadata.recordType",
        "fieldValues": [
          "driverAlert"
        ]
      },
      "thenPart": [
        "us.dot.its.jpo.ode.model.OdeDriverAlertPayload"
      ]
    },
    {
      "ifPart": {
        "fieldName": "metadata.receivedMessageDetails.rxSource",
        "fieldValues": [
          "RV"
        ]
      },
      "thenPart": [
        "us.dot.its.jpo.ode.model.OdeBsmPayload"
      ]
    },
    {
      "ifPart": {
        "fieldName": "metadata.receivedMessageDetails.rxSource",
        "fieldValues": [
          "RSU",
          "SAT",
          "SNMP",
          "NA"
        ]
      },
      "thenPart": [
        "us.dot.its.jpo.ode.model.OdeTimPayload"
      ]
    }
  ]
}
```

The following field validation specifies that `logFileName` must start with the same string as the value of `metadata.recordType`.

```
[logFileName]
Path = metadata.logFileName
Type = string
EqualsValue = {"startsWithField": "metadata.recordType"}
```

- `Values` \[_optional_\]
  - Summary: Used with enum types to specify the list of possible values that this field must be
  - Value: JSON array with values in quotes: `Values = ["OptionA", "OptionB", ]`
- `LowerLimit` \[_optional_\]
  - Summary: Used with decimal types to specify the lowest acceptable value for this field
  - Value: decimal number: `LowerLimit = 2`
- `UpperLimit` \[_optional_\]
  - Summary: Used with decimal types to specify the highest acceptable value for this field
  - Value: decimal number: `UpperLimit = 150.43`
- `EarliestTime` \[_optional_\]
  - Summary: Used with timestamp types to specify the earliest acceptable timestamp for this field down to second-level precision
  - Value: ISO timestamp: `EarliestTime = 2018-12-03T00:00:00.000Z`
  - Note: For more information on how to write parsable timestamps, see [dateutil.parser.parse()](https://dateutil.readthedocs.io/en/stable/parser.html#dateutil.parser.parse).
- `LatestTime` \[_optional_\]
  - Summary: Used with timestamp types to specify the latest acceptable timestamp for this field down to second-level precision
  - Special value: Use `NOW` to validate that the timestamp is not in the future: `LatestTime = NOW`
  - Value: ISO timestamp: `LatestTime = 2018-12-03T00:00:00.000Z`
  - Note: For more information on how to write parsable timestamps, see [dateutil.parser.parse()](https://dateutil.readthedocs.io/en/stable/parser.html#dateutil.parser.parse).
- `Alt` \[_optional_\]
  - Summary: Used with decimal and timestamp types to specify an alternate value that might exist if there is not a decimal value
  - Value: A string such as `Alt = NA` or `Alt = null`


The following field validation specifies that sequential validation should NOT be enacted on `metadata.recordGeneratedAt` when the record is generated
by TMC (`"metadata.recordGeneratedBy":"TMC"`).

```
[metadata.recordGeneratedAt]
Type = timestamp
LatestTime = NOW
EqualsValue = {"conditions":[{"ifPart":{"fieldName":"metadata.recordGeneratedBy","fieldValues":["TMC"]},"thenPart":{"skipSequentialValidation":"true"}}]}
```

The following field validation specifies that sequential validation should NOT be enacted on `metadata.serialId.recordId` when the records is from
and `rxMsg` OR the records is _santiized_ (`"metadata.sanitized": "True"`.
fields when

```
[metadata.serialId.recordId]
Type = decimal
UpperLimit = 2147483647
LowerLimit = 0
EqualsValue = {"conditions":[
    {"ifPart":{"fieldName":"metadata.recordType","fieldValues":["rxMsg"]},"thenPart":{"skipSequentialValidation":"true"}},
    {"ifPart":{"fieldName":"metadata.sanitized","fieldValues":["True"]},"thenPart":{"skipSequentialValidation":"true"}}]}
```

**Files**
- [Default Configuration File](odevalidator/config.ini)
- [Sample Data File](../../../data/bsmTx.json)

<a name="unit-testing"/>

## Unit Testing

This library includes unit tests built using the [`unittest`](https://docs.python.org/3/library/unittest.html) Python framework. They can be run using the _setup.py_ module.

<details><summary>1. Activate virtualenv</summary>
<p>

```bash
virtualenv -p python3 virtualenv
source virtualenv/bin/activate
```

</p>
</details>

2. Install the library

```bash
./install.sh
```

3. Run the tests

```bash
./unittest.sh
```


<details><summary>4. Deactivate virtualenv</summary>
<p>

```bash
deactivate
```

</p>
</details>

<a name="where-used"/>

## Where Used
This library is used in the following test and verification applications as of this release:

* [ODE Test Harness](https://github.com/usdot-jpo-ode/jpo-ode)
* [DataHub Canary](https://github.com/usdot-its-jpo-data-portal/canary-lambda)

<a name="release-notes"/>

## Release Notes

### Release 0.0.8
- Regular expression validation for strings

### Release 0.0.8
- Added support for alternate values for decimal and timestamp type fields
- Added support for '%' symbols appearing at the end of a decimal field value
- Changed choices to accept empty fields and properly invalidate them instead of throwing an exception
- Minor bug fixes resolved with validating explicitly defined list elements

### Release 0.0.7
- Added complete validation of payload for BSM and TIM message types
  - Lists and arbitrarily nested lists are now supported
  - Validation for choice elements (only 1 object of a set is allowed) are now supported
  - EqualsValue logic now allows mandatory fields within optional fields
  - Added specific configuration files for BSM and TIM message types with payload fields
- Added flexible date format parsing with the inclusion of a `DateFormat` parameter in configuration files for unusually formatted timestamps using python strftime strings
  - Example: For the timestamp `01-APR-17 12.02.17.833000000 AM` the proper `DateFormat` would be `%d-%b-%y %I.%M.%S.%f000 %p`
  - Documentation on how to create a python strftime format string can be found at `http://strftime.org/`

### Release 0.0.6
- Reduced precision of timestamp parsing to second-level instead of microsecond-level to allow roughly 1 second of tolerance

### Release 0.0.5
- Added support for CSV files
  - Added `--config-file` command-line argument
  - Added `[_settings]` block to configuration file
    - Added `DataType` settings configuration property
    - Added `Sequential` settings configuration property
    - Added `HasHeader` settings configuration property
  - Added example csv configuration file `odevalidator/csvconfig.ini`
  - Added csv test files
- Removed timestamp sanity check from odeReceivedAt field

### Release 0.0.4
* Config.ini changes
	* Added `metadata.request` elements to config.ini
	* Eliminated the Path option in config.ini because the section keys have to be unique and there
is always a possibility that two keys at different structures be named the same. SO now the section key
has to be the ful path of the field name.
	* Took advantage of python configuration file variable dereferencing
	* `config.ini` `then_part` can now be an empty array or completely missing which would mean that the field is
optional if the `if_part` condition is met.
	* The `fieldValue` of the `ifPart` can also be eliminated which would mean that the if the field identified by
the `fieldName` of the `ifPart` exists, the field has to be validated. If it the field doesn't exist,
it is considered optional and no validation error is issued.
	* Fields can now be specified to allow empty value by setting `AllowEmpty = True`. Currently only
`elevation` is allowed to be empty.
* Added field info to `FieldValidationResult` (renamed from ValidationResult) objects
* Added serialId to the `RecordValidationResult` (NEW) object. This replaces RecordID.
* `Field, FieldValidationResult and RecordValidationResult` objects now have `__str__()` method
which allows them to be serialized for printing purposes.
* Test files `good.json` and `bad.json` were updated with new tests for Broadcast TIM

### Release 0.0.3
Various clean ups to make the library production ready.

### Release 0.0.2
Added optional and conditional configuration of field validations allowing the same
config file to be used accross mutltiple data types/schemas.

### Release 0.0.1
Initial Release of odevalidator including the following features:

* Validation of each data field based on the configuration parameters providing valid values,
and ranges.
* Validation of sequential fields such as recordId, serialNumber, timestamps detecting
gaps and duplication of the sequential numbers and out of order timestamps.
