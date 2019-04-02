# ode-output-validator-library

Contains shared library functions for validating ODE message output schemas and constraints.

## Summary

Messages produced by the ODE have a specific structure, the purpose of this library is to check that the actual messages produced match that structure. This is a black box tool that takes a list of messages, processes them internally, and returns a results object containing validation details of each field of each message.

The constraints on the messages can be considered in two categories as outlined in the **Testing Details and Limitations** section: stateless and stateful checks. Stateless checks are user-configured using the configuration file as detailed in the **Configuration** section, and stateful checks are performed automatically.


## Testing Details and Limitations

### Testing Details

There are two general types of checks: stateless and stateful checks. Users may configure the stateless checks and may invoke the stateful checks by passing a list of messages.

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

#### 2. Non-configurable, implicit, stateful checks

The validation library accepts messages in a list format so that it may validate properties of the list as a whole. These checks include:

1. Message serial numbers and record IDs increment by 1 between messages without gaps or duplication
2. Timestamps from sequential messages are also chronological
3. Number of records in a list from one specific log file is less than or equal to the bundleSize

These checks require a whole list to be passed in and will vacuously pass when the list has only one message.

### Testing Limitations

The library is designed to encapsulate functionality that is most useful for all users. As a result some additional functionalities are not supported directly by the library and require wrapper code:

1. A test case can only be initialized with one configuration file. Data files with multiple types of messages will require separate TestCases objects for each message type.
2. Test cases cannot define optional fields. If fields are declared in the configuration file, they must appear in the message or else the validation is considered failed.
3. Test cases cannot define conditional fields or fields that are only checked if some other state is condition is met.

## Installation

Pip may be used to install the library locally, or by using pip to manage and pull the library from Github directly.

```
pip install .
```

Once you have the package installed, import the TestCase class.

```
from odevalidator import TestCase
```

## Functional Interface

### `TestCase(**kwargs)`

Creates a configured test case object that can be used for validation.

**Request Syntax**

```
test_case = TestCase(
  filepath='string'
)
```

**Parameters**

- **filepath** (_string_) \[_optional_\] Relative or absolute path to the configuration file (see more information in the configuration section below).

**Return Type**

`Object`

**Usage Example**
```
test_case = TestCase("./config/bsmLogDuringEvent.ini")
```

### `.validate(**kwargs)`

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
```
{ 'Results': [
    {
      'RecordID': 123,
      'Validations': [
        {
          'Field': 'string',
          'Valid': True|False,
          'Details': 'string'
        }]
    }]
}
```

**Response Structure**

- (_dict_)
  - **Results** (_list_)
    - (_dict_)
      - **RecordID** (_string_) Index of the message, taken from recordId metadata field.
      - **Validations** (_list_) List of validation results for each analyzed field.
        - (_dict_)
          - **Field** (_string_) Path or name of the analyzed field.
          - **Valid** (_boolean_) Whether the field passed validation (True) or failed (False).
          - **Details** (_string_) Further information about the check, including error messages if the check failed.

**Usage Example**
```
msg_queue = queue.Queue()
for msg in my_message_list:
  msg_queue.put(msg)

validation_results = test_case.validate(msg_queue)
```

## Configuration

The configuration file is a standard .ini file where each field is configured by setting the properties from the list below.

**Field configuration syntax:**

```
[fieldName]
Path = json.path.to.field
Type = decimal|enum|string|timestamp
Values = ["list", "of", "possible", "values"]
EqualsValue = expectedValueOfField
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
  - Summary: Sets the expected value of this field, will fail if the value does not match this
  - Value: Expected value: `EqualsValue = us.dot.its.jpo.ode.model.OdeBsmPayload`
- `Values` \[_optional_\]
  - Summary: Used with enum types to specify the list of possible values that this field must be
  - Value: JSON array with values in quotes: `Values = ["OptionA", "OptionB", ]`
- `LowerLimit` \[_optional_\]
  - Summary: Used with decimal types to specify the lowest acceptable value for this field
  - Value: decimal number: `LowerLimit = 2`
- `UpperLimit` \[_optional_\]
  - Summary: Used with decimal types to specify the highest acceptable value for this field
  - Value: decimal number: `UpperLimit = 150.43`

**[Sample Files](samples)**
- [Sample Configuration File](samples/bsmTx.ini)
- [Sample Data File](bsmTx.json)
