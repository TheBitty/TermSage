"""
Configuration management for TermSage.

This module handles loading, saving, and managing application settings.
"""

import os
import json
from typing import Dict, Any, Optional


# Define default configuration
DEFAULT_CONFIG = {
    "active_model": None,
    "temperature": 0.7,
    "system_prompt": (
        "You are a helpful AI assistant. "
        "Answer the user's questions concisely and accurately."
    ),
    "theme": {
        "prompt": "ansigreen bold",
        "model_info": "ansiyellow",
        "chat_prompt": "ansimagenta bold",
        "error": "ansired",
    },
    "history_limit": 100,
    "auto_start_ollama": True,
}


class Config:
    """Configuration manager for TermSage."""

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration manager.

        Args:
            config_dir: Optional path to the configuration directory
        """
        # Use user's home directory if no config_dir provided
        if config_dir is None:
            config_dir = os.path.expanduser("~/.termsage")

        # Create config directory if it doesn't exist
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "config.json")

        # Initialize with default config
        self.settings = DEFAULT_CONFIG.copy()

        # Load saved config if it exists
        self.load()

    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file.

        Returns:
            Dict of configuration settings
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    saved_config = json.load(f)

                # Update settings with saved config, keeping default values
                # for any missing keys
                self._update_nested_dict(self.settings, saved_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config: {e}")

        return self.settings

    def save(self) -> bool:
        """
        Save configuration to file.

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.settings, f, indent=2)
            return True
        except IOError as e:
            print(f"Error saving config: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key to retrieve
            default: Default value if key doesn't exist

        Returns:
            Configuration value or default
        """
        # Support for nested keys with dot notation (e.g., "theme.prompt")
        if "." in key:
            parts = key.split(".")
            value = self.settings
            for part in parts:
                if part not in value:
                    return default
                value = value[part]
            return value

        return self.settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key to set
            value: Value to set
        """
        # Support for nested keys with dot notation
        if "." in key:
            parts = key.split(".")
            config = self.settings
            for part in parts[:-1]:
                if part not in config:
                    config[part] = {}
                config = config[part]
            config[parts[-1]] = value
        else:
            self.settings[key] = value

    def _update_nested_dict(self, original: Dict, update: Dict) -> None:
        """
        Update a nested dictionary without overwriting unspecified nested values.

        Args:
            original: Original dictionary to update
            update: Dictionary with new values
        """
        for key, value in update.items():
            if (
                key in original
                and isinstance(original[key], dict)
                and isinstance(value, dict)
            ):
                self._update_nested_dict(original[key], value)
            else:
                original[key] = value
