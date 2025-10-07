#!/usr/bin/env python3
"""
Logger Manager GenServer

Routes log messages to registered handlers with runtime-configurable level.
"""

from otpylib.module import OTPModule, GEN_SERVER
from otpylib.gen_server.data import NoReply
from otpylib import process

from otpylib_logger.data import LoggerSpec
from otpylib_logger.atoms import LOG, ADD, LEVEL
from otpylib_logger import core


# =============================================================================
# Logger Manager GenServer Module
# =============================================================================

class LoggerManager(metaclass=OTPModule, behavior=GEN_SERVER, version="1.0.0"):
    """
    Logger Manager GenServer.
    
    Routes log messages to registered handlers with runtime-configurable level.
    """
    
    async def init(self, logger_spec: LoggerSpec):
        """Initialize the logger manager."""
        state = {
            "level": logger_spec.level,
            "handlers": [],
        }
        return state
    
    async def handle_call(self, message, _caller, state):
        """Handle synchronous calls (none defined yet)."""
        return (NoReply(), state)
    
    async def handle_cast(self, message, state):
        """Handle asynchronous casts (none defined yet)."""
        return (NoReply(), state)
    
    async def handle_info(self, message, state):
        """Handle log messages and control commands."""
        match message:
            case (msg_type, handler_pid) if msg_type == ADD:
                if handler_pid not in state["handlers"]:
                    state["handlers"].append(handler_pid)
                return (NoReply(), state)

            case (LOG, level, msg, metadata):
                if not core.should_log(level, state["level"]):
                    return (NoReply(), state)

                entry = core.format_log_entry(level, msg, metadata)
                for handler_pid in list(state["handlers"]):
                    await process.send(handler_pid, ("write", entry))

                return (NoReply(), state)

            case (LEVEL, new_level):
                state["level"] = new_level
                return (NoReply(), state)

            case _:
                return (NoReply(), state)
    
    async def terminate(self, reason, state):
        """Cleanup on termination."""
        pass
