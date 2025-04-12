"""
Tests for the main module.
"""

from venv.src import main


def test_main(capsys):
    """Test that the main function runs without errors."""
    main()
    captured = capsys.readouterr()
    assert "Welcome to TermSage!" in captured.out
