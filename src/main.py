#!/usr/bin/env python3
"""
TermSage - Main entry point

This module provides the main CLI interface for TermSage.
"""

import os
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML

from src.termsage.core.config.config_manager import ConfigManager as Config
from src.termsage.handlers.commands.commands import CommandStruct

def setup_completer():
    """Set up the autocompleter for the CLI."""
    # Simple placeholder that returns a dummy completer
    class SimpleCompleter:
        def __init__(self):
            self.words = ["exit", "help", "clear", "model", "list", "chat", "generate"]
    
    return SimpleCompleter()

def is_ollama_active():
    """Check if Ollama is running."""
    try:
        import subprocess
        result = subprocess.run(["pgrep", "ollama"], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def get_ollama_models():
    """Get a list of available Ollama models."""
    try:
        import subprocess
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if result.returncode != 0:
            return []
            
        models = []
        lines = result.stdout.strip().split('\n')[1:]  # Skip header line
        for line in lines:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 4:
                models.append({
                    "name": parts[0],
                    "tag": parts[1],
                    "size": parts[3]
                })
        return models
    except Exception:
        return []

class TermSageCLI:
    """Main CLI class for TermSage."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.config = Config()
        self.active_model = self.config.get("active_model")
        self.temperature = self.config.get("temperature", 0.7)
        self.system_prompt = self.config.get("system_prompt", "You are a helpful assistant")
        
        self.session = PromptSession()
        self.completer = setup_completer()
        
        # Set up command handlers
        self.commands = {
            "help": self.show_help,
            "exit": self.exit_app,
            "clear": self.clear_screen,
            "list": self.list_models,
            "model": self.set_model,
            "chat": self.chat_mode,
            "generate": self.generate_text,
            "temp": self.set_temperature,
        }
    
    def show_prompt(self):
        """Display the command prompt."""
        model_display = f"[{self.active_model}]" if self.active_model else ""
        return HTML(f"<ansigreen><b>TermSage</b></ansigreen> {model_display}> ")
    
    def show_help(self, args):
        """Show help information."""
        print("Available commands:")
        print("  help           - Show this help message")
        print("  exit           - Exit the application")
        print("  clear          - Clear the screen")
        print("  list           - List available models")
        print("  model <name>   - Set the active model")
        print("  chat           - Start chat mode")
        print("  generate <text>- Generate text with the active model")
        print("  temp <value>   - Set temperature (0.0-1.0)")
    
    def exit_app(self, args):
        """Exit the application."""
        self.config.save()
        print("Goodbye!")
        sys.exit(0)
    
    def clear_screen(self, args):
        """Clear the terminal screen."""
        os.system("clear" if os.name == "posix" else "cls")
    
    def list_models(self, args):
        """List available models."""
        models = get_ollama_models()
        if not models:
            print("No models found. Install models with 'ollama pull <model_name>'")
            return
            
        print(f"Available models ({len(models)}):")
        for model in models:
            active = "* " if self.active_model == f"{model['name']}:{model['tag']}" else "  "
            print(f"{active}{model['name']}:{model['tag']} ({model['size']})")
    
    def set_model(self, args):
        """Set the active model."""
        if not args:
            print("Please specify a model name (use 'list' to see available models)")
            return
            
        model_name = args[0]
        self.active_model = model_name
        self.config.set("active_model", model_name)
        self.config.save()
        print(f"Active model set to: {model_name}")
    
    def chat_mode(self, args):
        """Start chat mode with the active model."""
        if not self.active_model:
            print("No active model set. Use 'model <name>' to set a model.")
            return
            
        print(f"Chat mode with {self.active_model} (type 'exit' to return to command mode)")
        print(f"System prompt: {self.system_prompt}")
        # In a real implementation, this would start an interactive chat
        print("Chat functionality not implemented in this simplified version.")
    
    def generate_text(self, args):
        """Generate text with the active model."""
        if not self.active_model:
            print("No active model set. Use 'model <name>' to set a model.")
            return
            
        if not args:
            print("Please provide a prompt for text generation")
            return
            
        prompt = " ".join(args)
        print(f"Generating text with {self.active_model} (temp={self.temperature})")
        print(f"Prompt: {prompt}")
        # In a real implementation, this would call the model to generate text
        print("Text generation not implemented in this simplified version.")
    
    def set_temperature(self, args):
        """Set the temperature for text generation."""
        if not args:
            print(f"Current temperature: {self.temperature}")
            return
            
        try:
            temp = float(args[0])
            if 0.0 <= temp <= 1.0:
                self.temperature = temp
                self.config.set("temperature", temp)
                self.config.save()
                print(f"Temperature set to {temp}")
            else:
                print("Temperature must be between 0.0 and 1.0")
        except ValueError:
            print("Invalid temperature value. Please provide a number between 0.0 and 1.0")

def main():
    """Main entry point for TermSage."""
    cli = TermSageCLI()
    
    print("TermSage - AI Command Shell")
    
    if not is_ollama_active():
        print("Warning: Ollama service is not running. Some features may not work.")
    
    cli.show_help([])
    
    while True:
        try:
            user_input = cli.session.prompt(cli.show_prompt())
            parts = user_input.strip().split()
            
            if not parts:
                continue
                
            command = parts[0].lower()
            args = parts[1:]
            
            if command in cli.commands:
                cli.commands[command](args)
            else:
                # Treat as a generate command if no matching command
                cli.generate_text([user_input])
                
        except KeyboardInterrupt:
            print("\nUse 'exit' to quit")
        except EOFError:
            cli.exit_app([])

if __name__ == "__main__":
    main() 