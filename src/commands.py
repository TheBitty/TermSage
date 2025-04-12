"""
Command handling module for TermSage CLI.

This module contains command handler classes for executing CLI commands.
"""

import os
import sys

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
        }

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
            print(f"Unknown command: {cmd}")
            print("Type 'help' for available commands.")

    def show_help(self, args):
        """Show help information for commands."""
        print("Available commands:")
        for cmd, description in sorted(self.completer.base_commands.items()):
            print(f"  {cmd:<12} - {description}")

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