"""
Tests for the main CLI module.
"""

import unittest
from unittest.mock import patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from src.main import TermSageCLI, main

    MODULE_PATH = "src.main"
except ImportError:
    try:
        from main import TermSageCLI, main

        MODULE_PATH = "main"
    except ImportError:
        from unittest.case import SkipTest

        raise SkipTest("Could not import main module")


class TestTermSageCLI(unittest.TestCase):
    """Test cases for the TermSageCLI class."""

    @patch(f"{MODULE_PATH}.Config")
    @patch(f"{MODULE_PATH}.PromptSession")
    @patch(f"{MODULE_PATH}.setup_completer")
    def setUp(self, mock_setup_completer, mock_session, mock_config):
        """Set up the test environment."""
        # Set up mocks
        self.mock_config = mock_config.return_value

        # Setup mock config.get to return appropriate values
        def mock_config_get(key, default=None):
            if key == "theme.prompt":
                return "ansigreen bold"
            elif key == "active_model":
                return None
            elif key == "temperature":
                return 0.7
            elif key == "system_prompt":
                return "You are a helpful assistant"
            else:
                return default

        self.mock_config.get.side_effect = mock_config_get

        self.mock_session = mock_session.return_value
        self.mock_completer = mock_setup_completer.return_value

        # Create CLI instance
        self.cli = TermSageCLI()

    def test_init(self):
        """Test initialization of CLI."""
        # Check that config was loaded
        self.assertEqual(self.cli.config, self.mock_config)

        # Check that prompt session was created
        self.assertEqual(self.cli.session, self.mock_session)

        # Check that the command handlers are set up
        self.assertIn("help", self.cli.commands)
        self.assertIn("exit", self.cli.commands)
        self.assertIn("list", self.cli.commands)
        self.assertIn("model", self.cli.commands)
        self.assertIn("chat", self.cli.commands)
        self.assertIn("generate", self.cli.commands)

    @patch(f"{MODULE_PATH}.HTML")
    def test_show_prompt(self, mock_html):
        """Test show_prompt method."""
        # Set active model
        self.cli.active_model = "test-model:latest"

        # Call method
        self.cli.show_prompt()

        # Check HTML was created with correct format
        mock_html.assert_called_once()
        args = mock_html.call_args[0][0]
        self.assertIn("TermSage", args)
        self.assertIn("[test-model:latest]", args)

    @patch(f"{MODULE_PATH}.is_ollama_active")
    @patch("builtins.print")
    def test_show_help(self, mock_print, mock_is_active):
        """Test show_help method."""
        # Call the method
        self.cli.show_help([])

        # Verify print was called with help info
        mock_print.assert_any_call("Available commands:")
        # There should be calls to print - testing exact count is fragile
        self.assertTrue(mock_print.called, "print should be called at least once")

    @patch("builtins.print")
    @patch("sys.exit")
    def test_exit_app(self, mock_exit, mock_print):
        """Test exit_app method."""
        # Call the method
        self.cli.exit_app([])

        # Verify config was saved
        self.mock_config.save.assert_called_once()

        # Verify sys.exit was called
        mock_exit.assert_called_once_with(0)

    @patch("os.system")
    def test_clear_screen_unix(self, mock_system):
        """Test clear_screen method on Unix-like systems."""
        # Mock os.name to be posix
        with patch("os.name", "posix"):
            # Call method
            self.cli.clear_screen([])

            # Verify correct command was called
            mock_system.assert_called_once_with("clear")

    @patch("os.system")
    def test_clear_screen_windows(self, mock_system):
        """Test clear_screen method on Windows."""
        # Mock os.name to be Windows
        with patch("os.name", "nt"):
            # Call method
            self.cli.clear_screen([])

            # Verify correct command was called
            mock_system.assert_called_once_with("cls")

    @patch(f"{MODULE_PATH}.get_ollama_models")
    @patch("builtins.print")
    def test_list_models_with_models(self, mock_print, mock_get_models):
        """Test list_models method when models exist."""
        # Mock models
        mock_get_models.return_value = [
            {"name": "model1", "tag": "latest", "size": "1.1GB"},
            {"name": "model2", "tag": "v2", "size": "2.2GB"},
        ]

        # Set active model
        self.cli.active_model = "model1:latest"

        # Call method
        self.cli.list_models([])

        # Verify print was called with models
        mock_print.assert_any_call("Available models (2):")
        self.assertGreater(mock_print.call_count, 1)

    @patch(f"{MODULE_PATH}.get_ollama_models")
    @patch("builtins.print")
    def test_list_models_no_models(self, mock_print, mock_get_models):
        """Test list_models method when no models exist."""
        # Mock no models
        mock_get_models.return_value = []

        # Call method
        self.cli.list_models([])

        # Verify print was called with no models message
        mock_print.assert_called_with(
            "No models found. Install models with 'ollama pull <model_name>'"
        )

    @patch("builtins.print")
    def test_set_temperature(self, mock_print):
        """Test set_temperature method."""
        # Test with valid temperature
        self.cli.set_temperature(["0.5"])

        # Verify temperature was set
        self.assertEqual(self.cli.temperature, 0.5)

        # Verify config was updated
        self.mock_config.set.assert_called_with("temperature", 0.5)
        self.mock_config.save.assert_called_once()

        # Reset mocks
        mock_print.reset_mock()
        self.mock_config.set.reset_mock()
        self.mock_config.save.reset_mock()

        # Test with invalid temperature (too high)
        self.cli.set_temperature(["1.5"])

        # Verify temperature was not changed
        self.assertEqual(self.cli.temperature, 0.5)

        # Verify error message
        mock_print.assert_called_with("Temperature must be between 0.0 and 1.0")

        # Reset mocks
        mock_print.reset_mock()

        # Test with no arguments (should show current temperature)
        self.cli.set_temperature([])

        # Verify current temperature is shown
        mock_print.assert_any_call("Current temperature: 0.5")


@patch(f"{MODULE_PATH}.TermSageCLI")
def test_main_function(mock_termsage_cli):
    """Test the main function creates and runs CLI."""
    # Mock CLI instance
    mock_cli = mock_termsage_cli.return_value

    # Call main
    main()

    # Verify CLI was created and run
    mock_termsage_cli.assert_called_once()
    mock_cli.run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
