"""
Main entry point for the TermSage application.

TermSage is a command-line interface for interacting with Ollama models,
featuring auto-completion and a rich user experience.
"""

import os
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

# Local imports - use try/except to handle potential circular imports
try:
    from autocomplete import get_style_for_completion, setup_completer
    from ollama import (
        is_ollama_active,
        ollama_start,
        get_ollama_models,
        interactive_chat_session,
        generate_text,
    )
    from config import Config
except ImportError:
    from src.autocomplete import get_style_for_completion, setup_completer
    from src.ollama import (
        is_ollama_active,
        ollama_start,
        get_ollama_models,
        interactive_chat_session,
        generate_text,
    )
    from src.config import Config


class TermSageCLI:
    """Command-line interface for TermSage with auto-completion."""

    def __init__(self):
        """Initialize the TermSage CLI."""
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

        # Load active model configuration
        self.active_model = self.config.get("active_model")
        self.temperature = self.config.get("temperature", 0.7)
        self.system_prompt = self.config.get(
            "system_prompt",
            "You are a helpful AI assistant. Answer the user's questions concisely and accurately.",
        )

        # Command handlers
        self.commands = {
            "help": self.show_help,
            "exit": self.exit_app,
            "quit": self.exit_app,
            "clear": self.clear_screen,
            "list": self.list_models,
            "model": self.set_model,
            "temperature": self.set_temperature,
            "chat": self.start_chat,
            "generate": self.generate_text,
            "settings": self.show_settings_menu,
            "config": self.show_settings_menu,
        }

        # Add settings command to autocomplete
        if "settings" not in self.completer.base_commands:
            self.completer.base_commands["settings"] = "Configure TermSage settings"
        if "config" not in self.completer.base_commands:
            self.completer.base_commands["config"] = "Configure TermSage settings"

    def show_prompt(self):
        """Show the command prompt with current model info."""
        model_info = f"[{self.active_model}]" if self.active_model else ""
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
        if self.active_model is None:
            models = get_ollama_models()
            if models:
                print("No active model selected.")
                self.select_model_menu()

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
                if cmd in self.commands:
                    self.commands[cmd](args)
                else:
                    print(f"Unknown command: {cmd}")
                    print("Type 'help' for available commands.")

            except KeyboardInterrupt:
                # Handle Ctrl+C
                print("\nOperation cancelled.")
            except EOFError:
                # Handle Ctrl+D
                print("\nExiting TermSage.")
                break
            except Exception as e:
                print(f"Error: {str(e)}")

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

    def list_models(self, args):
        """List available Ollama models."""
        models = get_ollama_models()
        if not models:
            print("No models found. Install models with 'ollama pull <model_name>'")
            return

        print(f"Available models ({len(models)}):")
        for i, model in enumerate(models, 1):
            marker = (
                " *" if self.active_model == f"{model['name']}:{model['tag']}" else ""
            )
            print(f"  {i}. {model['name']}:{model['tag']} ({model['size']}){marker}")

    def set_model(self, args):
        """Set the active model."""
        if not args:
            # Interactive model selection
            self.select_model_menu()
            return

        model_name = args[0]
        tag = args[1] if len(args) > 1 else None

        # Validate model exists
        models = get_ollama_models()
        model_exists = False

        for model in models:
            if model["name"] == model_name:
                model_exists = True
                # If no tag specified, use the model's tag
                if not tag:
                    tag = model["tag"]
                break

        if not model_exists:
            print(
                f"Model '{model_name}' not found. Use 'list' to see available models."
            )
            return

        # Set as active model
        self.active_model = f"{model_name}:{tag}"
        print(f"Active model set to {self.active_model}")

        # Save to config
        self.config.set("active_model", self.active_model)
        self.config.save()

    def set_temperature(self, args):
        """Set the temperature for text generation."""
        if not args:
            print(f"Current temperature: {self.temperature}")
            print("Usage: temperature <value> (e.g., 0.1, 0.7, 1.0)")
            return

        try:
            temp = float(args[0])
            if 0.0 <= temp <= 1.0:
                self.temperature = temp
                print(f"Temperature set to {self.temperature}")

                # Save to config
                self.config.set("temperature", self.temperature)
                self.config.save()
            else:
                print("Temperature must be between 0.0 and 1.0")
        except ValueError:
            print("Please provide a valid number between 0.0 and 1.0")

    def start_chat(self, args):
        """Start an interactive chat session."""
        if not self.active_model:
            print("No model selected. Use 'model' to select a model.")
            self.select_model_menu()
            if not self.active_model:
                return

        print(f"Starting chat with {self.active_model}...")
        print("Type 'exit' to end the chat session.")

        interactive_chat_session(self.active_model, system_prompt=self.system_prompt)

    def generate_text(self, args):
        """Generate text from a prompt."""
        if not self.active_model:
            print("No model selected. Use 'model' to select a model.")
            self.select_model_menu()
            if not self.active_model:
                return

        if not args:
            print("Please provide a prompt. Usage: generate <prompt>")
            return

        prompt = " ".join(args)
        print(f"Generating text with {self.active_model}...")

        response = generate_text(
            self.active_model,
            prompt,
            system_prompt=self.system_prompt,
            temperature=self.temperature,
        )

        print("\nGenerated text:")
        print("-" * 40)
        print(response)
        print("-" * 40)

    def select_model_menu(self):
        """Display an interactive menu to select a model."""
        models = get_ollama_models()
        if not models:
            print("No models found. Install models with 'ollama pull <model_name>'")
            return

        # For command-line version (non-interactive)
        print("\nAvailable models:")
        for i, model in enumerate(models, 1):
            marker = (
                " *" if self.active_model == f"{model['name']}:{model['tag']}" else ""
            )
            print(f"  {i}. {model['name']}:{model['tag']} ({model['size']}){marker}")

        # Get user selection
        try:
            selection = int(input("\nEnter model number to select (0 to cancel): "))
            if selection == 0:
                return

            if 1 <= selection <= len(models):
                model = models[selection - 1]
                self.active_model = f"{model['name']}:{model['tag']}"
                print(f"Model set to {self.active_model}")

                # Save to config
                self.config.set("active_model", self.active_model)
                self.config.save()
            else:
                print(f"Please enter a number between 1 and {len(models)}")
        except ValueError:
            print("Please enter a valid number")

    def show_settings_menu(self, args):
        """Show the settings menu."""
        print("\nSettings:")
        print(f"  1. Active Model: {self.active_model or 'None'}")
        print(f"  2. Temperature: {self.temperature}")
        print(f"  3. System Prompt: {self.system_prompt[:50]}...")
        print(f"  4. Auto-start Ollama: {self.config.get('auto_start_ollama', True)}")
        print("  0. Back to main menu")

        try:
            choice = int(input("\nEnter your choice (0-4): "))

            if choice == 0:
                return
            elif choice == 1:
                self.select_model_menu()
            elif choice == 2:
                self.set_temperature_interactive()
            elif choice == 3:
                self.set_system_prompt_interactive()
            elif choice == 4:
                self.toggle_auto_start()
            else:
                print("Invalid choice")
        except ValueError:
            print("Please enter a valid number")

    def set_temperature_interactive(self):
        """Set temperature interactively."""
        current = self.temperature
        print(f"Current temperature: {current}")
        print("Temperature controls randomness in responses (0.0-1.0)")
        print("Lower values: more focused, deterministic responses")
        print("Higher values: more creative, varied responses")

        try:
            temp_str = input(
                "Enter new temperature (0.0-1.0, leave blank to keep current): "
            )
            if not temp_str:
                return

            temp = float(temp_str)
            if 0.0 <= temp <= 1.0:
                self.temperature = temp
                self.config.set("temperature", temp)
                self.config.save()
                print(f"Temperature set to {temp}")
            else:
                print("Temperature must be between 0.0 and 1.0")
        except ValueError:
            print("Please enter a valid number")

    def set_system_prompt_interactive(self):
        """Set system prompt interactively."""
        current = self.system_prompt
        print(f"Current system prompt: {current}")
        print("The system prompt helps define the AI's behavior.")

        new_prompt = input("Enter new system prompt (leave blank to keep current): ")
        if not new_prompt:
            return

        self.system_prompt = new_prompt
        self.config.set("system_prompt", new_prompt)
        self.config.save()
        print("System prompt updated")

    def toggle_auto_start(self):
        """Toggle auto-start Ollama setting."""
        current = self.config.get("auto_start_ollama", True)
        new_value = not current
        self.config.set("auto_start_ollama", new_value)
        self.config.save()
        print(f"Auto-start Ollama {'enabled' if new_value else 'disabled'}")


def main():
    """Main entry point for TermSage."""
    cli = TermSageCLI()
    cli.run()


if __name__ == "__main__":
    main()
