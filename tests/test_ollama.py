"""
Tests for the ollama module.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from src.ollama import (
        is_ollama_active,
        ollama_start,
        get_ollama_models,
        generate_text,
        create_chat_completer,
    )

    MODULE_PATH = "src.ollama"
except ImportError:
    try:
        from ollama import (
            is_ollama_active,
            ollama_start,
            get_ollama_models,
            generate_text,
            create_chat_completer,
        )

        MODULE_PATH = "ollama"
    except ImportError:
        from unittest.case import SkipTest

        raise SkipTest("Could not import ollama module")


class TestOllamaFunctions(unittest.TestCase):
    """Test cases for the ollama module functions."""

    @patch("subprocess.run")
    def test_is_ollama_active_when_running(self, mock_run):
        """Test is_ollama_active when Ollama is running."""
        # Mock subprocess result for when Ollama is running
        mock_process = MagicMock()
        mock_process.returncode = 0  # Success means process is running
        mock_run.return_value = mock_process

        # Call the function and check result
        result = is_ollama_active()
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["pgrep", "ollama"], capture_output=True, text=True
        )

    @patch("subprocess.run")
    def test_is_ollama_active_when_not_running(self, mock_run):
        """Test is_ollama_active when Ollama is not running."""
        # Mock subprocess result for when Ollama is not running
        mock_process = MagicMock()
        mock_process.returncode = 1  # Non-zero means process is not running
        mock_run.return_value = mock_process

        # Call the function and check result
        result = is_ollama_active()
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_is_ollama_active_handles_exception(self, mock_run):
        """Test is_ollama_active handles exceptions gracefully."""
        # Mock subprocess to raise an exception
        mock_run.side_effect = Exception("Test exception")

        # Call should not raise and return False
        result = is_ollama_active()
        self.assertFalse(result)

    @patch(f"{MODULE_PATH}.is_ollama_active")
    @patch("subprocess.Popen")
    @patch("time.sleep")
    def test_ollama_start_success(self, mock_sleep, mock_popen, mock_is_active):
        """Test ollama_start successfully starts Ollama."""
        # First check says not running, second says running (after start)
        mock_is_active.side_effect = [False, True]

        # Call function and check result
        result = ollama_start()
        self.assertTrue(result)

        # Verify subprocess.Popen was called to start Ollama
        mock_popen.assert_called_once()
        self.assertEqual(mock_popen.call_args[0][0][0], "ollama")

    @patch(f"{MODULE_PATH}.is_ollama_active")
    @patch("subprocess.Popen")
    @patch("time.sleep")
    def test_ollama_start_already_running(self, mock_sleep, mock_popen, mock_is_active):
        """Test ollama_start when Ollama is already running."""
        # Ollama is already running
        mock_is_active.return_value = True

        # Call function and check result
        result = ollama_start()
        self.assertTrue(result)

        # Verify subprocess.Popen was not called
        mock_popen.assert_not_called()

    @patch(f"{MODULE_PATH}.is_ollama_active")
    @patch("subprocess.Popen")
    @patch("time.sleep")
    def test_ollama_start_failure(self, mock_sleep, mock_popen, mock_is_active):
        """Test ollama_start when Ollama fails to start."""
        # Ollama never starts
        mock_is_active.return_value = False

        # Call function and check result
        result = ollama_start()
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_get_ollama_models_cli(self, mock_run):
        """Test get_ollama_models using CLI."""
        # Mock subprocess result with model list
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = """
NAME      TAG    ID      SIZE     MODIFIED
model1    latest abcd123 1.1GB    2023-01-01
model2    v2     efgh456 2.2GB    2023-02-02
"""
        mock_run.return_value = mock_process

        # Get models and check format
        models = get_ollama_models()

        # Verify models were parsed correctly
        self.assertEqual(len(models), 2)
        self.assertEqual(models[0]["name"], "model1")
        self.assertEqual(models[0]["tag"], "latest")
        self.assertEqual(models[0]["size"], "1.1GB")
        self.assertEqual(models[1]["name"], "model2")
        self.assertEqual(models[1]["tag"], "v2")

    @patch("subprocess.run")
    def test_get_ollama_models_error(self, mock_run):
        """Test get_ollama_models when CLI command fails."""
        # Mock subprocess failure
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_run.return_value = mock_process

        # Get models should return empty list on error
        models = get_ollama_models()
        self.assertEqual(models, [])

    def test_create_chat_completer(self):
        """Test create_chat_completer returns a completer with commands."""
        completer = create_chat_completer()
        # Check that completer has words property and it contains expected commands
        # Using a different approach to avoid type errors
        words_attr = getattr(completer, "words", [])
        self.assertTrue(any("exit" in str(w) for w in words_attr))
        self.assertTrue(any("help" in str(w) for w in words_attr))
        self.assertTrue(any("clear" in str(w) for w in words_attr))


class TestGenerateText(unittest.TestCase):
    """Test cases specifically for text generation."""

    @patch(f"{MODULE_PATH}.is_ollama_active")
    @patch(f"{MODULE_PATH}.ollama_start")
    @patch("subprocess.run")
    def test_generate_text_subprocess(self, mock_run, mock_start, mock_is_active):
        """Test generate_text using subprocess fallback."""
        # Mock ollama as active
        mock_is_active.return_value = True

        # Mock subprocess response
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Generated text response"
        mock_run.return_value = mock_process

        # Call function
        response = generate_text("model:tag", "Test prompt", temperature=0.5)

        # Check response and command
        self.assertEqual(response, "Generated text response")
        self.assertTrue(mock_run.called)

        # Verify command structure
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd[0:3], ["ollama", "run", "model:tag"])
        self.assertIn("-p", cmd)
        self.assertIn("--temperature", cmd)

    @patch(f"{MODULE_PATH}.is_ollama_active")
    @patch(f"{MODULE_PATH}.ollama_start")
    @patch("subprocess.run")
    def test_generate_text_with_system_prompt(
        self, mock_run, mock_start, mock_is_active
    ):
        """Test generate_text with system prompt."""
        # Mock ollama as active
        mock_is_active.return_value = True

        # Mock subprocess response
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Generated text response"
        mock_run.return_value = mock_process

        # Call function with system prompt
        _ = generate_text(
            "model:tag",
            "Test prompt",
            system_prompt="System instructions",
            temperature=0.5,
        )

        # Verify command includes system prompt
        cmd = mock_run.call_args[0][0]
        self.assertIn("--system", cmd)

    @patch(f"{MODULE_PATH}.is_ollama_active")
    def test_generate_text_ollama_not_running(self, mock_is_active):
        """Test generate_text when Ollama isn't running and can't start."""
        # Mock ollama as not active and not startable
        mock_is_active.return_value = False

        # Use context manager to patch specifically in this test
        with patch(f"{MODULE_PATH}.ollama_start", return_value=False):
            error_message = generate_text("model:tag", "Test prompt")

            # Should return error message
            self.assertIn("Error", error_message)
            self.assertIn("Ollama service", error_message)


if __name__ == "__main__":
    unittest.main()
