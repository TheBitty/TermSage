"""
TermSage CLI core module.

This module contains the main CLI logic for the TermSage application.
"""

import os
import importlib
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

# Import core modules
try:
    from autocomplete import get_style_for_completion, setup_completer
    from ollama import is_ollama_active, ollama_start, get_ollama_models
    from config import Config
except ImportError:
    from src.autocomplete import get_style_for_completion, setup_completer
    from src.ollama import is_ollama_active, ollama_start, get_ollama_models
    from src.config import Config


class TermSageCLI:
    """Command-line interface for TermSage with auto-completion."""

    def __init__(self):
        """Initialize the TermSage CLI."""
        # Dynamic imports to avoid circular dependencies
        # We import these at runtime to avoid circular imports
        try:
            models_module = importlib.import_module('models')
            settings_module = importlib.import_module('settings')
            commands_module = importlib.import_module('commands')
        except ImportError:
            try:
                models_module = importlib.import_module('src.models')
                settings_module = importlib.import_module('src.settings')
                commands_module = importlib.import_module('src.commands')
            except ImportError:
                raise ImportError("Could not import required modules")

        # Load configuration
        self.config = Config()

        # Create history file in config directory
        history_file = os.path.join(self.config.config_dir, "history")
        self.history = FileHistory(history_file)

        # Set up auto-completion
        self.completer = setup_completer(get_ollama_models)

        # Configure prompt style using theme from config
        self.style = Style.from_dict(
            {
                "prompt": self.config.get("theme.prompt", "ansigreen bold"),
                **get_style_for_completion(),
            }
        )

        # Create prompt session
        self.session = PromptSession(
            completer=self.completer,
            history=self.history,
            auto_suggest=AutoSuggestFromHistory(),
            style=self.style,
            complete_in_thread=True,
        )

        # Initialize managers using dynamic imports
        ModelManager = getattr(models_module, 'ModelManager')
        SettingsManager = getattr(settings_module, 'SettingsManager')
        CommandHandler = getattr(commands_module, 'CommandHandler')
        
        # Create instances
        self.model_manager = ModelManager(self.config)
        self.settings_manager = SettingsManager(self.config, self.model_manager)
        self.command_handler = CommandHandler(
            self.config, 
            self.model_manager,
            self.settings_manager,
            self.completer
        )

    def show_prompt(self):
        """Show the command prompt with current model info."""
        model_info = f"[{self.model_manager.active_model}]" if self.model_manager.active_model else ""
        prompt_html = HTML(
            f"<ansigreen>TermSage</ansigreen> "
            f"<ansiyellow>{model_info}</ansiyellow> <ansicyan>></ansicyan> "
        )
        return prompt_html

    def run(self):
        """Run the main CLI loop."""
        print("Welcome to TermSage!")
        print("Type 'help' for available commands.")

        # Check if Ollama is running
        if not is_ollama_active():
            print("Ollama service is not running.")
            auto_start = self.config.get("auto_start_ollama", True)

            if auto_start:
                print("Auto-starting Ollama (configure this in settings)...")
                if not ollama_start():
                    print(
                        "Failed to start Ollama. Please start it manually and try again."
                    )
                    return
            else:
                should_start = input("Would you like to start Ollama? (y/n): ").lower()
                if should_start == "y":
                    if not ollama_start():
                        print(
                            "Failed to start Ollama. Please start it manually and try again."
                        )
                        return
                else:
                    print(
                        "Ollama service is required. Please start it manually and try again."
                    )
                    return

        # If no active model is set but models exist, prompt to select one
        if self.model_manager.active_model is None:
            models = get_ollama_models()
            if models:
                print("No active model selected.")
                self.model_manager.select_model_menu()

        # Main command loop
        while True:
            try:
                # Get command with auto-completion
                command = self.session.prompt(self.show_prompt())

                # Process the command
                if not command.strip():
                    continue

                # Record the command for auto-completion ranking
                self.completer.record_command(command)

                # Parse the command
                parts = command.strip().split()
                cmd = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []

                # Execute the command
                self.command_handler.execute_command(cmd, args)

            except KeyboardInterrupt:
                # Handle Ctrl+C
                print("\nOperation cancelled.")
            except EOFError:
                # Handle Ctrl+D
                print("\nExiting TermSage.")
                break
            except Exception as e:
                print(f"Error: {str(e)}") 