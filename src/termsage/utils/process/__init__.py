"""
Process management utilities for TermSage.

This package provides utilities for secure process execution and management.
"""

from .process_manager import (
    ProcessError,
    is_process_running,
    run_command,
    start_background_process,
    wait_for_process_condition
)

__all__ = [
    'ProcessError',
    'is_process_running',
    'run_command',
    'start_background_process',
    'wait_for_process_condition'
] 