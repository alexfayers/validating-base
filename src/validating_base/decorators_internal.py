"""Internal decorators for the package. You shouldn't need to use anything in here directly."""
from __future__ import annotations

import inspect
import sys
from functools import wraps
from typing import TYPE_CHECKING, Callable, Concatenate

from typeguard import TypeCheckMemo
from typeguard._functions import check_argument_types, check_return_type

if TYPE_CHECKING:
    from .base import ValidatingBaseClass
    from .types import P, R


def validate_init(
    function: Callable[Concatenate[ValidatingBaseClass, P], R]
) -> Callable[Concatenate[ValidatingBaseClass, P], R]:
    """Make the decorated function call `_validate_self` before executing."""
    @wraps(function)
    def inner(self: ValidatingBaseClass, *args: P.args, **kwargs: P.kwargs) -> R:
        if not self._self_validated:
            self._validate_self()
        return function(self, *args, **kwargs)

    return inner


def prerun_validated(validation_method: Callable[P, None]) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Validate the decorated method with the supplied validation method.
    
    The validation method must be a method that accepts the same parameters as the decorated method.
    The validation method raise an exception if there's any validation errors.

    Args:
        validation_method (Callable[P, None]): The method to call to validated the decorated method.
    """

    def outer(function: Callable[P, R]) -> Callable[P, R]:
        @wraps(function)
        def inner(*args: P.args, **kwargs: P.kwargs) -> R:
            validation_method(*args, **kwargs)
            return function(*args, **kwargs)
        return inner
    return outer


def type_validated(function: Callable[P, R]) -> Callable[P, R]:
    """Validate the argument and return types of the decorated method.
    
    If used in conjunction with `prerun_validated`, this should be executed 2nd.
    """
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

        # run the function, and then check that the return type is valid
        res = function(*args, **kwargs)
        check_return_type(function_name, res, signature.return_annotation, memo)

        return res

    return inner
