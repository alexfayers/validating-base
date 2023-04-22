"""Example usages for the `validating_base.ValidatingBaseClass` class."""


import logging

import pytest
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


def test_adder() -> None:
    """Tests that the adder class gets validated."""
    adder = AdderExample()

    total = adder.action([1, 2, 3, 4, 5])
    assert total == 15

    with pytest.raises(TypeError):
        adder.action(["1", 2, 3, 4, 5])  # type: ignore


def test_multiplier() -> None:
    """Tests that the multiplier class gets validated."""
    multiplier = MultiplierExample()

    total = multiplier.action([1, 2, 3, 4, 5])
    assert total == 120

    with pytest.raises(TypeError):
        multiplier.action(["1", 2, 3, 4, 5])  # type: ignore


def test_invalid() -> None:
    """Tests that the invalid class raises an error."""
    with pytest.raises(NotImplementedError):
        InvalidExample()


def test_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Tests that the logging works."""
    caplog.set_level(logging.DEBUG, logger="validating_base")
    test_adder()

    assert all(log.levelname == "DEBUG" for log in caplog.records)

    expected_logs = [
        "Methods of 'tests.test_base.AdderExample' are ok",
        "Argument types for 'tests.test_base.AdderExample.action' are ok",
        "Inputs for 'tests.test_base.AdderExample.action' are ok (validated using 'tests.test_base.ActionExample.validate_action)",  # noqa
        "Return type of 'tests.test_base.AdderExample.action' is ok",
    ]

    for log_index, expected_log in enumerate(expected_logs):
        assert caplog.records[log_index].msg == expected_log

    assert len(caplog.records) == len(expected_logs)


if __name__ == "__main__":
    logger = logging.getLogger("validating_base")
    logger.setLevel(logging.DEBUG)
    test_adder()
