"""
Process management utilities for TermSage.

This module provides secure process execution and management functions.
"""

import os
import sys
import signal
import platform
import subprocess
import shlex
from typing import List, Dict, Any, Optional, Tuple, Union, Callable
import time

from ..log import get_logger

logger = get_logger()


class ProcessError(Exception):
    """Base exception for process-related errors."""
    pass


def is_process_running(process_name: str) -> bool:
    """
    Check if a process is running by name, in a platform-independent way.
    
    Args:
        process_name: Name of the process to check
        
    Returns:
        True if process is running, False otherwise
    """
    try:
        system = platform.system()
        
        if system == "Windows":
            # Windows approach using tasklist
            proc = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {process_name}.exe", "/NH"],
                capture_output=True,
                text=True,
                check=False
            )
            return process_name.lower() in proc.stdout.lower()
            
        elif system == "Darwin":  # macOS
            # Use pgrep on macOS
            proc = subprocess.run(
                ["pgrep", process_name],
                capture_output=True,
                check=False
            )
            return proc.returncode == 0
            
        else:  # Linux and other Unix-like systems
            # Use pgrep on Linux
            proc = subprocess.run(
                ["pgrep", process_name],
                capture_output=True,
                check=False
            )
            return proc.returncode == 0
            
    except Exception as e:
        logger.warning(f"Error checking if process '{process_name}' is running: {e}")
        return False


def run_command(
    cmd: Union[str, List[str]],
    timeout: Optional[int] = None,
    shell: bool = False,
    env: Optional[Dict[str, str]] = None,
    cwd: Optional[str] = None,
    check: bool = False,
) -> Tuple[int, str, str]:
    """
    Run a command securely and return its output.
    
    Args:
        cmd: Command to run (string or list of arguments)
        timeout: Maximum time to wait for command completion (None for no timeout)
        shell: Whether to use shell execution (avoid when possible)
        env: Environment variables for the subprocess
        cwd: Working directory for the subprocess
        check: Whether to raise an exception on non-zero return code
        
    Returns:
        Tuple of (return_code, stdout, stderr)
        
    Raises:
        ProcessError: If check is True and the command fails
    """
    # Ensure cmd is a list of strings if not using shell
    if not shell and isinstance(cmd, str):
        cmd = shlex.split(cmd)
    
    try:
        # Create environment with system environment as base
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
            
        logger.debug(f"Running command: {cmd}")
        
        # Run the command with appropriate options
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=shell,
            env=process_env,
            cwd=cwd,
            timeout=timeout,
            check=False  # We'll handle this ourselves
        )
        
        stdout = proc.stdout.strip() if proc.stdout else ""
        stderr = proc.stderr.strip() if proc.stderr else ""
        
        if check and proc.returncode != 0:
            error_msg = f"Command failed with code {proc.returncode}: {cmd}"
            if stderr:
                error_msg += f"\nError: {stderr}"
            raise ProcessError(error_msg)
            
        return proc.returncode, stdout, stderr
        
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout} seconds: {cmd}")
        return 124, "", f"Command timed out after {timeout} seconds"
        
    except subprocess.SubprocessError as e:
        logger.error(f"Subprocess error: {e}")
        return 1, "", str(e)
        
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return 1, "", str(e)


def start_background_process(
    cmd: Union[str, List[str]],
    shell: bool = False,
    env: Optional[Dict[str, str]] = None,
    cwd: Optional[str] = None,
) -> Optional[subprocess.Popen]:
    """
    Start a background process.
    
    Args:
        cmd: Command to run (string or list of arguments)
        shell: Whether to use shell execution
        env: Environment variables for the subprocess
        cwd: Working directory for the subprocess
        
    Returns:
        Popen object for the process, or None if failed
    """
    # Ensure cmd is a list of strings if not using shell
    if not shell and isinstance(cmd, str):
        cmd = shlex.split(cmd)
        
    try:
        # Create environment with system environment as base
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
            
        logger.debug(f"Starting background process: {cmd}")
        
        # Platform-specific setup for detached processes
        if platform.system() == "Windows":
            # Windows needs special flags for detached processes
            # DETACHED_PROCESS (0x00000008) | CREATE_NO_WINDOW (0x08000000)
            DETACHED_PROCESS_FLAGS = 0x08000008
            
            # Start the process
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=shell,
                env=process_env,
                cwd=cwd,
                # Windows-specific flags
                creationflags=DETACHED_PROCESS_FLAGS
            )
        else:
            # Unix-like systems (Linux, macOS)
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=shell,
                env=process_env,
                cwd=cwd,
                start_new_session=True  # Equivalent to setsid on Unix
            )
        
        return proc
        
    except Exception as e:
        logger.error(f"Error starting background process: {e}")
        return None
        

def wait_for_process_condition(
    condition_func: Callable[[], bool],
    timeout: int = 10, 
    interval: float = 0.5
) -> bool:
    """
    Wait for a condition to be true, with timeout.
    
    Args:
        condition_func: Function that returns True when condition is met
        timeout: Maximum time to wait in seconds
        interval: Time between checks
        
    Returns:
        True if condition was met within timeout, False otherwise
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)
    return False 