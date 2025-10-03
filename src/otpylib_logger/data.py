#!/usr/bin/env python3
"""
Logger Data Structures

Configuration specs and data types for the logger system.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional


class LogLevel(Enum):
    """Log severity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


@dataclass
class HandlerSpec:
    """
    Specification for a log handler.
    
    Args:
        name: Unique identifier for this handler
        handler_module: Python module path (e.g., "otpylib_logger.handlers.console")
        config: Handler-specific configuration
        level: Minimum log level this handler accepts
    """
    name: str
    handler_module: str
    config: Dict[str, Any] = field(default_factory=dict)
    level: LogLevel = LogLevel.INFO


@dataclass
class LoggerSpec:
    """
    Specification for logger configuration.
    
    Args:
        handlers: List of handler specifications
        level: Global minimum log level
    """
    handlers: List[HandlerSpec]
    level: LogLevel = LogLevel.INFO


@dataclass
class LogEntry:
    """
    Formatted log entry passed to handlers.
    
    Args:
        level: Log level (DEBUG, INFO, WARN, ERROR)
        message: Log message string
        metadata: Additional structured data
        timestamp: Unix timestamp of log event
    """
    level: str
    message: str
    metadata: Dict[str, Any]
    timestamp: float