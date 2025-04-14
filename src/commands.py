"""
Command handling module for TermSage CLI.

This module contains command handler classes for executing CLI commands.
"""

import os
import sys
import subprocess
import shlex
import re
import threading
import select
import signal
import time
import errno

try:
    from ollama import interactive_chat_session, generate_text
except ImportError:
    from src.ollama import interactive_chat_session, generate_text


# Define helper functions for Windows input handling
# This approach helps avoid linter errors while maintaining functionality
def is_key_pressed(msvcrt_module):
    """
    Check if a key was pressed using msvcrt module.
    
    Args:
        msvcrt_module: The msvcrt module
        
    Returns:
        bool: True if a key was pressed, False otherwise
    """
    if not msvcrt_module:
        return False
    try:
        return msvcrt_module.kbhit() if hasattr(msvcrt_module, 'kbhit') else False
    except Exception:
        return False


def get_pressed_key(msvcrt_module):
    """
    Get the pressed key using msvcrt module.
    
    Args:
        msvcrt_module: The msvcrt module
        
    Returns:
        str: The pressed key or empty string on error
    """
    if not msvcrt_module:
        return ''
    try:
        if hasattr(msvcrt_module, 'getch'):
            char = msvcrt_module.getch()
            # Decode the byte to string, handling any errors
            if isinstance(char, bytes):
                return char.decode('utf-8', errors='replace')
            return char
    except Exception:
        pass
    return ''


class CommandHandler:
    """Handler for TermSage CLI commands."""

    def __init__(self, config, model_manager, settings_manager, completer):
        """
        Initialize the command handler.

        Args:
            config: Configuration manager
            model_manager: Model manager instance
            settings_manager: Settings manager instance
            completer: Command completer instance
        """
        self.config = config
        self.model_manager = model_manager
        self.settings_manager = settings_manager
        self.completer = completer
        self.current_dir = os.getcwd()
        self.current_process = None
        self.process_running = False

        # Command handlers mapped to methods
        self.commands = {
            "help": self.show_help,
            "exit": self.exit_app,
            "quit": self.exit_app,
            "clear": self.clear_screen,
            "list": self.model_manager.list_models,
            "model": self.model_manager.set_model,
            "temperature": self.model_manager.set_temperature,
            "chat": self.start_chat,
            "generate": self.generate_text,
            "settings": self.settings_manager.show_settings_menu,
            "config": self.settings_manager.show_settings_menu,
            "cd": self.change_directory,
            "pwd": self.print_working_directory,
        }

        # Internal commands that shouldn't be executed as system commands
        self.internal_commands = set(self.commands.keys())
        
        # Set up signal handler for Ctrl+C
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful termination."""
        # Store original SIGINT handler
        self.original_sigint = signal.getsignal(signal.SIGINT)
        
        # Set new SIGINT handler to terminate child processes
        signal.signal(signal.SIGINT, self._handle_interrupt)

    def _handle_interrupt(self, sig, frame):
        """Handle interrupt signal (Ctrl+C)."""
        if self.process_running and self.current_process:
            print("\nTerminating process...")
            try:
                self.current_process.terminate()
            except Exception:
                pass  # Ignore errors when terminating process
            self.process_running = False
        else:
            # Restore original handler and re-raise the signal
            signal.signal(signal.SIGINT, self.original_sigint)
            if callable(self.original_sigint):
                self.original_sigint(sig, frame)

    def execute_command(self, cmd, args):
        """
        Execute a command with the given arguments.

        Args:
            cmd: Command name
            args: Command arguments
        """
        # Handle empty command
        if not cmd:
            return
            
        if cmd in self.commands:
            self.commands[cmd](args)
        else:
            # If not an internal command, try to execute as a system command
            success = self.execute_system_command(cmd, args)
            if not success:
                print(f"Unknown command: {cmd}")
                print("Type 'help' for available commands.")

    def execute_system_command(self, cmd, args):
        """
        Execute a system command using subprocess with real-time output.

        Args:
            cmd: Command name
            args: Command arguments

        Returns:
            bool: True if command execution was attempted, False if command not found
        """
        # Skip execution if this is an internal command (should be handled separately)
        if cmd in self.internal_commands:
            return False

        try:
            # Check if command contains shell metacharacters (pipes, redirects, etc.)
            full_cmd_str = cmd + " " + " ".join(args)
            has_shell_metacharacters = re.search(r'[|><&;]', full_cmd_str) is not None
            
            # Prepare environment with current directory
            env = os.environ.copy()
            
            # Create the process with appropriate settings
            if has_shell_metacharacters:
                # For complex commands with shell metacharacters
                self.current_process = subprocess.Popen(
                    full_cmd_str,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=True,
                    bufsize=1,  # Line buffered
                    cwd=self.current_dir,
                    env=env
                )
            else:
                # For simple commands, use the safer list form
                full_cmd = [cmd] + args
                self.current_process = subprocess.Popen(
                    full_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=True,
                    bufsize=1,  # Line buffered
                    cwd=self.current_dir,
                    env=env
                )
            
            # Mark process as running
            self.process_running = True
            
            # Handle process I/O based on platform
            try:
                if os.name == 'nt':  # Windows doesn't support select on pipes
                    self._handle_process_windows()
                else:  # Unix-like systems
                    self._handle_process_unix()
            except Exception as e:
                print(f"Error handling process I/O: {e}")
            
            # Process completed
            self.process_running = False
            self.current_process = None
            
            return True
            
        except FileNotFoundError:
            # Command not found
            print(f"Command not found: {cmd}")
            self.process_running = False
            self.current_process = None
            return True
        except Exception as e:
            # Other execution errors
            print(f"Error executing command: {e}")
            self.process_running = False
            self.current_process = None
            return True

    def _read_stdout_safely(self, stdout):
        """
        Safely read from stdout pipe.
        
        Args:
            stdout: A pipe to read from
            
        Returns:
            str: Line read or empty string on error
        """
        if not stdout:
            return ""
            
        try:
            line = stdout.readline()
            return line
        except (OSError, ValueError, AttributeError):
            return ""

    def _read_stderr_safely(self, stderr):
        """
        Safely read from stderr pipe.
        
        Args:
            stderr: A pipe to read from
            
        Returns:
            str: Line read or empty string on error
        """
        if not stderr:
            return ""
            
        try:
            line = stderr.readline()
            return line
        except (OSError, ValueError, AttributeError):
            return ""

    def _handle_process_unix(self):
        """Handle process I/O for Unix-like systems using select."""
        proc = self.current_process
        if not proc:
            return
            
        read_list = []
        if proc.stdout:
            read_list.append(proc.stdout)
        if proc.stderr:
            read_list.append(proc.stderr)
        
        if not read_list:
            # If there are no pipes to read from, just wait for the process
            try:
                proc.wait()
            except Exception:
                pass
            return
            
        # Set stdin to non-blocking mode
        try:
            import fcntl
            orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
            fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)
        except (ImportError, AttributeError):
            orig_fl = None  # Can't set non-blocking mode
        
        try:
            # Process I/O while the process is running
            while proc and proc.poll() is None:
                try:
                    # Check if there's data to read (with timeout to avoid high CPU usage)
                    r, _, _ = select.select(read_list + [sys.stdin], [], [], 0.1)
                    
                    # Handle stdout
                    if proc.stdout in r:
                        line = self._read_stdout_safely(proc.stdout)
                        if line:
                            print(line, end='', flush=True)
                    
                    # Handle stderr
                    if proc.stderr in r:
                        line = self._read_stderr_safely(proc.stderr)
                        if line:
                            print(line, end='', flush=True, file=sys.stderr)
                    
                    # Handle stdin (user input)
                    if sys.stdin in r and proc.stdin:
                        try:
                            input_data = sys.stdin.readline()
                            if input_data and proc and proc.poll() is None:
                                proc.stdin.write(input_data)
                                proc.stdin.flush()
                        except (OSError, IOError, BrokenPipeError):
                            # No input available or pipe closed
                            pass
                except (select.error, OSError) as e:
                    # Handle select errors
                    if hasattr(e, 'args') and e.args and e.args[0] != errno.EINTR:  # Ignore interrupted system call
                        raise
                    # Sleep a bit to avoid tight loop on errors
                    time.sleep(0.1)
            
            # Read any remaining output
            if proc and proc.stdout:
                try:
                    for line in proc.stdout:
                        if line:
                            print(line, end='', flush=True)
                except (OSError, ValueError):
                    pass
                    
            if proc and proc.stderr:
                try:
                    for line in proc.stderr:
                        if line:
                            print(line, end='', flush=True, file=sys.stderr)
                except (OSError, ValueError):
                    pass
                    
        finally:
            # Restore stdin to blocking mode if we changed it
            if orig_fl is not None:
                try:
                    fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl)
                except (OSError, IOError):
                    pass  # Ignore errors when restoring
        
        # Get the return code
        try:
            if proc:
                return_code = proc.wait(timeout=1)
                if return_code != 0:
                    print(f"\nCommand exited with status {return_code}", file=sys.stderr)
        except (subprocess.TimeoutExpired, AttributeError):
            # Process didn't terminate within timeout or proc is None
            print("\nProcess is still running. Terminating...", file=sys.stderr)
            try:
                if proc:
                    proc.terminate()
                    proc.wait(timeout=1)
            except Exception:
                # Force kill if terminate fails
                try:
                    if proc:
                        proc.kill()
                        proc.wait(timeout=1)
                except Exception:
                    print("\nFailed to terminate process", file=sys.stderr)

    def _handle_process_windows(self):
        """Handle process I/O for Windows systems."""
        proc = self.current_process
        if not proc:
            return
            
        # Create threads for reading output
        def read_stdout():
            if not proc or not proc.stdout:
                return
                
            try:
                for line in iter(lambda: self._read_stdout_safely(proc.stdout), ''):
                    if line:
                        print(line, end='', flush=True)
            except (OSError, ValueError, AttributeError):
                pass  # Handle pipe closed errors
        
        def read_stderr():
            if not proc or not proc.stderr:
                return
                
            try:
                for line in iter(lambda: self._read_stderr_safely(proc.stderr), ''):
                    if line:
                        print(line, end='', flush=True, file=sys.stderr)
            except (OSError, ValueError, AttributeError):
                pass  # Handle pipe closed errors
        
        # Set up threads for reading stdout and stderr
        stdout_thread = threading.Thread(target=read_stdout)
        stderr_thread = threading.Thread(target=read_stderr)
        
        stdout_thread.daemon = True
        stderr_thread.daemon = True
        
        stdout_thread.start()
        stderr_thread.start()
        
        # Handle stdin - pass input to process
        has_input_error = False
        
        # Try to import msvcrt for Windows-specific input handling
        msvcrt = None
        try:
            # Dynamic import for msvcrt to avoid import errors on non-Windows platforms
            import msvcrt as _msvcrt
            msvcrt = _msvcrt
        except ImportError:
            has_input_error = True
        
        while proc and proc.poll() is None and not has_input_error:
            try:
                # Check if there's input available on Windows
                if sys.stdin.isatty() and proc.stdin and msvcrt:
                    try:
                        # Use the helper functions to avoid linter errors
                        if is_key_pressed(msvcrt):
                            char = get_pressed_key(msvcrt)
                            if char:
                                if char == '\r':
                                    proc.stdin.write('\n')
                                else:
                                    proc.stdin.write(char)
                                proc.stdin.flush()
                    except Exception:
                        # If any error occurs with input, stop trying
                        has_input_error = True
                
                # Small sleep to reduce CPU usage
                time.sleep(0.05)
            except Exception:
                has_input_error = True
        
        # Wait for threads to complete
        stdout_thread.join(timeout=1)
        stderr_thread.join(timeout=1)
        
        # Get the return code
        try:
            if proc:
                return_code = proc.wait(timeout=1)
                if return_code != 0:
                    print(f"\nCommand exited with status {return_code}", file=sys.stderr)
        except (subprocess.TimeoutExpired, AttributeError):
            # Process didn't terminate within timeout or proc is None
            print("\nProcess is still running. Terminating...", file=sys.stderr)
            try:
                if proc:
                    proc.terminate()
                    proc.wait(timeout=1)
            except Exception:
                # Force kill if terminate fails
                try:
                    if proc:
                        proc.kill()
                except Exception:
                    print("\nFailed to terminate process", file=sys.stderr)

    def change_directory(self, args):
        """
        Change the current working directory.
        
        Args:
            args: Directory to change to
        """
        # Default to home directory if no args
        target_dir = os.path.expanduser("~") if not args else args[0]
        
        try:
            # Expand user directory if ~ is used
            target_dir = os.path.expanduser(target_dir)
            
            # Change to the directory
            os.chdir(target_dir)
            self.current_dir = os.getcwd()
            print(self.current_dir)
        except FileNotFoundError:
            print(f"Directory not found: {target_dir}")
        except PermissionError:
            print(f"Permission denied: {target_dir}")
        except Exception as e:
            print(f"Error changing directory: {e}")

    def print_working_directory(self, args):
        """Print the current working directory."""
        print(self.current_dir)

    def show_help(self, args):
        """Show help information for commands."""
        print("Available commands:")
        print("\nTermSage commands:")
        for cmd, description in sorted(self.completer.base_commands.items()):
            print(f"  {cmd:<12} - {description}")
        
        print("\nBuilt-in shell commands:")
        print("  cd           - Change directory")
        print("  pwd          - Print working directory")
        
        print("\nYou can also run any system command directly (e.g., ls, git, python).")
        print("TermSage supports pipes, redirections, and other shell features.")
        print("Examples:")
        print("  ls -la | grep .py")
        print("  echo 'Hello, world!' > file.txt")
        print("  sudo apt update")
        print("  nmap -sP 192.168.1.0/24")
        
        print("\nKeyboard shortcuts:")
        print("  F1           - Toggle AI suggestions on/off")
        print("  Tab          - Accept AI suggestion (when available)")
        print("  Alt+S        - Request AI suggestion for current input")
        print("  Ctrl+C       - Cancel current command")
        print("  Ctrl+D       - Exit TermSage")

    def exit_app(self, args):
        """Exit the application."""
        print("Exiting TermSage.")
        # Save configuration before exiting
        self.config.save()
        sys.exit(0)

    def clear_screen(self, args):
        """Clear the terminal screen."""
        os.system("cls" if os.name == "nt" else "clear")

    def start_chat(self, args):
        """Start an interactive chat session."""
        if not self.model_manager.active_model:
            print("No model selected. Use 'model' to select a model.")
            self.model_manager.select_model_menu()
            if not self.model_manager.active_model:
                return

        print(f"Starting chat with {self.model_manager.active_model}...")
        print("Type 'exit' to end the chat session.")

        interactive_chat_session(
            self.model_manager.active_model, 
            system_prompt=self.model_manager.system_prompt
        )

    def generate_text(self, args):
        """Generate text from a prompt."""
        if not self.model_manager.active_model:
            print("No model selected. Use 'model' to select a model.")
            self.model_manager.select_model_menu()
            if not self.model_manager.active_model:
                return

        if not args:
            print("Please provide a prompt. Usage: generate <prompt>")
            return

        prompt = " ".join(args)
        print(f"Generating text with {self.model_manager.active_model}...")

        response = generate_text(
            self.model_manager.active_model,
            prompt,
            system_prompt=self.model_manager.system_prompt,
            temperature=self.model_manager.temperature,
        )

        print("\nGenerated text:")
        print("-" * 40)
        print(response)
        print("-" * 40) 