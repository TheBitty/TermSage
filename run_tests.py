#!/usr/bin/env python3
"""
Test runner script for TermSage.

This script runs all tests and generates code coverage reports.
"""

import os
import sys
import subprocess
import argparse
import time


def print_banner(message):
    """Print a banner with the given message."""
    border = "=" * (len(message) + 4)
    print(f"\n{border}")
    print(f"= {message} =")
    print(f"{border}\n")


def run_linting():
    """Run flake8 linting on the codebase."""
    print_banner("Running Linting (flake8)")
    
    try:
        result = subprocess.run(
            ["flake8", "src", "tests"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Linting passed - no issues found!")
            return True
        else:
            print("❌ Linting found issues:")
            print(result.stdout)
            return False
    except Exception as e:
        print(f"Error running linting: {e}")
        return False


def run_black_check():
    """Check code formatting with black."""
    print_banner("Checking Code Formatting (black)")
    
    try:
        result = subprocess.run(
            ["black", "--check", "src", "tests"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Code formatting check passed!")
            return True
        else:
            print("❌ Code formatting issues found:")
            print(result.stdout)
            print("\nTo fix formatting issues, run: black src tests")
            return False
    except Exception as e:
        print(f"Error checking code formatting: {e}")
        return False


def run_tests(coverage=False):
    """
    Run all tests.
    
    Args:
        coverage: Whether to generate coverage report
    
    Returns:
        bool: True if all tests passed, False otherwise
    """
    print_banner("Running Tests")
    
    cmd = ["pytest"]
    
    if coverage:
        cmd.extend([
            "--cov=src",
            "--cov-report=term",
            "--cov-report=html:coverage_report"
        ])
    
    cmd.extend(["-v", "tests/"])
    
    try:
        result = subprocess.run(cmd, text=True)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
            return True
        else:
            print("\n❌ Some tests failed.")
            return False
    except Exception as e:
        print(f"Error running tests: {e}")
        return False


def format_code():
    """Format code using black."""
    print_banner("Formatting Code (black)")
    
    try:
        result = subprocess.run(
            ["black", "src", "tests"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Code formatted successfully!")
            return True
        else:
            print(f"❌ Error formatting code: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error formatting code: {e}")
        return False


def check_ollama_running():
    """Check if Ollama service is running."""
    print_banner("Checking Ollama Service")
    
    try:
        # Import is_ollama_active from the codebase
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        try:
            from src.ollama import is_ollama_active
        except ImportError:
            from ollama import is_ollama_active
        
        if is_ollama_active():
            print("✅ Ollama service is running.")
            return True
        else:
            print("❌ Ollama service is NOT running.")
            print("Some integration tests will be skipped.")
            return False
    except ImportError:
        print("⚠️ Could not import ollama module to check service.")
        return False


def main():
    """Execute all testing operations."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run tests for TermSage")
    parser.add_argument(
        "--coverage", 
        action="store_true", 
        help="Generate code coverage report"
    )
    parser.add_argument(
        "--lint-only", 
        action="store_true", 
        help="Only run linting checks"
    )
    parser.add_argument(
        "--format", 
        action="store_true", 
        help="Format code with black"
    )
    
    args = parser.parse_args()
    
    # Start timing
    start_time = time.time()
    
    # Format code if requested
    if args.format:
        format_code()
    
    # Check linting
    linting_passed = run_linting()
    
    # Check formatting
    format_check_passed = run_black_check()
    
    # Exit if only linting is requested
    if args.lint_only:
        return 0 if linting_passed and format_check_passed else 1
    
    # Check Ollama service for integration tests
    check_ollama_running()
    
    # Run tests
    tests_passed = run_tests(coverage=args.coverage)
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    # Print summary
    print_banner(f"Test Run Summary (Elapsed time: {elapsed_time:.2f} seconds)")
    print(f"Linting: {'✅ PASSED' if linting_passed else '❌ FAILED'}")
    print(f"Formatting: {'✅ PASSED' if format_check_passed else '❌ FAILED'}")
    print(f"Tests: {'✅ PASSED' if tests_passed else '❌ FAILED'}")
    
    # Show coverage report path if generated
    if args.coverage:
        print("\nCoverage report generated at: ./coverage_report/index.html")
    
    # Determine exit code
    success = linting_passed and format_check_passed and tests_passed
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 