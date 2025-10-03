"""Log handlers for otpylib_logger."""

from otpylib_logger.handlers.console import start_link as start_console_handler
from otpylib_logger.handlers.file import start_link as start_file_handler

__all__ = [
    "start_console_handler",
    "start_file_handler",
]