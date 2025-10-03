#!/usr/bin/env python3
"""
Logger Manager GenServer

The core GenServer that manages log routing and handler coordination.
"""

import types
from typing import Any

from otpylib import gen_server, process

from otpylib_logger.data import LoggerSpec
from otpylib_logger import core


# =============================================================================
# GenServer Callbacks
# =============================================================================

callbacks = types.SimpleNamespace()


async def init(logger_spec: LoggerSpec):
    """Initialize the logger manager."""
    state = {
        "level": logger_spec.level,
        "handlers": [],  # Will be populated with handler PIDs
    }
    
    return state


async def handle_info(message, state):
    """Handle log messages and route to handlers."""
    match message:
        case ("log", level, msg, metadata):
            # Check if we should log at this level
            if not core.should_log(level, state["level"].value):
                return (gen_server.NoReply(), state)
            
            # Format the log entry
            entry = core.format_log_entry(level, msg, metadata)
            
            # Route to all handlers
            for handler_pid in state["handlers"]:
                await process.send(handler_pid, ("write", entry))
            
            return (gen_server.NoReply(), state)
        
        case ("add_handler", handler_pid):
            # Dynamically add a handler
            state["handlers"].append(handler_pid)
            return (gen_server.NoReply(), state)
        
        case ("set_level", new_level):
            # Change log level at runtime
            state["level"] = new_level
            return (gen_server.NoReply(), state)
        
        case _:
            return (gen_server.NoReply(), state)


async def terminate(reason, state):
    """Cleanup on termination."""
    pass


callbacks.init = init
callbacks.handle_info = handle_info
callbacks.terminate = terminate
