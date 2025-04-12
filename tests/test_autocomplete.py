"""
Tests for the autocomplete module.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.autocomplete import TermSageCompleter, setup_completer
    MODULE_PATH = 'src.autocomplete'
except ImportError:
    try:
        from autocomplete import TermSageCompleter, setup_completer
        MODULE_PATH = 'autocomplete'
    except ImportError:
        # Skip tests if module cannot be imported
        from unittest.case import SkipTest
        raise SkipTest("Could not import autocomplete module")


class TestTermSageCompleter(unittest.TestCase):
    """Test cases for the TermSageCompleter class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a mock for get_ollama_models
        self.mock_get_models = MagicMock()
        self.mock_get_models.return_value = [
            {'name': 'model1', 'tag': 'latest', 'id': 'id1', 'size': '1.1GB'},
            {'name': 'model2', 'tag': 'v2', 'id': 'id2', 'size': '2.2GB'}
        ]
        
        # Create a completer with the mock
        self.completer = TermSageCompleter(self.mock_get_models)
    
    def test_record_command(self):
        """Test recording commands for history."""
        # Record some commands
        self.completer.record_command("test1")
        self.completer.record_command("test2")
        self.completer.record_command("test1")  # Duplicate should move to front
        
        # Check command history
        self.assertEqual(len(self.completer.command_history), 2)
        self.assertEqual(self.completer.command_history[0], "test1")
        self.assertEqual(self.completer.command_history[1], "test2")
    
    def test_setup_completer(self):
        """Test the setup_completer function."""
        completer = setup_completer(self.mock_get_models)
        self.assertIsInstance(completer, TermSageCompleter)
        self.assertEqual(completer.get_ollama_models, self.mock_get_models)


if __name__ == '__main__':
    unittest.main() 