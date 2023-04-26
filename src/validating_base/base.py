"""The main functionality of `validating-base`."""
from __future__ import annotations

from abc import ABCMeta
from typing import TYPE_CHECKING, Any

from validating_base.decorators_internal import prerun_validated, type_validated, validate_init

if TYPE_CHECKING:
    from .types import C


def ensure_required_attributes(cls: C) -> C:
    """Ensure that the class has the attributes that we're expecting."""
    if not hasattr(cls, "_self_validated"):
        cls._self_validated = False  # type: ignore[attr-defined]

    return cls


def update_init(cls: C) -> C:
    """Install the validate_init decorator on `__init__`."""
    cls.__init__ = validate_init(cls.__init__)  # type: ignore[misc]
    return cls


def update_validated_methods(cls: C) -> C:
    """Update the `__prerun_validated_methods__` and `__type_validated_methods__` attributes."""
    prerun_validated_methods = set()
    type_validated_methods = set()

    # Check the existing validated methods of the parents and add them to the validated methods
    for scls in cls.__bases__:  # type: ignore[attr-defined]
        for name in getattr(scls, "__prerun_validated_methods__", ()):
            prerun_validated_methods.add(name)

        for name in getattr(scls, "__type_validated_methods__", ()):
            type_validated_methods.add(name)

    # Also add any other newly added validated methods.
    for name, value in cls.__dict__.items():
        if getattr(value, "__is_runtime_prerun_validated__", False):
            prerun_validated_methods.add(name)

        if getattr(value, "__is_runtime_type_validated__", False):
            type_validated_methods.add(name)

    cls.__prerun_validated_methods__ = frozenset(prerun_validated_methods)  # type: ignore[attr-defined]
    cls.__type_validated_methods__ = frozenset(type_validated_methods)  # type: ignore[attr-defined]
    return cls


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
        new_class = super().__new__(cls, name, bases, attrs, **kwargs)

        new_class = ensure_required_attributes(new_class)
        new_class = update_init(new_class)
        new_class = update_validated_methods(new_class)

        return new_class


class ValidatingBaseClass(metaclass=ValidatingBaseClassMeta):
    """A class which automatically validates itself.

    The inputs and outputs of specified methods are validated through the use of the `validated` decorator.

    A TypeError is raised if the input arguments to a validated method are not of the correct type.
    A TypeError is raised if return value to a validated method is not of the correct type.

    Example usage can be seen in `validating_base.examples`.
    """

    _self_validated: bool
    """Internal flag to indicate whether the class itself has been validated."""

    def _validate_self(self) -> None:
        """Validate that the class has the specified methods defined.

        Raises:
            NotImplementedError: Raised if a method is not defined.
        """
        if getattr(self, "validated_methods", None) is not None:
            raise DeprecationWarning(
                "The validated_methods attribute is deprecated. Use the `validating_base.validated` decorator instead."
            )

        if getattr(self, "required_methods", None) is not None:
            raise DeprecationWarning(
                "The required_methods attribute is deprecated. Use the `abc.abstractmethod` decorator instead."
            )

        for validated_method_name in self.__prerun_validated_methods__:
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

        if __name in ["_self_validated", "__prerun_validated_methods__", "__type_validated_methods__"]:
            return method

        if callable(method) and self._self_validated:
            if __name in self.__prerun_validated_methods__:
                validator_name = f"validate_{__name}"
                validator = super().__getattribute__(validator_name)
                method = prerun_validated(validator)(method)

            if __name in self.__type_validated_methods__:
                method = type_validated(method)

        return method
