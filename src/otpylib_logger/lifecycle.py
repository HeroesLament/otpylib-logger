#!/usr/bin/env python3
"""
Logger Lifecycle Management

Supervisor that manages the LoggerManager GenServer and Handler processes.
"""

import importlib

from otpylib import supervisor
from otpylib.supervisor import PERMANENT, ONE_FOR_ONE
from otpylib.module import OTPModule, SUPERVISOR

from otpylib_logger.atoms import LOGGER, LOGGER_SUP
from otpylib_logger.data import LoggerSpec
from otpylib_logger.boundaries import LoggerManager


# =============================================================================
# Logger Supervisor Module
# =============================================================================

class LoggerSupervisor(metaclass=OTPModule, behavior=SUPERVISOR, version="1.0.0"):
    """
    Logger Supervisor.
    
    Manages LoggerManager GenServer and all handler processes.
    """
    
    async def init(self, logger_spec: LoggerSpec):
        """Initialize the logger supervision tree."""
        children = [
            supervisor.child_spec(
                id="logger_manager",
                module=LoggerManager,
                args=logger_spec,
                restart=PERMANENT,
                name=LOGGER
            ),
        ]
        
        # Add handlers - dynamically import their OTPModule classes
        for handler_spec in logger_spec.handlers:
            handler_class = _get_handler_class(handler_spec.handler_module)
            
            # Merge handler level into config
            handler_config = {
                **handler_spec.config,
                "level": handler_spec.level,
            }
            
            children.append(
                supervisor.child_spec(
                    id=f"handler_{handler_spec.name}",
                    module=handler_class,
                    args=handler_config,
                    restart=PERMANENT,
                    # No name - handlers register themselves with LOGGER in init()
                )
            )
        
        opts = supervisor.options(strategy=ONE_FOR_ONE)
        return (children, opts)
    
    async def terminate(self, reason, state):
        """Cleanup on termination."""
        pass


# =============================================================================
# Helper Functions
# =============================================================================

def _get_handler_class(handler_module_path: str) -> type:
    """
    Import and return the handler OTPModule class.
    
    Convention: Handler modules export their class with standard naming.
    - "otpylib_logger.handlers.console" -> ConsoleHandler
    - "otpylib_logger.handlers.file" -> FileHandler
    - "otpylib_logger.handlers.journal" -> JournalHandler
    
    Args:
        handler_module_path: Python module path (e.g., "otpylib_logger.handlers.console")
    
    Returns:
        Handler OTPModule class
    
    Raises:
        ValueError: If handler class not found or not an OTPModule
    """
    handler_module = importlib.import_module(handler_module_path)
    
    # Derive class name from module name
    # "console" -> "ConsoleHandler"
    # "file" -> "FileHandler"
    module_name = handler_module_path.split('.')[-1]
    class_name = ''.join(word.capitalize() for word in module_name.split('_')) + 'Handler'
    
    if not hasattr(handler_module, class_name):
        available = [name for name in dir(handler_module) if not name.startswith('_')]
        raise ValueError(
            f"Handler module '{handler_module_path}' must export class '{class_name}'. "
            f"Available attributes: {available}"
        )
    
    handler_class = getattr(handler_module, class_name)
    
    # Verify it's an OTPModule
    from otpylib.module import is_otp_module
    if not is_otp_module(handler_class):
        raise ValueError(
            f"{class_name} in {handler_module_path} is not an OTPModule"
        )
    
    return handler_class


# =============================================================================
# Lifecycle Functions
# =============================================================================

async def start_link(logger_spec: LoggerSpec):
    """
    Start the logger supervision tree.
    
    Args:
        logger_spec: Logger configuration specification
    
    Returns:
        PID of the spawned supervisor
    """
    return await supervisor.start_link(
        LoggerSupervisor,
        init_arg=logger_spec,
        name=LOGGER_SUP
    )
