#!/usr/bin/env python3
"""
Console Handler

Writes log entries to stdout/stderr.
"""

import sys
import types
from typing import Dict, Any

from otpylib import gen_server, atom, process

from otpylib_logger import core
from otpylib_logger.atoms import LOGGER
from otpylib_logger.data import LogEntry


# =============================================================================
# Console Handler GenServer
# =============================================================================

callbacks = types.SimpleNamespace()


async def init(config: Dict[str, Any]):
    """
    Initialize console handler.
    
    Config options:
        - use_stderr: bool - Write ERROR level to stderr (default: True)
        - colorize: bool - Use ANSI colors (default: False)
    """
    state = {
        "use_stderr": config.get("use_stderr", True),
        "colorize": config.get("colorize", False),
    }
    
    # Register with logger manager
    my_pid = process.self()
    await process.send(LOGGER, ("add_handler", my_pid))
    
    return state


async def handle_info(message, state):
    """Handle write requests."""
    match message:
        case ("write", entry):
            # Format the log entry
            log_line = core.format_log_line(entry)
            
            # Optionally colorize
            if state["colorize"]:
                log_line = _colorize(entry.level, log_line)
            
            # Choose output stream
            if state["use_stderr"] and entry.level == "ERROR":
                print(log_line, file=sys.stderr)
            else:
                print(log_line, file=sys.stdout)
            
            return (gen_server.NoReply(), state)
        
        case _:
            return (gen_server.NoReply(), state)


callbacks.init = init
callbacks.handle_info = handle_info


def _colorize(level: str, text: str) -> str:
    """Add ANSI color codes based on log level."""
    colors = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",   # Green
        "WARN": "\033[33m",   # Yellow
        "ERROR": "\033[31m",  # Red
    }
    reset = "\033[0m"
    
    color = colors.get(level, "")
    return f"{color}{text}{reset}"


async def start_link(config: Dict[str, Any]):
    """Start the console handler GenServer."""
    return await gen_server.start(
        callbacks,
        config,
        name=atom.ensure("handler_console")
    )
