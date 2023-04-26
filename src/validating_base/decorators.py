"""Public decorators."""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .types import P, R


def validate_prerun(function: Callable[P, R]) -> Callable[P, R]:
    """Enable runtime validation for a method by sending arguments to validation method.

    The validation method that will be called is `validate_XXX`, where `XXX` is the name of the decorated function.
    """
    function.__is_runtime_prerun_validated__ = True  # type: ignore[attr-defined]
    return function


def validate_types(function: Callable[P, R]) -> Callable[P, R]:
    """Enable runtime validation for a method's parameter and return types."""
    function.__is_runtime_type_validated__ = True  # type: ignore[attr-defined]
    return function


def validated(function: Callable[P, R]) -> Callable[P, R]:
    """Enable both type and prerun validation for a method."""
    function = validate_types(function)
    function = validate_prerun(function)
    function.__isruntimevalidated__ = True  # type: ignore[attr-defined]  # TODO: remove
    return function



