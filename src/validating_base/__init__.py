""".. include:: ../../README.md"""  # noqa
__version__ = "0.1.0"

import logging

from .base import ValidatingBaseClass

# set up logging for the package
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)

__all__ = ["ValidatingBaseClass"]
