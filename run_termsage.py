#!/usr/bin/env python3
"""
TermSage runner script.
This is a simple entry point to start TermSage from the root directory.
"""

import os
import sys
import importlib.util

def main():
    """Run the TermSage application by importing and calling its main function."""
    # Add the current directory to the path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)
    
    try:
        # Try to import the main module
        if importlib.util.find_spec("src.main") is not None:
            # Import the main module
            from src.main import main as termsage_main
            # Run the main function
            termsage_main()
        else:
            print("Error: Could not find src.main module.")
            print("Make sure you're running this script from the TermSage root directory.")
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
    except Exception as e:
        print(f"Error starting TermSage: {e}")


if __name__ == "__main__":
    main() 