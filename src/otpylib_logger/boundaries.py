#!/usr/bin/env python3
"""
Logger Manager GenServer

Routes log messages to registered handlers with runtime-configurable level.
"""

from typing import Any
from otpylib import atom, gen_server, process
from otpylib.gen_server import CallbackNS

from otpylib_logger.data import LoggerSpec
from otpylib_logger.atoms import (
    LOG, ADD, LEVEL
)
from otpylib_logger import core


# =============================================================================
# GenServer Callbacks
# =============================================================================

callbacks = CallbackNS("LoggerManager")

async def init(logger_spec: LoggerSpec):
    """Initialize the logger manager."""
    state = {
        "level": logger_spec.level,
        "handlers": [],
    }
    return state


async def handle_info(message, state):
    """Handle log messages and control commands."""
    match message:
        case (msg_type, handler_pid) if msg_type == ADD:
            if handler_pid not in state["handlers"]:
                state["handlers"].append(handler_pid)
            return (gen_server.NoReply(), state)

        case (LOG, level, msg, metadata):
            if not core.should_log(level, state["level"]):
                return (gen_server.NoReply(), state)

            entry = core.format_log_entry(level, msg, metadata)
            for handler_pid in list(state["handlers"]):
                await process.send(handler_pid, ("write", entry))

            return (gen_server.NoReply(), state)

        case (LEVEL, new_level):
            state["level"] = new_level
            return (gen_server.NoReply(), state)

        case _:
            return (gen_server.NoReply(), state)


async def terminate(reason, state):
    """Cleanup on termination."""
    return None


# Wire up callbacks
callbacks.init = init
callbacks.handle_info = handle_info
callbacks.terminate = terminate
