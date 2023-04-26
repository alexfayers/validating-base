"""The main functionality of `validating-base`."""
from __future__ import annotations

import inspect
import sys
from abc import ABCMeta
from functools import wraps
from typing import Any, Callable, Concatenate, ParamSpec, TypeVar
from warnings import warn

from typeguard import TypeCheckMemo
from typeguard._functions import check_argument_types, check_return_type

C = TypeVar("C")
P = ParamSpec("P")
R = TypeVar("R")


def validated_decorated(validation_method: Callable[P, None]) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Validate the decorated method with the supplied validation method.

    The validation method must be a method that accepts the same parameters as the decorated method.

    The validation method should return None, and raise an exception if there's any validation errors.

    Args:
        validation_method (Callable[P, None]): The method to call to validated the decorated method.
    """

    def outer(function: Callable[P, R]) -> Callable[P, R]:
        @wraps(function)
        def inner(*args: P.args, **kwargs: P.kwargs) -> R:
            # Get the decorated function's name
            function_name = function.__name__

            # This is bascially getting the arguments and typehints for the function.
            signature = inspect.signature(function)

            # This is like matching up the values in args and kwargs to the signature we just got.
            bound_args = signature.bind(*args, **kwargs).arguments

            # This lets us see all of the variables that are accessible in this function.
            frame = sys._getframe(0)

            # TypeCheckMemo is just typeguard's storage for info about an object.
            memo = TypeCheckMemo(frame.f_globals, frame.f_locals, self_type=type(function))

            # Convert the signature parameters into the format that typeguard expects
            # (dict[str, tuple[Any, Any]]): dict[`argument_name`, tuple[`argument_value`, `argument_expected_type`]]
            formatted_args = {}

            for (expected_name, expected_type), actual_value in zip(signature.parameters.items(), bound_args.values()):
                formatted_args[expected_name] = (actual_value, expected_type.annotation)

            # Use typeguard to check the types, and then run the validation method if it exists.
            check_argument_types(function_name, formatted_args, memo)
            validation_method(*args, **kwargs)

            # run the function, and then check that the return type is valid
            res = function(*args, **kwargs)
            check_return_type(function_name, res, signature.return_annotation, memo)

            return res

        return inner

    return outer


def validated(function: Callable[P, R]) -> Callable[P, R]:
    """Enable runtime validation for a method."""
    function.__isruntimevalidated__ = True  # type: ignore[attr-defined]
    return function


class ValidatingBaseClassMeta(ABCMeta):
    """Metaclass to create a class which automatically validates itself.

    All of the methods in the `validated_methods` attribute will be validated using the `typeguard` library.

    This metaclass is used by the `ValidatingBaseClass` class.
    """

    def __new__(cls, name: str, bases: tuple[type, ...], attrs: dict[str, Any], /, **kwargs: Any) -> type:
        """Create a new class.

        Args:
            name (str): The name of the class
            bases (tuple[type, ...]): The base classes
            attrs (dict[str, Any]): The attributes of the class
            **kwargs (Any): Arbitrary keyword argmuents.

        Returns:
            type: The new class
        """
        required_methods = attrs.get("required_methods", [])
        required_methods_changed = False
        validated_methods = attrs.get("validated_methods", [])
        validated_methods_changed = False

        # handle decorated functions
        for attr_name, attr_value in attrs.items():
            if getattr(attr_value, "__isruntimevalidated__", False):
                if attr_name not in validated_methods:
                    validated_methods.append(attr_name)
                    validated_methods_changed = True
            if getattr(attr_value, "__isabstractmethod__", False):
                if attr_name not in required_methods:
                    required_methods.append(attr_name)
                    required_methods_changed = True

        if validated_methods_changed:
            attrs["validated_methods"] = validated_methods

        if required_methods_changed:
            attrs["required_methods"] = required_methods

        # handle non-decorator methods
        # adds __isabstractmethod__ = True to all required methods
        # so that ABC can handle the required-ness
        for required_method_name in required_methods:
            required_method = attrs.get(required_method_name)

            if callable(required_method):
                required_method.__isabstractmethod__ = True
                attrs[required_method_name] = required_method

        if "_self_validated" not in attrs:
            attrs["_self_validated"] = False

        new_class = super().__new__(cls, name, bases, attrs, **kwargs)

        new_class_init = getattr(new_class, "__init__")

        def validate_init(
            function: Callable[Concatenate[ValidatingBaseClass, P], R]
        ) -> Callable[Concatenate[ValidatingBaseClass, P], R]:
            @wraps(function)
            def inner(self: ValidatingBaseClass, *args: P.args, **kwargs: P.kwargs) -> R:
                if not self._self_validated:
                    self._validate_self()
                return function(self, *args, **kwargs)

            return inner

        setattr(new_class, "__init__", validate_init(new_class_init))

        return new_class


class ValidatingBaseClass(metaclass=ValidatingBaseClassMeta):
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
    All `validate_XXX` methods should accept the same arguments as the method that they are validating, and return None.
        They should raise an error if the arguments are not valid.
    """

    _self_validated: bool = False
    """Internal flag to indicate whether the class itself has been validated."""

    def _validate_self(self) -> None:
        """Validate that the class has the specified methods defined.

        Reads the required method from the `ValidatingBaseClass.required_methods` attribute.

        Raises:
            NotImplementedError: Raised if a required method is not defined.
        """
        for required_method_name in self.required_methods:
            method = getattr(self, required_method_name, None)
            if not callable(method):
                raise TypeError(f"The {required_method_name} attribute must be a callable.")

        for validated_method_name in self.validated_methods:
            validated_method = getattr(self, validated_method_name, None)
            if validated_method is None:
                # this method isn't implemented, so we don't need to validate it
                warn(
                    f"The {validated_method_name} method is not implemented, but is "
                    "specified in the validated_methods attribute. It will not be validated."
                )
                # remove the method from the validated methods list
                self.validated_methods.remove(validated_method_name)
                continue

            if not callable(validated_method):
                raise TypeError(f"The {validated_method_name} attribute must be a callable.")

            # check that the validate method exists for this method

            validator_name = f"validate_{validated_method_name}"
            validator_method = getattr(self, validator_name, None)

            if validator_method is None:
                raise NotImplementedError(
                    f"The {validator_name} method must be defined for the {validated_method_name} method."
                )

            if not callable(validator_method):
                raise TypeError(f"The {validator_name} attribute must be a callable.")

        self._self_validated = True

    def __getattribute__(self, __name: str) -> Any:
        """Get an attribute from the class, and decorate any validated methods with their validation methods.."""
        method = super().__getattribute__(__name)

        if __name in ["_self_validated", "validated_methods"]:
            return method

        if callable(method) and self._self_validated and __name in self.validated_methods:
            validator_name = f"validate_{__name}"
            validator = super().__getattribute__(validator_name)
            return validated_decorated(validator)(method)
        else:
            return method
