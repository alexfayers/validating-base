""".. include:: ../../README.md"""  # noqa
__version__ = "2.0.3"

from .base import ValidatingBaseClass
from .decorators import validated

__all__ = ["ValidatingBaseClass", "validated"]
