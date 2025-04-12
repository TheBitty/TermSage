# TermSage

A Python project for [brief description of your project].

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Development

- Run tests: `pytest` or use the test runner: `./run_tests.py`
- Format code: `black .`
- Lint code: `flake8`

For comprehensive testing information, see [TESTING.md](TESTING.md).

## Project Structure

```
TermSage/
├── src/               # Source code
├── tests/            # Test files
├── requirements.txt  # Project dependencies
└── README.md        # This file
```

## Testing

The project includes comprehensive test scripts to verify its functionality:

- Unit tests with pytest
- Integration tests
- End-to-end tests

To run all tests with coverage reporting:

```bash
./run_tests.py --coverage
```

## License

[Your chosen license] 