# validating-base

A simple Validating Base Class library. Enables runtime validation of argument types using typeguard.

All you need to do is inherit from the `ValidatingBaseClass` class, type hint ([more info](https://docs.python.org/3/library/typing.html)) all the methods, and then specify the methods that you want to validate.

See the [tests](./tests/test_base.py) for some better examples of usage.

## Installation

To install the project you only need to clone the repo and run pip install within the repo folder:

```bash
pip install .
```

Or you can install directly from GitHub:

```bash
pip install git+https://github.com/alexfayers/validating-base
```

## Usage

You use validating-base by importing the base class and inheriting from it.

Below is an example, taken from the project's tests, that shows simple usage.

Anything that inherits from `ValidatingBaseClass` will need to implement an `action` method (because this is specified in the `required_methods` class variable).

This method will have it's argument types validated at runtime using simple type checking (because the method is specified in the `validated_methods` class variable) (this step is provided by typeguard).

If the first type checking step passes with no exceptions, then the `validate_action` method will be called. This method validates that the `number_list` argument is a list of integers.

Finally, the return type of the `action` method is validated using typeguard.

```py
from typeguard import _CallMemo
from validating_base import ValidatingBaseClass

class ActionExample(ValidatingBaseClass):
    """Shows an example usage of the `validating_base.ValidatingBaseClass` class."""

    required_methods: list[str] = ["action"]
    validated_methods: list[str] = ["action"]

    def validate_action(self, method_memo: _CallMemo) -> None:
        """Validate that the data to be processed is in the correct format.

        Args:
            method_memo (_CallMemo): The `_CallMemo` which holds the method's typing information and arguments

        Raises:
            TypeError: Raised if the data is not the correct type
            ValueError: Raised if the types are correct, but there is an issue in the formatting
        """
        for number in method_memo.arguments["number_list"]:
            if not isinstance(number, int):
                raise TypeError(f"{number} is not an integer")
```

Most of the time, an abstract base class will work. But, if you want the runtime validation then this library might be useful.

## Documentation

Documentation for validating-base can be found within the docs folder.
