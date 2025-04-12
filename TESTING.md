# Testing TermSage

This document provides instructions on how to test the TermSage application to ensure its correct functionality.

## Test Scripts

The project includes several test scripts to verify different aspects of the application:

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test the interaction between components
3. **End-to-end Test**: Test the whole application flow

## Prerequisites

Before running the tests, ensure you have installed all the required dependencies:

```bash
pip install -r requirements.txt
```

## Running the Tests

### Using the Test Runner

The easiest way to run all tests is to use the test runner script:

```bash
./run_tests.py
```

Options:
- `--coverage`: Generate a code coverage report
- `--lint-only`: Only run linting checks without executing tests
- `--format`: Format code with black before running tests

Example:
```bash
./run_tests.py --coverage
```

### Running Individual Tests

You can also run individual test modules with pytest:

```bash
# Run a specific test file
pytest tests/test_config.py

# Run all tests with verbose output
pytest -v tests/

# Run tests with coverage
pytest --cov=src tests/
```

### Integration Test

To run a full integration test that checks the entire application flow:

```bash
./integration_test.py
```

This script:
1. Checks if Ollama is running (and tries to start it if not)
2. Tests the configuration module
3. Checks available models
4. Tests text generation
5. Tests the CLI interface

## CI/CD Integration

The test scripts are designed to work in CI/CD environments with appropriate exit codes:
- Exit code 0: All tests passed
- Exit code 1: One or more tests failed

You can use these exit codes to trigger appropriate actions in your CI/CD pipeline.

## Linting and Formatting

The project uses flake8 for linting and black for code formatting:

```bash
# Check code style with flake8
flake8 src tests

# Format code with black
black src tests
```

## Troubleshooting

### Common Issues

1. **Ollama Service Not Running**
   
   Some tests require the Ollama service to be running. If you see skipped tests related to Ollama, make sure the service is running and try again.

2. **No Models Available**
   
   Text generation tests require at least one model to be available. If no models are found, pull one with:
   ```bash
   ollama pull llama2
   ```

3. **Import Errors**
   
   If you encounter import errors, make sure you're running the tests from the project root directory.

## Adding New Tests

When adding new functionality to TermSage, please also add appropriate tests:

1. Unit tests in the `tests/` directory following the pattern `test_*.py`
2. Update the integration test if necessary to cover the new functionality

Aim for high test coverage to ensure the application remains stable and reliable. 