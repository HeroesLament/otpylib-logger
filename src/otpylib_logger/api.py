from otpylib import process
from otpylib_logger.atoms import LOGGER

async def info(message, metadata=None):
    """Send info log message to LOGGER process."""
    caller_pid = process.self()
    metadata = metadata or {}
    metadata["pid"] = caller_pid
    await process.send(LOGGER, ("log", "INFO", message, metadata))

async def debug(message, metadata=None):
    """Send debug log message to LOGGER process."""
    caller_pid = process.self()
    metadata = metadata or {}
    metadata["pid"] = caller_pid
    await process.send(LOGGER, ("log", "DEBUG", message, metadata))

async def error(message, metadata=None):
    """Send error log message to LOGGER process."""
    caller_pid = process.self()
    metadata = metadata or {}
    metadata["pid"] = caller_pid
    await process.send(LOGGER, ("log", "ERROR", message, metadata))

async def warn(message, metadata=None):
    """Send warn log message to LOGGER process."""
    caller_pid = process.self()
    metadata = metadata or {}
    metadata["pid"] = caller_pid
    await process.send(LOGGER, ("log", "WARN", message, metadata))