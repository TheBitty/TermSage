"""
Auto-completion system for TermSage commands using prompt_toolkit.

This module provides context-aware command auto-completion for the
TermSage command-line interface.
"""

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from typing import List, Dict, Callable, Optional, Iterable
import os
import shutil

# Avoid circular imports
OllamaModelGetterType = Callable[[], List[Dict[str, str]]]


class TermSageCompleter(Completer):
    """
    Context-aware command auto-completer for TermSage.

    This class handles command suggestions based on the input context,
    providing relevant completions for models, commands, and parameters.
    """

    def __init__(self, get_ollama_models_func: Optional[OllamaModelGetterType] = None):
        """
        Initialize the completer with commands and model getter function.

        Args:
            get_ollama_models_func: Function to get available Ollama models
        """
        self.get_ollama_models = get_ollama_models_func

        # Base commands with descriptions
        self.base_commands = {
            "exit": "Exit TermSage",
            "quit": "Exit TermSage",
            "help": "Show available commands and help",
            "list": "List available models",
            "clear": "Clear the screen",
            "model": "Set the model to use",
            "temperature": "Set the temperature for text generation",
            "chat": "Start an interactive chat session",
            "generate": "Generate text from a prompt",
            "history": "Show command history",
            "reset": "Reset the chat history",
            "save": "Save the chat history to a file",
            "load": "Load a model",
            "settings": "Configure TermSage settings",
            "config": "Configure TermSage settings",
        }

        # Common system commands for auto-completion
        self.system_commands = {
            "ls": "List directory contents",
            "cd": "Change directory",
            "pwd": "Print working directory",
            "mkdir": "Make directories",
            "rm": "Remove files or directories",
            "cp": "Copy files or directories",
            "mv": "Move or rename files or directories",
            "cat": "Display file contents",
            "grep": "Search for patterns in files",
            "echo": "Display a line of text",
            "find": "Find files",
            "touch": "Create empty files or update timestamps",
            "chmod": "Change file permissions",
            "chown": "Change file owner and group",
            "ps": "Report process status",
            "kill": "Terminate processes",
            "top": "Display system tasks",
            "git": "Version control system",
            "ssh": "Secure shell client",
            "scp": "Secure copy",
            "tar": "Tape archive utility",
            "unzip": "Extract files from zip archives",
            "curl": "Transfer data from or to a server",
            "wget": "Download files from the web",
            "sudo": "Execute a command as another user",
        }

        # Temperature suggestions
        self.temperature_values = ["0.1", "0.3", "0.5", "0.7", "0.9", "1.0"]

        # Command history for ranking suggestions
        self.command_history = []
        self.max_history = 100

    def record_command(self, command: str) -> None:
        """
        Record a command to improve future suggestions.

        Args:
            command: The command that was used
        """
        if command in self.command_history:
            self.command_history.remove(command)
        self.command_history.insert(0, command)

        # Trim history if needed
        if len(self.command_history) > self.max_history:
            self.command_history = self.command_history[: self.max_history]

    def get_completions(self, document, complete_event) -> Iterable[Completion]:
        """
        Get context-aware completions based on the current input.

        Args:
            document: The document (input text) to complete
            complete_event: Event that triggered the completion

        Returns:
            Iterable of Completion objects
        """
        text = document.text.lstrip()

        # Split the input text to understand context
        words = text.split()
        word_count = len(words)
        word_before_cursor = document.get_word_before_cursor()

        # Handle empty input - suggest base commands
        if not text or not word_count:
            # First suggest TermSage commands
            for cmd, description in sorted(self.base_commands.items()):
                yield Completion(
                    cmd,
                    start_position=-len(word_before_cursor),
                    display=self._format_command_display(cmd, description),
                    style="class:completion",
                )
            
            # Then suggest system commands
            for cmd, description in sorted(self.system_commands.items()):
                if shutil.which(cmd):  # Only suggest commands that exist on the system
                    yield Completion(
                        cmd,
                        start_position=-len(word_before_cursor),
                        display=self._format_system_command_display(cmd, description),
                        style="class:completion.system",
                    )
            return

        # Context: After 'model' command, suggest Ollama models
        if word_count == 1 and words[0] == "model":
            models = self._get_models()
            for model in models:
                model_name = model.get("name", "")
                model_meta = f"Size: {model.get('size', 'Unknown')}"
                yield Completion(
                    model_name,
                    start_position=0,
                    display=self._format_model_display(model_name, model_meta),
                    style="class:completion.model",
                )
            return

        # Context: After model selection, suggest tags
        if word_count == 2 and words[0] == "model":
            models = self._get_models()
            selected_model = words[1]

            for model in models:
                if model.get("name") == selected_model:
                    tag = model.get("tag", "")
                    if tag:
                        yield Completion(
                            tag,
                            start_position=0,
                            display=self._format_tag_display(tag),
                            style="class:completion.tag",
                        )
            return

        # Context: After 'temperature' command, suggest common values
        if word_count == 1 and words[0] == "temperature":
            for temp in self.temperature_values:
                yield Completion(
                    temp,
                    start_position=0,
                    display=HTML(f"<ansiyellow>{temp}</ansiyellow>"),
                    style="class:completion.temperature",
                )
            return

        # Default: Suggest commands that match the prefix
        # First check TermSage commands
        for cmd, description in sorted(self.base_commands.items()):
            if cmd.startswith(word_before_cursor):
                yield Completion(
                    cmd,
                    start_position=-len(word_before_cursor),
                    display=self._format_command_display(cmd, description),
                    style="class:completion",
                )
        
        # Then check system commands
        for cmd, description in sorted(self.system_commands.items()):
            if cmd.startswith(word_before_cursor) and shutil.which(cmd):
                yield Completion(
                    cmd,
                    start_position=-len(word_before_cursor),
                    display=self._format_system_command_display(cmd, description),
                    style="class:completion.system",
                )

    def _get_models(self) -> List[Dict[str, str]]:
        """
        Get available Ollama models.

        Returns:
            List of model dictionaries with name, tag, etc.
        """
        try:
            if self.get_ollama_models:
                return self.get_ollama_models()
        except Exception:
            pass

        # Return empty list if function is not available or fails
        return []

    def _format_command_display(self, cmd: str, description: str) -> HTML:
        """Format a command completion with description."""
        return HTML(f"<ansiblue>{cmd}</ansiblue> - <ansigray>{description}</ansigray>")

    def _format_system_command_display(self, cmd: str, description: str) -> HTML:
        """Format a system command completion with description."""
        return HTML(f"<ansigreen>{cmd}</ansigreen> - <ansigray>{description}</ansigray>")

    def _format_model_display(self, name: str, metadata: str) -> HTML:
        """Format a model completion with metadata."""
        return HTML(f"<ansigreen>{name}</ansigreen> <ansigray>({metadata})</ansigray>")

    def _format_tag_display(self, tag: str) -> HTML:
        """Format a tag completion."""
        return HTML(f"<ansicyan>{tag}</ansicyan>")


def get_style_for_completion():
    """Return style definitions for completions."""
    return {
        "completion": "bg:#008800 #ffffff",
        "completion.system": "bg:#004488 #ffffff",
        "completion.model": "bg:#000088 #ffffff",
        "completion.tag": "bg:#884400 #ffffff",
        "completion.temperature": "bg:#880000 #ffffff",
    }


def setup_completer(get_ollama_models_func=None):
    """
    Set up and return a configured TermSage completer.

    Args:
        get_ollama_models_func: Function to get Ollama models

    Returns:
        Configured TermSageCompleter instance
    """
    return TermSageCompleter(get_ollama_models_func)
