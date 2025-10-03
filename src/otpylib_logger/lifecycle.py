#!/usr/bin/env python3
"""
Logger Lifecycle Management

Supervisor that manages the LoggerManager GenServer and Handler processes.
"""

import asyncio
import importlib

from otpylib import supervisor, gen_server, process, atom
from otpylib.supervisor import PERMANENT, ONE_FOR_ONE

from otpylib_logger.atoms import LOGGER, LOGGER_SUP
from otpylib_logger.data import LoggerSpec
from otpylib_logger import boundaries


async def start_logger_manager(logger_spec: LoggerSpec):
    """Start the logger manager GenServer."""
    return await gen_server.start(
        boundaries.callbacks,
        logger_spec,
        name=LOGGER
    )


async def logger_supervisor(logger_spec: LoggerSpec):
    """
    Run the logger supervisor process.
    Manages logger manager and handlers under OTP supervision.
    """
    # Import handler modules dynamically
    handlers = []
    for handler_spec in logger_spec.handlers:
        handler_module = importlib.import_module(handler_spec.handler_module)
        handler_start_func = getattr(handler_module, "start_link")
        handlers.append((handler_spec, handler_start_func))
    
    # Build supervision tree
    children = [
        supervisor.child_spec(
            id="logger_manager",
            func=start_logger_manager,
            args=[logger_spec],
            restart=PERMANENT,
        ),
    ]
    
    # Add handlers as supervised children
    for handler_spec, start_func in handlers:
        children.append(
            supervisor.child_spec(
                id=f"handler_{handler_spec.name}",
                func=start_func,
                args=[handler_spec.config],
                restart=PERMANENT,
            )
        )
    
    opts = supervisor.options(strategy=ONE_FOR_ONE)
    await supervisor.start(children, opts, name=LOGGER_SUP)
    
    # Stay alive
    try:
        while True:
            await process.receive()
    except asyncio.CancelledError:
        pass


async def start_link(logger_spec: LoggerSpec):
    """
    Factory that spawns the logger supervisor process.
    Returns the PID of the spawned supervisor.
    """
    return await process.spawn(logger_supervisor, args=[logger_spec], mailbox=True)