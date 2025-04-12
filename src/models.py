"""
Model management module for TermSage.

This module handles Ollama model selection and configuration.
"""

try:
    from ollama import get_ollama_models
except ImportError:
    from src.ollama import get_ollama_models


class ModelManager:
    """Manager for Ollama models in TermSage."""

    def __init__(self, config):
        """
        Initialize the model manager.

        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.active_model = self.config.get("active_model")
        self.temperature = self.config.get("temperature", 0.7)
        self.system_prompt = self.config.get(
            "system_prompt",
            "You are a helpful AI assistant. Answer the user's questions concisely and accurately.",
        )

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