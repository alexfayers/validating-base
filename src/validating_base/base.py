"""The main functionality of `validating-base`."""

import inspect
from functools import wraps
from typing import Any
from warnings import warn

from typeguard import typechecked


class ValidatingBaseClassMeta(type):
    """Metaclass to create a class which automatically validates itself.

    All of the methods in the `validated_methods` attribute will be validated using the `typeguard` library.

    This metaclass is used by the `ValidatingBaseClass` class.
    """

    required_methods: list[str]
    """Methods that must be implemented in any child classes"""
    validated_methods: list[str]
    """Methods that must be validated in any child classes.

    The `validate_XXX` naming scheme should be used when creating a validation function.
    All `validate_XXX` methods should accept a single argument, which is a `_CallMemo` object.
    """

    def __new__(cls, name: str, bases: tuple[type, ...], attrs: dict[str, Any]) -> type:
        """Create a new class.

        Args:
            name (str): The name of the class
            bases (tuple[type, ...]): The base classes
            attrs (dict[str, Any]): The attributes of the class

        Returns:
            type: The new class
        """
        new_class = super().__new__(cls, name, bases, attrs)

        new_class_init = getattr(new_class, "__init__")

        @wraps(new_class_init)
        def _validate_init(self: Any, *args: Any, **kwargs: Any) -> None:
            if not self._self_validated:
                self._validate_self(check_required=True, check_validated=True)

            new_class_init(self, *args, **kwargs)

        setattr(new_class, "__init__", _validate_init)

        # wrap all of the methods that need to be validated with the typechecked decorator
        for method_name in new_class.validated_methods:
            method = getattr(new_class, method_name, None)
            if method is None:
                # this method is not implemented in the child class, so we can't validate it
                # will show a warning when the child class is instantiated without this method
                continue

            if not callable(method):
                # this method is not callable, so we can't validate it
                # will raise an error when the child class is instantiated
                continue

            validate_method = getattr(new_class, f"validate_{method_name}", None)
            if validate_method is None:
                # this method is not implemented in the child class, so we can't use it to validate
                # will raise an error when the child class is instantiated without this method
                continue

            if not callable(validate_method):
                # this method is not callable, so we can't validate it
                # will raise an error when the child class is instantiated
                continue

            @wraps(method)
            def _validated(*args: Any, **kwargs: Any) -> Any:
                """Decorator that runs the specified validator before the decorated method.

                Returns:
                    Any: The return value of the decorated method
                """
                typechecked(validate_method)(*args, **kwargs)
                return typechecked(method)(*args, **kwargs)

            setattr(new_class, method_name, _validated)

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
    All `validate_XXX` methods should accept a single argument, which is a `_CallMemo` object.
    """

    _self_validated: bool = False
    """Internal flag to indicate whether the class itself has been validated."""

    def _validate_self(self, check_required: bool = True, check_validated: bool = True) -> None:
        """Validate that the class has the specified methods defined.

        Reads the required method from the `ValidatingBaseClass.required_methods` attribute.

        Raises:
            NotImplementedError: Raised if a required method is not defined.
        """
        if check_required:
            for required_method_name in self.required_methods:
                method = getattr(self, required_method_name, None)
                if method is None:
                    raise NotImplementedError(f"The {required_method_name} method must be defined.")

                if not callable(method):
                    raise TypeError(f"The {required_method_name} attribute must be a callable.")

        if check_validated:
            for validated_method_name in self.validated_methods:
                print(f"'{validated_method_name}'")
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

                print(validated_method)

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

                # check that the validate method has the same argument signature as the validated method

                validated_method_signature = inspect.signature(validated_method)
                validator_method_signature = inspect.signature(validator_method)

                if validated_method_signature.parameters != validator_method_signature.parameters:
                    raise TypeError(
                        f"The {validator_name} method must have the same argument signature as "
                        f"the {validated_method_name} method."
                    )

                # check that the validate method has a return type of None

                if validator_method_signature.return_annotation is not None:
                    raise TypeError(f"The {validator_name} method must have a return type of None.")

        self._self_validated = True
