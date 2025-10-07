#!/usr/bin/env python3
"""
Logger Demo Application

Demonstrates otpylib_logger with multiple handlers and supervised workers.
Uses the new 0.5.0 OTPModule supervisor pattern.
"""

import asyncio

from otpylib import atom, supervisor, process
from otpylib.runtime import set_runtime
from otpylib.runtime.backends.asyncio_backend.backend import AsyncIOBackend
from otpylib.supervisor import PERMANENT, ONE_FOR_ONE
from otpylib.module import OTPModule, GEN_SERVER, SUPERVISOR
from otpylib.gen_server.data import NoReply, Stop

import otpylib_logger as logger
from otpylib_logger.lifecycle import LoggerSupervisor  # ← Import the supervisor class
from otpylib_logger import LOGGER_SUP
from otpylib_logger.data import LoggerSpec, HandlerSpec, LogLevel


DEMO_WORKER = atom.ensure("demo_worker")
ROOT_SUPERVISOR = atom.ensure("root_supervisor")


# =============================================================================
# Demo Worker GenServer
# =============================================================================

class DemoWorker(metaclass=OTPModule, behavior=GEN_SERVER, version="1.0.0"):
    """
    Demo worker GenServer that generates various log messages.
    
    Demonstrates different log levels and metadata usage.
    """
    
    async def init(self, args):
        """Initialize worker and schedule first tick."""
        await logger.info("Worker started successfully")
        
        # Schedule first tick to self
        my_pid = process.self()
        await process.send_after(2.0, my_pid, "tick")
        
        return {"counter": 0}
    
    async def handle_call(self, message, _caller, state):
        """Handle synchronous calls."""
        return (NoReply(), state)
    
    async def handle_cast(self, message, state):
        """Handle asynchronous casts."""
        match message:
            case "stop":
                return (Stop(), state)
            case _:
                return (NoReply(), state)
    
    async def handle_info(self, message, state):
        """Handle info messages (tick events)."""
        match message:
            case "tick":
                counter = state["counter"] + 1
                
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
                
                # Schedule next tick
                my_pid = process.self()
                await process.send_after(2.0, my_pid, "tick")
                
                return (NoReply(), {"counter": counter})
            
            case _:
                return (NoReply(), state)
    
    async def terminate(self, reason, state):
        """Cleanup on termination."""
        await logger.info(f"Worker terminating after {state['counter']} ticks")


# =============================================================================
# Root Supervisor
# =============================================================================

class RootSupervisor(metaclass=OTPModule, behavior=SUPERVISOR, version="1.0.0"):
    """
    Root supervisor for the logger demo.
    
    Manages the logger subsystem and demo worker.
    """
    
    async def init(self, logger_spec: LoggerSpec):
        """Initialize the demo supervision tree."""
        children = [
            supervisor.child_spec(
                id=LOGGER_SUP,
                module=LoggerSupervisor,
                args=logger_spec,
                restart=PERMANENT,
                name=LOGGER_SUP
            ),
            supervisor.child_spec(
                id=DEMO_WORKER,
                module=DemoWorker,
                args=None,
                restart=PERMANENT,
                name=DEMO_WORKER
            )
        ]
        
        opts = supervisor.options(
            strategy=ONE_FOR_ONE,
            max_restarts=5,
            max_seconds=60
        )
        
        return (children, opts)
    
    async def terminate(self, reason, state):
        """Cleanup on shutdown."""
        pass


# =============================================================================
# Demo Application
# =============================================================================

async def run_demo():
    """Run the logger demo."""
    
    print("=" * 70)
    print("Starting Logger Demo")
    print("=" * 70)
    
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
    
    # Start root supervisor - it will start everything else
    print("\n[1] Starting supervision tree...")
    root_pid = await supervisor.start_link(
        RootSupervisor,
        init_arg=logger_spec,
        name=ROOT_SUPERVISOR
    )
    print(f"    ✓ Root supervisor started: {root_pid}")
    
    print("\n[2] Demo worker is logging in background...")
    print("    Check /tmp/otpylib_demo.log for file output")
    print("    Press Ctrl+C to stop")
    
    # Keep demo alive
    await asyncio.sleep(30)
    
    print("\n" + "=" * 70)
    print("Demo Summary")
    print("=" * 70)
    print("\nSuccessfully demonstrated:")
    print("  ✓ Logger with multiple handlers (console + file)")
    print("  ✓ Different log levels (DEBUG, INFO, WARN, ERROR)")
    print("  ✓ Structured logging with metadata")
    print("  ✓ GenServer self-scheduling with send_after()")
    print("  ✓ Supervised worker with automatic restart")
    print()


# =============================================================================
# Main Entry Point
# =============================================================================

async def main():
    """Main entry point - initialize backend and run demo."""
    
    backend = AsyncIOBackend()
    await backend.initialize()
    set_runtime(backend)
    
    async def demo_process():
        try:
            await run_demo()
        except Exception as e:
            print(f"\n✗ Demo failed: {e}")
            import traceback
            traceback.print_exc()
    
    await process.spawn(demo_process, mailbox=True)
    
    # Keep running for demo duration
    await asyncio.sleep(35)
    await backend.shutdown()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("OTPylib Logger Demo")
    print("=" * 70)
    asyncio.run(main())
