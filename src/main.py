"""
Main entry point for the TermSage application.

TermSage is a command-line interface for interacting with Ollama models,
featuring auto-completion and a rich user experience.
"""

# Local imports - use try/except to handle potential import paths
try:
    from cli import TermSageCLI
except ImportError:
    from src.cli import TermSageCLI


def main():
    """Main entry point for TermSage."""
    cli = TermSageCLI()
    cli.run()


if __name__ == "__main__":
    main()
