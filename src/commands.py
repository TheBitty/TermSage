"""
Command handling module for TermSage CLI.

This module contains command handler classes for executing CLI commands.
"""

import os
import sys
import subprocess
import shlex
import re

try:
    from ollama import interactive_chat_session, generate_text
except ImportError:
    from src.ollama import interactive_chat_session, generate_text


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

    def execute_command(self, cmd, args):
        """
        Execute a command with the given arguments.

        Args:
            cmd: Command name
            args: Command arguments
        """
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
        Execute a system command using subprocess.

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
            
            if has_shell_metacharacters:
                # Execute with shell=True for commands with pipes, redirects, etc.
                result = subprocess.run(
                    full_cmd_str,
                    shell=True,
                    capture_output=True,
                    text=True,
                    check=False,
                    cwd=self.current_dir
                )
            else:
                # For simple commands, use the safer list form
                full_cmd = [cmd] + args
                
                # Execute the command and capture output
                result = subprocess.run(
                    full_cmd, 
                    capture_output=True, 
                    text=True,
                    check=False,  # Don't raise exception on non-zero exit code
                    cwd=self.current_dir
                )
            
            # Display standard output if any
            if result.stdout:
                print(result.stdout.rstrip())
            
            # Display error output if any
            if result.stderr:
                print(result.stderr.rstrip(), file=sys.stderr)
            
            # Return success based on whether the command was found and executed
            return True
        except FileNotFoundError:
            # Command not found
            print(f"Command not found: {cmd}")
            return True
        except Exception as e:
            # Other execution errors
            print(f"Error executing command: {e}")
            return True

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