"""
Configuration management for TermSage.

This module handles loading, saving, and managing application settings in a thread-safe manner.
"""

import os
import json
import threading
from typing import Dict, Any, Optional, Union, List

# Define default configuration with type hints for better documentation
DEFAULT_CONFIG: Dict[str, Any] = {
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
    "ai_suggestions_enabled": True,
    "suggestion_system_prompt": (
        "You are a helpful command line assistant. "
        "Suggest complete shell commands based on partial input or descriptions."
    ),
    "logging": {
        "level": "INFO",
        "file_enabled": True,
        "console_enabled": True,
    },
}


class ConfigError(Exception):
    """Base exception for configuration errors."""
    pass


class ConfigLoadError(ConfigError):
    """Exception raised when configuration loading fails."""
    pass


class ConfigSaveError(ConfigError):
    """Exception raised when configuration saving fails."""
    pass


class ConfigManager:
    """Thread-safe configuration manager for TermSage."""

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration manager.

        Args:
            config_dir: Optional path to the configuration directory.
                        If None, uses ~/.termsage
        
        Raises:
            ConfigError: If the configuration directory cannot be created
        """
        # Use user's home directory if no config_dir provided
        if config_dir is None:
            config_dir = os.path.expanduser("~/.termsage")

        # Create config directory if it doesn't exist
        try:
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
        except OSError as e:
            raise ConfigError(f"Failed to create config directory: {e}")

        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "config.json")
        
        # Thread safety
        self._lock = threading.RLock()  # Reentrant lock for nested method calls
        
        # Initialize with default config
        self._settings = DEFAULT_CONFIG.copy()

        # Load saved config if it exists
        try:
            self.load()
        except ConfigLoadError as e:
            # Log the error but continue with defaults
            print(f"Warning: {e}. Using default configuration.")

    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file in a thread-safe manner.

        Returns:
            Dict of configuration settings
        
        Raises:
            ConfigLoadError: If the configuration file exists but cannot be loaded
        """
        with self._lock:
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, "r") as f:
                        saved_config = json.load(f)

                    # Update settings with saved config, keeping default values
                    # for any missing keys
                    self._update_nested_dict(self._settings, saved_config)
                except json.JSONDecodeError as e:
                    raise ConfigLoadError(f"Invalid JSON in config file: {e}")
                except IOError as e:
                    raise ConfigLoadError(f"Could not read config file: {e}")

            return self._settings.copy()  # Return a copy to prevent direct modification

    def save(self) -> None:
        """
        Save configuration to file in a thread-safe manner.

        Raises:
            ConfigSaveError: If the configuration cannot be saved
        """
        with self._lock:
            try:
                with open(self.config_file, "w") as f:
                    json.dump(self._settings, f, indent=2)
            except IOError as e:
                raise ConfigSaveError(f"Could not write config file: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value in a thread-safe manner.

        Args:
            key: Configuration key to retrieve (supports dot notation for nested keys)
            default: Default value if key doesn't exist

        Returns:
            Configuration value or default
        """
        with self._lock:
            # Support for nested keys with dot notation (e.g., "theme.prompt")
            if "." in key:
                parts = key.split(".")
                value = self._settings
                for part in parts:
                    if not isinstance(value, dict) or part not in value:
                        return default
                    value = value[part]
                return value

            return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value in a thread-safe manner.

        Args:
            key: Configuration key to set (supports dot notation for nested keys)
            value: Value to set
        """
        with self._lock:
            # Support for nested keys with dot notation
            if "." in key:
                parts = key.split(".")
                config = self._settings
                for part in parts[:-1]:
                    if part not in config:
                        config[part] = {}
                    elif not isinstance(config[part], dict):
                        # If the existing value is not a dict, convert it
                        config[part] = {}
                    config = config[part]
                config[parts[-1]] = value
            else:
                self._settings[key] = value

    def get_all(self) -> Dict[str, Any]:
        """
        Get a copy of all configuration settings.

        Returns:
            Copy of configuration dictionary
        """
        with self._lock:
            return self._settings.copy()

    def reset(self) -> None:
        """Reset all settings to default values."""
        with self._lock:
            self._settings = DEFAULT_CONFIG.copy()

    def reset_key(self, key: str) -> None:
        """
        Reset a specific key to its default value.

        Args:
            key: Configuration key to reset (supports dot notation)
        """
        with self._lock:
            if "." in key:
                parts = key.split(".")
                
                # Check if the key exists in default config
                default_value = DEFAULT_CONFIG
                for part in parts:
                    if not isinstance(default_value, dict) or part not in default_value:
                        return  # Key not in defaults, nothing to reset
                    default_value = default_value[part]
                
                # Set the value back to default
                self.set(key, default_value)
            elif key in DEFAULT_CONFIG:
                self._settings[key] = DEFAULT_CONFIG[key]

    def _update_nested_dict(self, original: Dict[str, Any], update: Dict[str, Any]) -> None:
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