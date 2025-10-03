#!/usr/bin/env python3
"""
Logger Demo Application

Demonstrates otpylib_logger with multiple handlers and supervised workers.
"""

import asyncio

from otpylib import atom, supervisor, process
from otpylib.runtime import set_runtime
from otpylib.runtime.backends.asyncio_backend.backend import AsyncIOBackend
from otpylib.supervisor import PERMANENT, ONE_FOR_ONE

import otpylib_logger as logger
from otpylib_logger import LOGGER_SUP
from otpylib_logger.data import LoggerSpec, HandlerSpec, LogLevel


DEMO_WORKER = atom.ensure("demo_worker")
ROOT_SUPERVISOR = atom.ensure("root_supervisor")


# =============================================================================
# Demo Worker
# =============================================================================

async def worker_main():
    """Demo worker that generates various log messages."""
    print(f"[demo_worker] Started, PID: {process.self()}")
    
    await asyncio.sleep(0.5)  # Let logger initialize
    
    await logger.info("Worker started successfully")
    
    counter = 0
    while True:
        await asyncio.sleep(2.0)
        counter += 1
        
        # Various log levels with metadata
        if counter % 5 == 1:
            await logger.debug("Processing tick", {"counter": counter, "status": "ok"})
        
        if counter % 5 == 2:
            await logger.info("Heartbeat check", {"counter": counter, "memory_mb": 128})
        
        if counter % 5 == 3:
            await logger.warn("High latency detected", {"counter": counter, "latency_ms": 250})
        
        if counter % 5 == 4:
            await logger.error("Connection failed", {"counter": counter, "host": "192.168.1.100"})
        
        if counter == 10:
            await logger.info("Demo complete, continuing to log...")


async def demo_worker():
    """Factory that spawns a demo worker process."""
    return await process.spawn(worker_main, mailbox=True)


# =============================================================================
# Supervisor Setup
# =============================================================================

async def start():
    """Entrypoint into the Demo Root Supervisor."""
    
    # Configure logger with console and file handlers
    logger_spec = LoggerSpec(
        level=LogLevel.DEBUG,
        handlers=[
            HandlerSpec(
                name="console",
                handler_module="otpylib_logger.handlers.console",
                config={
                    "use_stderr": True,
                    "colorize": True,
                },
                level=LogLevel.DEBUG,
            ),
            HandlerSpec(
                name="file",
                handler_module="otpylib_logger.handlers.file",
                config={
                    "path": "/tmp/otpylib_demo.log",
                    "mode": "a",
                },
                level=LogLevel.INFO,
            ),
        ]
    )
    
    children = [
        supervisor.child_spec(
            id=LOGGER_SUP,
            func=logger.start_link,
            args=[logger_spec],
            restart=PERMANENT,
        ),
        supervisor.child_spec(
            id=DEMO_WORKER,
            func=demo_worker,
            restart=PERMANENT
        )
    ]
    
    opts = supervisor.options(strategy=ONE_FOR_ONE)

    await supervisor.start(
        child_specs=children,
        opts=opts,
        name=ROOT_SUPERVISOR,
    )
    
    try:
        while True:
            await process.receive()
    except asyncio.CancelledError:
        pass


async def main():
    """Main demo application."""
    backend = AsyncIOBackend()
    await backend.initialize()
    set_runtime(backend)
    
    await process.spawn(start, mailbox=True)
    
    try:
        while True:
            await asyncio.sleep(1.0)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await backend.shutdown()


if __name__ == "__main__":
    asyncio.run(main())