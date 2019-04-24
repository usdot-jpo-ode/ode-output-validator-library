[![Build Status](https://travis-ci.org/usdot-jpo-ode/ode-output-validator-library.svg?branch=master)](https://travis-ci.org/usdot-jpo-ode/ode-output-validator-library)[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=ode-output-validator-library&metric=alert_status)](https://sonarcloud.io/dashboard?id=ode-output-validator-library)[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=ode-output-validator-library&metric=coverage)](https://sonarcloud.io/dashboard?id=ode-output-validator-library)
# ode-output-validator-library

Contains shared library functions for validating ODE message output schemas and constraints.

## Table of Contents

1.  [Summary](#summary)
2.  [Quick Start Guide](#quick-start-guide)
3.  [Validation Details and Limitations](#validation-details-and-limitations)
4.  [Configuration](#configuration)
5.  [Unit Testing](#unit-testing)

<a name="summary"/>

## Summary

Messages produced by the ODE have a specific structure, the purpose of this library is to check that the actual messages produced match that structure. This is a black box tool that takes a list of messages, processes them internally, and returns a results object containing validation details of each field of each message.

The constraints on the messages can be considered in two categories as outlined in the **Validation Details and Limitations** section: stateless and stateful checks. Stateless checks are user-configured using the configuration file as detailed in the **Configuration** section, and stateful checks are performed automatically.

<a name="quick-start-guide"/>

## Quick Start Guide

This library comes ready to use right out of the box. To get started testing quickly:

1. Clone this repository and run `install.sh`
2. Run the library as a python module and pass your file (with records separated by newlines) using the `--data-file` argument:

```bash
python -m odevalidator --data-file tests/testfiles/good.json
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
5. Field value is in a certain range


The library is designed to encapsulate functionality that is most useful for all users.
1. `odevalidator` requires only one configuration file.
2. Test cases declare conditional fields or fields that are only checked if some other condition is met.
3. Data files with multiple types of messages will be processed based on the conditional statements in the config file.
4. Test cases can have "optional fields". If fields are declared in the configuration file, they are considered as required
   fields *unless* an `EqualsValue` declaration exists for that field and it provides a conditional and/or optional value for that field.

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

`Object`

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

`dict`

**Response Syntax**
The following are examples of a stateless and stateful responses:

***Stateless***
```
{ 'Results': [
    {
      'RecordID': 123,
      'Validations': [
        {
          'Field': 'string',
          'Valid': True|False,
          'Details': 'string'
        }],
      'Record': 'string'
    }]
}
```

***Stateful***
```
{ 'Results': [
    {
      'RecordID': -1,
      'Validations': [
        {
		  'Field': "SequentialCheck",
          'Valid': True|False,
          'Details': 'string'
        }],
	  'Record': "NA"
    }]
}
```

**Response Structure**

- (_dict_)
  - **Results** (_list_)
    - (_dict_)
      - **RecordID** (_string_) Index of the message, taken from recordId metadata field. _For stateful contextual checks, the value of this field will be set to -1._
      - **Validations** (_list_) List of validation results for each analyzed field.
        - (_dict_)
          - **Field** (_string_) JSON path of the analyzed field. _For stateful contextual checks, the value of this field will be `SequentialCheck`._
          - **Valid** (_boolean_) Whether the field passed validation (True) or failed (False).
          - **Details** (_string_) Further information about the check, including error messages if the check failed.
      - **Record** (_string_) The full record in JSON string format. _For stateful contextual checks, the value of this field will be `NA`._

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
[fieldName]
Path = json.path.to.field
Type = decimal|enum|string|timestamp
Values = ["list", "of", "possible", "values"]
EqualsValue = json
UpperLimit = 123
LowerLimit = -123
```

**Field configuration structure:**

- `Path` \[**REQUIRED**\]
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
- `EqualsValue` \[_optional_\]
  - Summary: Sets the expected value of this field based on the given specifications in json format.
    Validation check for the field will fail if the value does not comply with at least one of the given conditions.
  - Value: Expected value: A json string with the following schema:
```
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "title": "Schema for EqualsValue field of the odevalidator config file.",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "conditions": {
      "description": "This object specifies an array of conditions to be evaluated and matched with the value of this field validation. The specification is in the form of a `if-then` statement. `ifPart` references another data field (`fieldName`) and a list of values (`fieldValues`). `thenPart` provides the valid values for this field validation if the `ifPart` condition is satisifed. If the `ifPart` condition is not satisied, the logic will check the next `condition` until one is satisfied or none are satisifed. If no condition is satisied, the field validation is considered optional. Therefore, if a field is required but conditional, all possible values should be provided as conditions. Search for conditions `short-circuit` as soon as a condition is met.",
      "type": "array",
      "items": {
        "$ref": "#/definitions/Conditions"
      }
    },
    "startsWithField": {
      "description": "The value of this property is a fully qualified path to another data field. The value of this field is expected to be `start` with the value of the referenced data field.",
      "type": "string"
    }
  },
  "Conditions": {
    "ifPart": {
      "description": "This object specifies a condition to be evaluated and matched with the value of the field validation. This specification references another data field (`fieldName`) and a list of paossible valid values (`fieldValues`) to be matched.",
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "fieldName": {
          "description": "This object specifies data field. This condition is met if the value of the field given by the `fieldName` equals one of the values given by `fieldValues`",
          "type": "string"
        },
        "fieldValues": {
          "description": "This element of the `ifPart`a list of values for `fieldName` that would satisfy this condition.",
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      }
    },
    "thenPart": {
      "description": "This element provides the valid values for this field validation given that one of conditions is met. If no condition is satisied, the field validation is considered optional. Therefore, if a field is required but conditional, all possible values should be provided as conditions.",
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}
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
  - Summary: Used with timestamp types to specify the earliest acceptable timestamp for this field
  - Value: ISO timestamp: `EarliestTime = 2018-12-03T00:00:00.000Z`
  - Note: For more information on how to write parsable timestamps, see [dateutil.parser.parse()](https://dateutil.readthedocs.io/en/stable/parser.html#dateutil.parser.parse).
- `LatestTime` \[_optional_\]
  - Summary: Used with timestamp types to specify the latest acceptable timestamp for this field
  - Special value: Use `NOW` to validate that the timestamp is not in the future: `LatestTime = NOW`
  - Value: ISO timestamp: `LatestTime = 2018-12-03T00:00:00.000Z`
  - Note: For more information on how to write parsable timestamps, see [dateutil.parser.parse()](https://dateutil.readthedocs.io/en/stable/parser.html#dateutil.parser.parse).

**[Sample Files](samples)**
- [Sample Configuration File](samples/bsmTx.ini)
- [Sample Data File](bsmTx.json)

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
