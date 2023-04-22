"""The main functionality of `validating-base`."""

import logging
from typing import Any

from typeguard import (
    _CallMemo,
    check_argument_types,
    check_return_type,
    function_name,
    qualified_name,
)


class ValidatingBaseClass:
    """A class which automatically validates itself.

    The inputs and outputs of specified methods are validated through the use of the `validated_methods` class variable,
    and any methods are are required to be implemented in child classes are defined within the `required_methods`
    class variable.

    A NotImplementedError is raised if a required method is not implemented in a child class.
    A TypeError is raised if the input arguments to a validated method are not of the correct type.
    A TypeError is raised if return value to a validated method is not of the correct type.

    Example usage can be seen in `validating_base.examples`.
    """

    required_methods: list[str] = []
    """Methods that must be implemented in any child classes"""
    validated_methods: list[str] = []
    """Methods that must be validated in any child classes.

    The `validate_XXX` naming scheme should be used when creating a validation function.
    All `validate_XXX` methods should accept a single argument, which is a `_CallMemo` object.
    """

    _self_validated = False
    """Internal flag to indicate whether the class itself has been validated."""

    def __init__(self) -> None:
        """Initialises a `ValidatingBaseClass` instance."""
        self.logger = logging.getLogger(__name__).getChild(self.__class__.__qualname__)

        self._validate_self()

    def _validate_self(self) -> None:
        """Validate that the class has the specified methods defined.

        Reads the required method from the `ValidatingBaseClass.required_methods` attribute.

        Raises:
            NotImplementedError: Raised if a required method is not defined.
        """
        for required_method in self.required_methods:
            method = getattr(self, required_method, None)
            if not callable(method):
                raise NotImplementedError(f"The {required_method} method must be defined.")
        self._self_validated = True
        self.logger.debug(f"Methods of '{qualified_name(self)}' are ok")

    def _validate_argument_types(self, method_memo: _CallMemo) -> None:
        """Validate that the arguments to a method are the correct type.

        Args:
            method_memo (_CallMemo): The `_CallMemo` which holds the method's typing information and arguments

        Raises:
            TypeError: if there is an argument type mismatch
        """
        check_argument_types(method_memo)
        self.logger.debug(f"Argument types for '{method_memo.func_name}' are ok")

    def _validate_return_type(self, method_memo: _CallMemo, result: Any) -> None:
        """Validate that the return value of a method is the correct type.

        Args:
            method_memo (_CallMemo): The `_CallMemo` which holds the method's typing information and arguments
            result (Any): The actual result from the method

        Raises:
            TypeError: if there is a type mismatch in the return value
        """
        check_return_type(result, method_memo)
        self.logger.debug(f"Return type of '{method_memo.func_name}' is ok")

    def __getattribute__(self, __name: str) -> Any:
        """Called when an attribute of the object is attempted to be accessed.

        Ensures that child classes are structured correctly, and that the inputs for the methods specified
        in `ValidatingBaseClass.validated_methods` are validated before a method is executed.

        Args:
            __name (str): The attribute which is being accessed

        Raises:
            NotImplementedError: Raised if a required validation method does not exist

        Returns:
            Any: The value of the attribute
        """
        method = super().__getattribute__(__name)

        skip_methods = {"required_methods", "validated_methods", "_self_validated"}

        if (
            __name not in skip_methods
            and callable(method)
            and self._self_validated
            and __name in self.validated_methods
        ):

            def _validated(*args: Any, **kwargs: Any) -> Any:
                """Decorator that runs the specified validator before the decorated method.

                Returns:
                    Any: The return value of the method
                """
                validator_name = f"validate_{__name}"
                validator = getattr(self, validator_name, None)

                if validator is None:
                    raise NotImplementedError(f"The {__name} method does not have a validator ({validator_name})")

                method_memo = _CallMemo(method, args=args, kwargs=kwargs)

                self._validate_argument_types(method_memo)

                validator(method_memo)

                self.logger.debug(
                    f"Inputs for '{function_name(method)}' are ok (validated using '{function_name(validator)})"
                )

                result = method(*args, **kwargs)

                self._validate_return_type(method_memo, result)

                return result

            return _validated
        else:
            return method
