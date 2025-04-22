"""
Configuration management for TermSage.
"""

from .config_manager import (
    ConfigManager,
    ConfigError,
    ConfigLoadError,
    ConfigSaveError,
    DEFAULT_CONFIG
)

__all__ = [
    'ConfigManager',
    'ConfigError',
    'ConfigLoadError',
    'ConfigSaveError',
    'DEFAULT_CONFIG'
] 