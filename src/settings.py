"""
Settings management module for TermSage.

This module handles settings configuration and management.
"""


class SettingsManager:
    """Manager for TermSage settings and configuration."""

    def __init__(self, config, model_manager=None):
        """
        Initialize the settings manager.

        Args:
            config: Configuration manager instance
            model_manager: Optional ModelManager instance for model settings
        """
        self.config = config
        self.model_manager = model_manager

    def show_settings_menu(self, args):
        """Show the settings menu."""
        if self.model_manager:
            active_model = self.model_manager.active_model
            temperature = self.model_manager.temperature
            system_prompt = self.model_manager.system_prompt
        else:
            active_model = self.config.get("active_model")
            temperature = self.config.get("temperature", 0.7)
            system_prompt = self.config.get(
                "system_prompt",
                "You are a helpful AI assistant. Answer the user's questions concisely and accurately.",
            )

        print("\nSettings:")
        print(f"  1. Active Model: {active_model or 'None'}")
        print(f"  2. Temperature: {temperature}")
        print(f"  3. System Prompt: {system_prompt[:50]}...")
        print(f"  4. Auto-start Ollama: {self.config.get('auto_start_ollama', True)}")
        print("  0. Back to main menu")

        try:
            choice = int(input("\nEnter your choice (0-4): "))

            if choice == 0:
                return
            elif choice == 1:
                if self.model_manager:
                    self.model_manager.select_model_menu()
                else:
                    print("Model manager not available")
            elif choice == 2:
                if self.model_manager:
                    self.model_manager.set_temperature_interactive()
                else:
                    self.set_temperature_interactive()
            elif choice == 3:
                if self.model_manager:
                    self.model_manager.set_system_prompt_interactive()
                else:
                    self.set_system_prompt_interactive()
            elif choice == 4:
                self.toggle_auto_start()
            else:
                print("Invalid choice")
        except ValueError:
            print("Please enter a valid number")

    def toggle_auto_start(self):
        """Toggle auto-start Ollama setting."""
        current = self.config.get("auto_start_ollama", True)
        new_value = not current
        self.config.set("auto_start_ollama", new_value)
        self.config.save()
        print(f"Auto-start Ollama {'enabled' if new_value else 'disabled'}")

    def set_temperature_interactive(self):
        """Set temperature interactively (when model_manager is not available)."""
        current = self.config.get("temperature", 0.7)
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
                self.config.set("temperature", temp)
                self.config.save()
                print(f"Temperature set to {temp}")
            else:
                print("Temperature must be between 0.0 and 1.0")
        except ValueError:
            print("Please enter a valid number")

    def set_system_prompt_interactive(self):
        """Set system prompt interactively (when model_manager is not available)."""
        current = self.config.get(
            "system_prompt",
            "You are a helpful AI assistant. Answer the user's questions concisely and accurately.",
        )
        print(f"Current system prompt: {current}")
        print("The system prompt helps define the AI's behavior.")

        new_prompt = input("Enter new system prompt (leave blank to keep current): ")
        if not new_prompt:
            return

        self.config.set("system_prompt", new_prompt)
        self.config.save()
        print("System prompt updated") 