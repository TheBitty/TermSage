"""
Main entry point for the TermSage application.

TermSage is a command-line interface for interacting with Ollama models,
featuring auto-completion and a rich user experience. It also functions as a
complete terminal shell, allowing you to run system commands alongside AI interactions.
"""

# Local imports - use try/except to handle potential import paths
try:
    from cli import TermSageCLI
except ImportError:
    from src.cli import TermSageCLI


def main():
    """Main entry point for TermSage."""
    print("=" * 60)
    print("TermSage - AI Command Shell")
    print("=" * 60)
    print("• Use Ollama models for AI chat and text generation")
    print("• Run system commands directly (ls, pwd, git, etc.)")
    print("• Supports pipes, redirections, and other shell features")
    print("• Type 'help' for available commands")
    print("=" * 60)
    
    # Initialize and run the CLI
    cli = TermSageCLI()
    cli.run()


if __name__ == "__main__":
    main()
