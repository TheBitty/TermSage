"""
Integration tests for TermSage.

These tests verify the core functionality of TermSage by simulating
user input and checking the expected outputs.
"""

import unittest
import subprocess
import sys
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import io

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from src.main import TermSageCLI
    from src.config import Config
    from src.ollama import is_ollama_active, get_ollama_models

    MODULE_PATH = "src.main"
except ImportError:
    try:
        from main import TermSageCLI
        from config import Config
        from ollama import is_ollama_active, get_ollama_models

        MODULE_PATH = "main"
    except ImportError:
        from unittest.case import SkipTest

        raise SkipTest("Could not import necessary modules")


@unittest.skipIf(not is_ollama_active(), "Ollama service not running")
class TestTermSageIntegration(unittest.TestCase):
    """Integration tests for TermSage that require Ollama to be running."""

    def setUp(self):
        """Set up the test environment with a temporary config directory."""
        # Create temporary directory for test config
        self.temp_dir = tempfile.mkdtemp()

        # Create configuration with the temporary directory
        self.config = Config(self.temp_dir)

        # Set default values for testing
        self.config.set("active_model", None)
        self.config.set("temperature", 0.5)
        self.config.set("system_prompt", "You are a test assistant.")
        self.config.set("theme.prompt", "ansigreen bold")
        self.config.save()

        # Save original stdin and stdout
        self.original_stdin = sys.stdin
        self.original_stdout = sys.stdout

        # Set up stdin and stdout for testing
        self.stdin = io.StringIO()
        self.stdout = io.StringIO()
        sys.stdin = self.stdin
        sys.stdout = self.stdout

        # Create patches for terminal input/output
        self.mock_session = MagicMock()

        # Check if we have any models available
        self.models = get_ollama_models()
        if not self.models:
            self.skipTest("No Ollama models available for testing")

        # Get the first available model
        self.test_model = f"{self.models[0]['name']}:{self.models[0]['tag']}"

        # Set up CLI with patches
        with patch(f"{MODULE_PATH}.PromptSession", return_value=self.mock_session):
            with patch(f"{MODULE_PATH}.Config", return_value=self.config):
                self.cli = TermSageCLI()
                self.cli.active_model = self.test_model

    def tearDown(self):
        """Clean up the test environment."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)

        # Restore stdin and stdout
        sys.stdin = self.original_stdin
        sys.stdout = self.original_stdout

    def simulate_commands(self, commands):
        """
        Simulate a sequence of commands and return the output.

        Args:
            commands: List of command strings to execute

        Returns:
            String containing all output generated
        """
        # Set up the mock session to return each command in sequence
        self.mock_session.prompt.side_effect = commands + [KeyboardInterrupt()]

        try:
            # Clear previous output
            self.stdout = io.StringIO()
            sys.stdout = self.stdout

            # Run the CLI
            self.cli.run()
        except Exception as e:
            print(f"Error during test: {e}")

        # Return all output
        return self.stdout.getvalue()

    def test_help_command(self):
        """Test the help command shows available commands."""
        # Run help command
        output = self.simulate_commands(["help"])

        # Check that help information is shown
        self.assertIn("Available commands:", output)
        self.assertIn("help", output)
        self.assertIn("exit", output)
        self.assertIn("model", output)

    def test_list_models(self):
        """Test listing available models."""
        # Run list command
        output = self.simulate_commands(["list"])

        # Check that models are listed
        self.assertIn("Available models", output)

        # At least the first model should be shown
        for model in self.models[:1]:
            self.assertIn(model["name"], output)

    def test_temperature_command(self):
        """Test setting the temperature."""
        # Set to 0.8 and then show current
        output = self.simulate_commands(["temperature 0.8", "temperature"])

        # Check temperature was set and shown
        self.assertIn("Temperature set to 0.8", output)
        self.assertIn("Current temperature: 0.8", output)

    def test_model_command(self):
        """Test setting the model."""
        # If we have at least one model
        if self.models:
            # Set to the first model
            model_name = self.models[0]["name"]
            output = self.simulate_commands([f"model {model_name}"])

            # Check model was set
            self.assertIn(f"Active model set to {model_name}", output)

    def test_settings_command(self):
        """Test the settings menu."""
        # Show settings
        output = self.simulate_commands(["settings", "0"])

        # Check settings are shown
        self.assertIn("Settings:", output)
        self.assertIn("Active Model:", output)
        self.assertIn("Temperature:", output)
        self.assertIn("System Prompt:", output)


class TestCommandLineInterface(unittest.TestCase):
    """Test the command-line interface by running the script directly."""

    @unittest.skip("Skipping direct CLI test as it's not fully implemented")
    def test_main_script(self):
        """Test running the main script."""
        # Run the script with --help to test basic functionality
        # This doesn't require Ollama to be running
        try:
            # Use subprocess with timeout in case it hangs
            result = subprocess.run(
                [sys.executable, "-m", "src.main", "--help"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            # Check that it ran without error
            self.assertEqual(result.returncode, 0)

            # Not all Python scripts handle --help, so just check it ran
            self.assertFalse(result.stderr)

        except subprocess.TimeoutExpired:
            self.fail("Script execution timed out")


if __name__ == "__main__":
    unittest.main()
