# ode-output-validator-library

Contains shared library functions for validating ODE message output schemas and constraints.

The shared library manages all validation checks and constraints are defined in a configuration ini file.

## Installation

TODO - Analyze value of pip support

```
pip install odevalidator
```

Once you have the package installed, import the TestCase class.

```
from odevalidator import TestCase
```

## Functional Interface

#### `TestCase(**kwargs)`

Creates a configured test case object that can be used for validation.

**Request Syntax**

```
test_case = TestCase(
  filepath='string'  
)
```

**Parameters**

- **filepath** (_string_) \[REQUIRED\] Relative or absolute path to configuration file (see more information in the configuration section below).

**Return Type**

`Object`

**Usage Example**
```
test_case = TestCase("./config/bsmLogDuringEvent.ini")
```

#### `.validate(**kwargs)`

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
