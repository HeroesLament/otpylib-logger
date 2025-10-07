#!/usr/bin/env python3
"""
Console Handler

Writes log entries to stdout/stderr.
"""

import sys
from typing import Dict, Any

from otpylib import atom, process
from otpylib.module import OTPModule, GEN_SERVER
from otpylib.gen_server.data import NoReply

from otpylib_logger import core
from otpylib_logger.atoms import ADD, LOGGER


HANDLER_CONSOLE = atom.ensure("handler_console")


# =============================================================================
# Console Handler GenServer Module
# =============================================================================

class ConsoleHandler(metaclass=OTPModule, behavior=GEN_SERVER, version="1.0.0"):
    """
    Console Handler GenServer.
    
    Writes log entries to stdout/stderr with optional colorization.
    """
    
    async def init(self, config: Dict[str, Any]):
        """Initialize console handler."""
        state = {
            "use_stderr": config.get("use_stderr", True),
            "colorize": config.get("colorize", False),
            "level": config.get("level"),
        }
        
        # Register with logger manager
        my_pid = process.self()
        await process.send(LOGGER, (ADD, my_pid))
        
        return state
    
    async def handle_call(self, message, _caller, state):
        """Handle synchronous calls (none defined)."""
        return (NoReply(), state)
    
    async def handle_cast(self, message, state):
        """Handle asynchronous casts (none defined)."""
        return (NoReply(), state)
    
    async def handle_info(self, message, state):
        """Handle write requests."""
        match message:
            case ("write", entry):            
                # CHECK LEVEL BEFORE WRITING
                if state["level"] and not core.should_log(entry.level, state["level"]):
                    return (NoReply(), state)
                
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
                
                return (NoReply(), state)
            
            case _:
                return (NoReply(), state)
    
    async def terminate(self, reason, state):
        """Cleanup on termination."""
        pass


# =============================================================================
# Helper Functions
# =============================================================================

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


# =============================================================================
# Lifecycle Function
# =============================================================================

async def start_link(config: Dict[str, Any]):
    """Start the console handler GenServer."""
    from otpylib import gen_server
    return await gen_server.start_link(
        ConsoleHandler,
        init_arg=config,
        name=HANDLER_CONSOLE
    )
