#!/usr/bin/env python3
"""
File Handler

Writes log entries to a file.
"""

from typing import Dict, Any
from pathlib import Path

from otpylib import atom, process
from otpylib.module import OTPModule, GEN_SERVER
from otpylib.gen_server.data import NoReply

from otpylib_logger import core
from otpylib_logger.atoms import ADD, LOGGER


# =============================================================================
# File Handler GenServer Module
# =============================================================================

class FileHandler(metaclass=OTPModule, behavior=GEN_SERVER, version="1.0.0"):
    """
    File Handler GenServer.
    
    Writes log entries to a file with configurable path and mode.
    """
    
    async def init(self, config: Dict[str, Any]):
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
                # Format and write to file
                log_line = core.format_log_line(entry)
                state["file"].write(log_line + "\n")
                state["file"].flush()
                
                return (NoReply(), state)
            
            case _:
                return (NoReply(), state)
    
    async def terminate(self, reason, state):
        """Close file handle on shutdown."""
        if state.get("file"):
            state["file"].close()


# =============================================================================
# Lifecycle Function
# =============================================================================

async def start_link(config: Dict[str, Any]):
    """Start the file handler GenServer."""
    from otpylib import gen_server
    return await gen_server.start_link(
        FileHandler,
        init_arg=config,
        name=atom.ensure("handler_file")
    )
