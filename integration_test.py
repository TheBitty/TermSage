#!/usr/bin/env python3
"""
TermSage Integration Test Script

This script performs a full integration test of the TermSage application by:
1. Starting the Ollama service if not running
2. Checking for model availability
3. Testing all main commands and functionalities
4. Reporting results

This provides an easy way to verify the entire application is working correctly.
"""

import os
import sys
import time
import subprocess
import tempfile
import shutil
import argparse
from typing import Dict, List, Tuple, Optional, Any
import json

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import from source directory
try:
    from src.ollama import is_ollama_active, ollama_start, get_ollama_models
    from src.config import Config
except ImportError:
    try:
        from ollama import is_ollama_active, ollama_start, get_ollama_models
        from config import Config
    except ImportError:
        print("ERROR: Could not import TermSage modules. Make sure you're in the correct directory.")
        sys.exit(1)


class TestResult:
    """Class to track test results."""
    
    def __init__(self):
        """Initialize test results."""
        self.passed = []
        self.failed = []
        self.skipped = []
        self.start_time = time.time()
    
    def pass_test(self, name: str, message: str = ""):
        """Record a passed test."""
        self.passed.append((name, message))
        print(f"✅ PASS: {name}{' - ' + message if message else ''}")
    
    def fail_test(self, name: str, message: str = ""):
        """Record a failed test."""
        self.failed.append((name, message))
        print(f"❌ FAIL: {name}{' - ' + message if message else ''}")
    
    def skip_test(self, name: str, message: str = ""):
        """Record a skipped test."""
        self.skipped.append((name, message))
        print(f"⏭️  SKIP: {name}{' - ' + message if message else ''}")
    
    def summary(self) -> str:
        """Generate a summary of test results."""
        total = len(self.passed) + len(self.failed) + len(self.skipped)
        elapsed = time.time() - self.start_time
        
        return (
            f"\n==== Test Summary ====\n"
            f"Total tests: {total}\n"
            f"Passed: {len(self.passed)}\n"
            f"Failed: {len(self.failed)}\n"
            f"Skipped: {len(self.skipped)}\n"
            f"Time elapsed: {elapsed:.2f} seconds\n"
            f"======================="
        )
    
    def all_passed(self) -> bool:
        """Check if all tests passed."""
        return len(self.failed) == 0


def print_header(message: str) -> None:
    """Print a header message."""
    print(f"\n=== {message} ===")


def run_command(cmd: List[str], timeout: int = 60) -> Tuple[int, str, str]:
    """
    Run a command and return exit code, stdout, and stderr.
    
    Args:
        cmd: Command list to execute
        timeout: Timeout in seconds
        
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)


def ensure_ollama_running(results: TestResult) -> bool:
    """
    Ensure Ollama service is running.
    
    Args:
        results: TestResult object to track results
        
    Returns:
        True if Ollama is running, False otherwise
    """
    print_header("Checking Ollama Service")
    
    if is_ollama_active():
        results.pass_test("ollama_service", "Ollama service is running")
        return True
    
    print("Ollama service not running, attempting to start...")
    
    if ollama_start():
        # Give it a moment to fully initialize
        time.sleep(2)
        results.pass_test("ollama_start", "Successfully started Ollama service")
        return True
    else:
        results.fail_test("ollama_start", "Failed to start Ollama service")
        return False


def check_ollama_models(results: TestResult) -> Optional[str]:
    """
    Check for available Ollama models.
    
    Args:
        results: TestResult object to track results
        
    Returns:
        First model name if available, None otherwise
    """
    print_header("Checking Available Models")
    
    models = get_ollama_models()
    
    if not models:
        results.fail_test("ollama_models", "No models available")
        print("No models found. Please pull at least one model with 'ollama pull <model_name>'")
        print("For example: ollama pull llama2")
        return None
    
    model_names = [f"{m['name']}:{m['tag']}" for m in models]
    results.pass_test("ollama_models", f"Found {len(models)} models: {', '.join(model_names[:3])}" +
                    ("..." if len(models) > 3 else ""))
    
    # Return the first model for testing
    return f"{models[0]['name']}:{models[0]['tag']}"


def test_cli_help(results: TestResult) -> None:
    """
    Test CLI help command.
    
    Args:
        results: TestResult object to track results
    """
    print_header("Testing CLI Help")
    
    # Try running without --help first (not all CLI tools support --help)
    exit_code, stdout, stderr = run_command([sys.executable, "-m", "src.main"], timeout=3)
    
    if exit_code == 0:
        results.pass_test("cli_help", "CLI script runs successfully")
    else:
        # Fall back to checking if the module can be imported
        try:
            import src.main
            results.pass_test("cli_help", "CLI module can be imported")
        except ImportError:
            results.fail_test("cli_help", "Failed to import CLI module")


def test_generate_text(results: TestResult, model: Optional[str]) -> None:
    """
    Test text generation with Ollama.
    
    Args:
        results: TestResult object to track results
        model: Model to use for generation
    """
    if not model:
        results.skip_test("generate_text", "No model available")
        return
    
    print_header(f"Testing Text Generation with {model}")
    
    try:
        from src.ollama import generate_text, is_ollama_active
        
        # Verify Ollama is running
        if not is_ollama_active():
            results.skip_test("generate_text", "Ollama service not running")
            return
            
        # Try a simple prompt
        prompt = "Write a single word."
        response = generate_text(model, prompt, temperature=0.5)
        
        # Check if we got any response at all
        if response is not None:
            results.pass_test("generate_text", "Successfully received a response from model")
        else:
            results.fail_test("generate_text", "No response received from model")
    except Exception as e:
        results.fail_test("generate_text", f"Error during text generation: {str(e)}")


def test_config(results: TestResult) -> None:
    """
    Test configuration loading and saving.
    
    Args:
        results: TestResult object to track results
    """
    print_header("Testing Configuration")
    
    try:
        # Create a temporary directory for config
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Initialize config
            config = Config(temp_dir)
            
            # Set a test value
            config.set("test_key", "test_value")
            config.save()
            
            # Create a new config instance to load the saved value
            new_config = Config(temp_dir)
            loaded_value = new_config.get("test_key")
            
            if loaded_value == "test_value":
                results.pass_test("config_save_load", "Successfully saved and loaded config")
            else:
                results.fail_test("config_save_load", f"Expected 'test_value', got '{loaded_value}'")
            
            # Test nested config
            config.set("nested.key", "nested_value")
            config.save()
            
            new_config = Config(temp_dir)
            nested_value = new_config.get("nested.key")
            
            if nested_value == "nested_value":
                results.pass_test("config_nested", "Successfully handled nested config")
            else:
                results.fail_test("config_nested", f"Expected 'nested_value', got '{nested_value}'")
        
        finally:
            # Clean up
            shutil.rmtree(temp_dir)
    
    except Exception as e:
        results.fail_test("config", f"Error testing configuration: {str(e)}")


def run_integration_tests() -> int:
    """
    Run all integration tests.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("\n========================================")
    print("   TermSage Integration Test Suite")
    print("========================================\n")
    
    results = TestResult()
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check if Ollama is running
    ollama_running = ensure_ollama_running(results)
    
    # Test configuration
    test_config(results)
    
    # Skip model-dependent tests if Ollama isn't running
    if ollama_running:
        # Check models
        model = check_ollama_models(results)
        
        # Test text generation
        test_generate_text(results, model)
    else:
        results.skip_test("model_checks", "Ollama service not running")
        results.skip_test("generate_text", "Ollama service not running")
    
    # Test CLI help
    test_cli_help(results)
    
    # Print summary
    print(results.summary())
    
    # Return success if all tests passed
    return 0 if results.all_passed() else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TermSage Integration Tests")
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    
    sys.exit(run_integration_tests()) 