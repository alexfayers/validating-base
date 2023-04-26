"""Example usages for the `validating_base.ValidatingBaseClass` class."""

from abc import abstractmethod

import pytest
from typeguard import TypeCheckError
from validating_base import ValidatingBaseClass, validated


class ActionExample(ValidatingBaseClass):
    """Shows an example usage of the `validating_base.ValidatingBaseClass` class.

    Uses the `abstractmethod` for required methods, and the `validated` decorators instead of
        the `validated_methods` class variable.
    """

    def validate_action(self, number_list: list[int]) -> None:
        """Validate that the data to be processed is in the correct format.

        Args:
            number_list (List[int]): The list of ints

        Raises:
            TypeError: Raised if the data is not the correct type
            ValueError: Raised if the types are correct, but there is an issue in the formatting
        """

    @abstractmethod
    @validated
    def action(self, number_list: list[int]) -> int:
        """Take a list of ints and sum all of the elements.

        The validation method in this case is `ActionExample.validate_action`.

        Args:
            number_list (List[int]): The list of ints

        Returns:
            int: The sum of all elements in the list
        """


class AdderExample(ActionExample):
    """A class that adds things."""

    def action(self, number_list: list[int]) -> int:
        """Take a list of ints and sum all of the elements.

        The validation method in this case is `ActionExample.validate_action`.

        Args:
            number_list (List[int]): The list of ints

        Returns:
            int: The sum of all elements in the list
        """
        total = 0
        for number in number_list:
            total = total + number

        return total


class MultiplierExample(ActionExample):
    """A class that multiplies things."""

    def action(self, number_list: list[int]) -> int:
        """Take a list of ints and multiply all of the elements.

        The validation method in this case is `ActionExample.validate_action`.

        Args:
            number_list (List[int]): The list of ints

        Returns:
            int: The multiply of all elements in the list
        """
        total = 1
        for number in number_list:
            total = total * number

        return total


class InvalidExample(ActionExample):
    """A class that doesn't define an action method."""


class MissingValidator(ValidatingBaseClass):
    """Define the action but not the validator."""

    @validated
    def action(self, items: dict[str, str]) -> None:
        """Validated."""


class NonCallableValidator(ValidatingBaseClass):
    """A validator that is not callable."""

    @validated
    def action(self, items: dict[str, str]) -> None:
        """Validated."""

    validate_action: int = 1


class DeprecatedRequired(ValidatingBaseClass):
    """Deprecated usage."""
    required_methods: list[str] = []


class DeprecatedValidated(ValidatingBaseClass):
    """Deprecated usage."""
    validated_methods: list[str] = []


def test_adder() -> None:
    """Tests that the adder class gets validated."""
    adder = AdderExample()

    total = adder.action([1, 2, 3, 4, 5])
    assert total == 15

    with pytest.raises(TypeCheckError, match="is not an instance of int"):
        adder.action(["1", 2, 3, 4, 5])  # type: ignore


def test_multiplier() -> None:
    """Tests that the multiplier class gets validated."""
    multiplier = MultiplierExample()

    total = multiplier.action([1, 2, 3, 4, 5])
    assert total == 120

    with pytest.raises(TypeCheckError, match="is not an instance of int"):
        multiplier.action(["1", 2, 3, 4, 5])  # type: ignore


def test_missing_required() -> None:
    """Tests that a class with a missing requirement raises an error."""
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        InvalidExample()  # type: ignore[abstract]


def test_missing_validator() -> None:
    """Tests that a class with a missing requirement raises an error."""
    with pytest.raises(NotImplementedError, match="The validate_action method must be defined for the action method."):
        MissingValidator()


def test_non_callable_validator() -> None:
    """Tests a validator that is not callable."""
    with pytest.raises(TypeError, match="must be a callable"):
        NonCallableValidator()


def test_deprecated_required() -> None:
    """Tests that deprecated usage results in an error."""
    with pytest.raises(DeprecationWarning):
        DeprecatedRequired()


def test_deprecated_validated() -> None:
    """Tests that deprecated usage results in an error."""
    with pytest.raises(DeprecationWarning):
        DeprecatedValidated()
