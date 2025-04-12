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
    from autocomplete import TermSageCompleter, get_style_for_completion, setup_completer
    from ollama import (
        is_ollama_active,
        ollama_start,
        get_ollama_models,
        interactive_chat_session,
        generate_text,
    )
except ImportError:
    from src.autocomplete import TermSageCompleter, get_style_for_completion, setup_completer
    from src.ollama import (
        is_ollama_active,
        ollama_start,
        get_ollama_models,
        interactive_chat_session,
        generate_text,
    )


class TermSageCLI:
    """Command-line interface for TermSage with auto-completion."""
    
    def __init__(self):
        """Initialize the TermSage CLI."""
        # Create history file in user's home directory
        history_file = os.path.expanduser("~/.termsage_history")
        self.history = FileHistory(history_file)
        
        # Set up auto-completion
        self.completer = setup_completer(get_ollama_models)
        
        # Configure prompt style
        self.style = Style.from_dict({
            "prompt": "ansigreen bold",
            **get_style_for_completion()
        })
        
        # Create prompt session
        self.session = PromptSession(
            completer=self.completer,
            history=self.history,
            auto_suggest=AutoSuggestFromHistory(),
            style=self.style,
            complete_in_thread=True
        )
        
        # Active model configuration
        self.active_model = None
        self.temperature = 0.7
        self.system_prompt = (
            "You are a helpful AI assistant. Answer the user's questions "
            "concisely and accurately."
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
        }

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
            should_start = input("Would you like to start Ollama? (y/n): ").lower()
            if should_start == "y":
                if not ollama_start():
                    print("Failed to start Ollama. Please start it manually and try again.")
                    return
            else:
                print("Ollama service is required. Please start it manually and try again.")
                return
        
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
            print(f"  {i}. {model['name']}:{model['tag']} ({model['size']})")
    
    def set_model(self, args):
        """Set the active model."""
        if not args:
            print("Please specify a model. Usage: model <model_name> [tag]")
            return
        
        model_name = args[0]
        tag = args[1] if len(args) > 1 else None
        
        # Validate model exists
        models = get_ollama_models()
        model_exists = False
        
        for model in models:
            if model['name'] == model_name:
                model_exists = True
                # If no tag specified, use the model's tag
                if not tag:
                    tag = model['tag']
                break
        
        if not model_exists:
            print(f"Model '{model_name}' not found. Use 'list' to see available models.")
            return
        
        # Set as active model
        self.active_model = f"{model_name}:{tag}"
        print(f"Active model set to {self.active_model}")
    
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
            else:
                print("Temperature must be between 0.0 and 1.0")
        except ValueError:
            print("Please provide a valid number between 0.0 and 1.0")
    
    def start_chat(self, args):
        """Start an interactive chat session."""
        if not self.active_model:
            print("No model selected. Use 'model <model_name>' to select a model.")
            return
        
        print(f"Starting chat with {self.active_model}...")
        print("Type 'exit' to end the chat session.")
        
        interactive_chat_session(self.active_model, system_prompt=self.system_prompt)
    
    def generate_text(self, args):
        """Generate text from a prompt."""
        if not self.active_model:
            print("No model selected. Use 'model <model_name>' to select a model.")
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
            temperature=self.temperature
        )
        
        print("\nGenerated text:")
        print("-" * 40)
        print(response)
        print("-" * 40)


def main():
    """Main entry point for TermSage."""
    cli = TermSageCLI()
    cli.run()


if __name__ == "__main__":
    main()
