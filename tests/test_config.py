"""
Tests for the config module.
"""

import unittest
import os
import tempfile
import shutil
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from src.config import Config, DEFAULT_CONFIG

    MODULE_PATH = "src.config"
except ImportError:
    try:
        from config import Config, DEFAULT_CONFIG

        MODULE_PATH = "config"
    except ImportError:
        from unittest.case import SkipTest

        raise SkipTest("Could not import config module")


class TestConfig(unittest.TestCase):
    """Test cases for the Config class."""

    def setUp(self):
        """Set up the test environment with a temporary config directory."""
        # Create temporary directory for test config
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "config.json")

        # Create configuration with the temporary directory
        self.config = Config(self.temp_dir)

    def tearDown(self):
        """Clean up the test environment."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)

    def test_init_creates_directory(self):
        """Test that initialization creates the config directory."""
        # Remove directory to test creation
        shutil.rmtree(self.temp_dir)

        # Initialize config again
        Config(self.temp_dir)

        # Check directory was created
        self.assertTrue(os.path.isdir(self.temp_dir))

    def test_default_config(self):
        """Test that configuration starts with default values."""
        # Check all default values
        for key, value in DEFAULT_CONFIG.items():
            self.assertEqual(self.config.get(key), value)

    def test_save_and_load(self):
        """Test saving and loading configuration."""
        # Change a setting
        self.config.set("temperature", 0.5)

        # Save configuration
        self.config.save()

        # Check file exists
        self.assertTrue(os.path.isfile(self.config_file))

        # Create new config object to load the saved settings
        new_config = Config(self.temp_dir)

        # Check the value was loaded
        self.assertEqual(new_config.get("temperature"), 0.5)

    def test_get_with_default(self):
        """Test getting a value with a default."""
        # Get a non-existent key with a default value
        value = self.config.get("non_existent_key", "default_value")
        self.assertEqual(value, "default_value")

    def test_nested_get(self):
        """Test getting a nested value using dot notation."""
        # Get a nested value
        value = self.config.get("theme.prompt")
        self.assertEqual(value, DEFAULT_CONFIG["theme"]["prompt"])

    def test_nested_set(self):
        """Test setting a nested value using dot notation."""
        # Set a nested value
        self.config.set("theme.prompt", "new_prompt_value")

        # Check the value was set
        self.assertEqual(self.config.get("theme.prompt"), "new_prompt_value")

    def test_load_invalid_json(self):
        """Test loading invalid JSON returns default config."""
        # Write invalid JSON to config file
        with open(self.config_file, "w") as f:
            f.write("invalid JSON")

        # Load should not raise exception
        self.config.load()

        # Should still have default values
        self.assertEqual(self.config.get("temperature"), DEFAULT_CONFIG["temperature"])

    def test_update_nested_dict(self):
        """Test update_nested_dict correctly updates nested dictionaries."""
        # Original nested dictionary
        original = {"a": 1, "b": {"c": 2, "d": 3}}

        # Update with new nested dictionary
        update = {"b": {"c": 4, "e": 5}}

        # Update the dictionary
        self.config._update_nested_dict(original, update)

        # Check the update was correctly applied
        self.assertEqual(original, {"a": 1, "b": {"c": 4, "d": 3, "e": 5}})


if __name__ == "__main__":
    unittest.main()
