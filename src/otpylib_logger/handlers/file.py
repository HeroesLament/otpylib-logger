#!/usr/bin/env python3
"""
File Handler

Writes log entries to a file.
"""

import types
from typing import Dict, Any
from pathlib import Path

from otpylib import atom, gen_server, process

from otpylib_logger import core
from otpylib_logger.atoms import LOGGER
from otpylib_logger.data import LogEntry


# =============================================================================
# File Handler GenServer
# =============================================================================

callbacks = types.SimpleNamespace()


async def init(config: Dict[str, Any]):
    """
    Initialize file handler.
    
    Config options:
        - path: str - File path to write logs (required)
        - mode: str - File open mode (default: 'a' for append)
    """
    path = config.get("path")
    if not path:
        raise ValueError("File handler requires 'path' in config")
    
    mode = config.get("mode", "a")
    
    # Ensure directory exists
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    
    # Open file handle
    file_handle = open(path, mode, buffering=1)  # Line buffered
    
    state = {
        "path": path,
        "file": file_handle,
    }
    
    # Register with logger manager
    my_pid = process.self()
    await process.send(LOGGER, ("add_handler", my_pid))
    
    return state


async def handle_info(message, state):
    """Handle write requests."""
    match message:
        case ("write", entry):
            # Format and write to file
            log_line = core.format_log_line(entry)
            state["file"].write(log_line + "\n")
            state["file"].flush()
            
            return (gen_server.NoReply(), state)
        
        case _:
            return (gen_server.NoReply(), state)


async def terminate(reason, state):
    """Close file handle on shutdown."""
    if state.get("file"):
        state["file"].close()


callbacks.init = init
callbacks.handle_info = handle_info
callbacks.terminate = terminate


async def start_link(config: Dict[str, Any]):
    """Start the file handler GenServer."""
    return await gen_server.start(
        callbacks,
        config,
        name=atom.ensure("handler_file")
    )
