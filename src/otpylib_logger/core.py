#!/usr/bin/env python3
"""
Logger Core Business Logic

Pure functions for log routing, filtering, and formatting.
No side effects, no GenServer knowledge, just business logic.
"""

import time
from typing import Dict, Any
from datetime import datetime

from otpylib import process

from otpylib_logger.data import LogLevel, LogEntry


def should_log(message_level: str, handler_level: str) -> bool:
    """
    Determine if a message should be logged based on severity levels.
    
    Args:
        message_level: The level of the incoming log message
        handler_level: The minimum level the handler accepts
    
    Returns:
        True if message should be logged, False otherwise
    
    Example:
        >>> should_log("ERROR", "INFO")
        True
        >>> should_log("DEBUG", "WARN")
        False
    """
    # Convert strings to LogLevel if needed
    if isinstance(message_level, str):
        message_level = LogLevel[message_level]
    if isinstance(handler_level, str):
        handler_level = LogLevel[handler_level]
    
    # Compare enum values directly
    return message_level.value >= handler_level.value


def format_log_entry(level: str, message: str, metadata: Dict[str, Any]) -> LogEntry:
    """
    Format a log message into a structured LogEntry.
    
    Args:
        level: Log level (DEBUG, INFO, WARN, ERROR)
        message: The log message
        metadata: Additional structured data (pid, module, custom fields)
    
    Returns:
        LogEntry with timestamp and all fields populated
    """
    return LogEntry(
        level=level,
        message=message,
        metadata=metadata,
        timestamp=time.time()
    )


def format_log_line(entry: LogEntry) -> str:
    """
    Format a LogEntry into a human-readable string.
    
    Args:
        entry: The log entry to format
    
    Returns:
        Formatted string suitable for console/file output
    
    Example output:
        2025-10-02 14:23:45 | INFO | my_server | Server started
    """
    # Format timestamp
    dt = datetime.fromtimestamp(entry.timestamp)
    timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
    
    # Extract and resolve pid if present
    pid = entry.metadata.get("pid", "unknown")
    
    # Try to resolve pid to registered name
    if pid != "unknown":
        try:
            name = process.whereis_name(pid)
            if name:
                pid = name  # Use the name instead of raw PID
        except:
            pass  # Keep raw PID if resolution fails
    
    # Build base log line
    log_line = f"{timestamp_str} | {entry.level:<5} | {pid} | {entry.message}"
    
    # Append additional metadata (excluding pid since we already showed it)
    extra_metadata = {k: v for k, v in entry.metadata.items() if k != "pid"}
    if extra_metadata:
        metadata_str = " | ".join(f"{k}={v}" for k, v in extra_metadata.items())
        log_line += f" | {metadata_str}"
    
    return log_line