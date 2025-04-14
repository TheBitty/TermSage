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
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition
from prompt_toolkit.cursor_shapes import CursorShape
import threading

# Import core modules
try:
    from autocomplete import get_style_for_completion, setup_completer
    from ollama import is_ollama_active, ollama_start, get_ollama_models, generate_text
    from config import Config
except ImportError:
    from src.autocomplete import get_style_for_completion, setup_completer
    from src.ollama import is_ollama_active, ollama_start, get_ollama_models, generate_text
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
                "ai_suggestion": "ansigray italic",
                **get_style_for_completion(),
            }
        )

        # Initialize AI suggestion state
        self.ai_suggestion = None
        self.ai_suggestion_lock = threading.Lock()
        self.ai_suggestion_enabled = self.config.get("ai_suggestions_enabled", True)
        self.ai_suggestion_requested = False
        self.ai_suggestion_event = threading.Event()
        self.current_input = ""
        
        # Set up key bindings
        self.key_bindings = self._create_key_bindings()
        
        # Create prompt session
        self.session = PromptSession(
            completer=self.completer,
            history=self.history,
            auto_suggest=AutoSuggestFromHistory(),
            style=self.style,
            complete_in_thread=True,
            key_bindings=self.key_bindings,
            include_default_pygments_style=False,
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
        
        # Start AI suggestion thread if enabled
        if self.ai_suggestion_enabled:
            self._start_ai_suggestion_thread()

    def _create_key_bindings(self):
        """Create custom key bindings for TermSage."""
        bindings = KeyBindings()
        
        # Toggle AI suggestions with F1
        @bindings.add('f1')
        def _(event):
            self.ai_suggestion_enabled = not self.ai_suggestion_enabled
            if self.ai_suggestion_enabled:
                event.app.output.write("\rAI suggestions enabled\n")
                self._start_ai_suggestion_thread()
            else:
                event.app.output.write("\rAI suggestions disabled\n")
            
            # Save the setting
            self.config.set("ai_suggestions_enabled", self.ai_suggestion_enabled)
            self.config.save()
            
            # Redraw the prompt
            event.app.invalidate()
        
        # Tab key to accept AI suggestion
        @bindings.add('tab', filter=Condition(lambda: self.ai_suggestion is not None))
        def _(event):
            if self.ai_suggestion:
                event.current_buffer.text = self.ai_suggestion
                event.current_buffer.cursor_position = len(self.ai_suggestion)
                self.ai_suggestion = None
        
        # Alt+S to request AI suggestion
        @bindings.add('escape', 's')
        def _(event):
            text = event.current_buffer.text
            self.current_input = text
            self.ai_suggestion_requested = True
            self.ai_suggestion_event.set()
            event.app.output.write("\rRequesting AI suggestion...")
            
        return bindings

    def _start_ai_suggestion_thread(self):
        """Start a thread to generate AI suggestions."""
        if not hasattr(self, 'ai_thread') or not self.ai_thread.is_alive():
            self.ai_thread = threading.Thread(target=self._ai_suggestion_worker, daemon=True)
            self.ai_thread.start()

    def _ai_suggestion_worker(self):
        """Worker thread that generates AI command suggestions."""
        while self.ai_suggestion_enabled:
            # Wait for a trigger or timeout
            triggered = self.ai_suggestion_event.wait(timeout=0.5)
            
            # Check if we need to generate a suggestion
            if triggered or (self.current_input and not self.ai_suggestion):
                self.ai_suggestion_event.clear()
                
                # Get current input
                current_text = self.current_input
                
                # Only generate suggestions for meaningful input
                if len(current_text) >= 2:
                    try:
                        suggestion = self._generate_command_suggestion(current_text)
                        
                        # Update suggestion with lock to avoid race conditions
                        with self.ai_suggestion_lock:
                            # Only update if the text hasn't changed
                            if current_text == self.current_input:
                                self.ai_suggestion = suggestion
                    except Exception as e:
                        # Silently fail to not disrupt the user
                        self.ai_suggestion = None
            
            # Reset explicit request flag
            self.ai_suggestion_requested = False

    def _generate_command_suggestion(self, text):
        """
        Generate a command suggestion using Ollama.
        
        Args:
            text: Current input text
            
        Returns:
            str: Suggested command or None
        """
        # Only generate suggestions if we have a model
        if not self.model_manager.active_model:
            return None
            
        # Prepare the prompt for command suggestion
        system_prompt = """You are a helpful command line assistant. 
Give exactly one shell command based on the user's partial input or description.
Respond with just the command, nothing else - no explanation, no markdown.
If you're unsure, respond with an empty message."""
        
        user_prompt = f"""Give a command suggestion that completes or expands: "{text}"
Context: The working directory is {os.getcwd()}.
If this is a valid command already, just repeat it. If it's a natural language request, suggest the appropriate shell command.
Remember, respond with JUST the command, nothing else."""
        
        # Get command suggestion from Ollama
        suggestion = generate_text(
            self.model_manager.active_model,
            user_prompt,
            system_prompt=system_prompt,
            temperature=0.3,  # Lower temperature for more predictable results
        )
        
        # If suggestion same as input, return None
        if suggestion.strip() == text.strip() or not suggestion.strip():
            return None
            
        return suggestion.strip()

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
        
        if self.ai_suggestion_enabled:
            print("AI suggestions are enabled. Press F1 to toggle, Tab to accept a suggestion.")

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
                # Get current AI suggestion
                current_suggestion = None
                if self.ai_suggestion_enabled:
                    with self.ai_suggestion_lock:
                        current_suggestion = self.ai_suggestion
                
                # Custom continuation for AI suggestions
                def get_continuation(width, line_number, wrap_count):
                    if current_suggestion and line_number == 0 and wrap_count == 0:
                        # If suggestion is available, show it greyed out
                        return HTML(f"<class:ai_suggestion> {current_suggestion}</class:ai_suggestion>")
                    return None
                
                # Get command with auto-completion
                command = self.session.prompt(
                    self.show_prompt(),
                    prompt_continuation=get_continuation if self.ai_suggestion_enabled else None,
                    cursor=CursorShape.BEAM,
                )
                
                # Update current input
                self.current_input = command
                with self.ai_suggestion_lock:
                    self.ai_suggestion = None

                # Process the command
                if not command.strip():
                    continue

                # Record the command for auto-completion ranking
                self.completer.record_command(command)

                # Parse the command
                parts = command.strip().split()
                cmd = parts[0].lower() if parts else ""
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