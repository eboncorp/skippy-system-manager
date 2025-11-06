# Skippy System Manager - Test Suite

**Version**: 1.0.0
**Last Updated**: 2025-11-05

## Overview

This directory contains the comprehensive test suite for the Skippy System Manager project. Tests are organized by type and use pytest as the testing framework.

## Directory Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Shared pytest fixtures and configuration
├── README.md                # This file
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_mcp_server_config.py
│   ├── test_file_operations.py
│   └── ...
├── integration/             # Integration tests (slower, require external services)
│   ├── test_wordpress_integration.py
│   ├── test_ssh_connectivity.py
│   └── ...
└── fixtures/                # Test data and fixtures
    ├── sample_files/
    └── mock_responses/
```

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -r requirements-test.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
pytest -m unit

# Integration tests only
pytest -m integration

# Smoke tests (quick validation)
pytest -m smoke

# Security tests
pytest -m security

# WordPress tests
pytest -m wordpress
```

### Run Specific Test Files

```bash
# Single file
pytest tests/unit/test_mcp_server_config.py

# Specific test class
pytest tests/unit/test_mcp_server_config.py::TestMCPServerConfiguration

# Specific test function
pytest tests/unit/test_mcp_server_config.py::TestMCPServerConfiguration::test_default_paths_when_no_env_vars
```

### Run Tests with Coverage

```bash
# Generate coverage report
pytest --cov

# Generate HTML coverage report
pytest --cov --cov-report=html

# View HTML report
open htmlcov/index.html
```

### Run Tests in Parallel

```bash
# Auto-detect number of CPUs
pytest -n auto

# Specify number of workers
pytest -n 4
```

## Test Markers

Tests are categorized using pytest markers. Available markers:

| Marker | Description | Example |
|--------|-------------|---------|
| `unit` | Fast, isolated unit tests | `@pytest.mark.unit` |
| `integration` | Tests requiring external services | `@pytest.mark.integration` |
| `slow` | Slow-running tests | `@pytest.mark.slow` |
| `security` | Security-related tests | `@pytest.mark.security` |
| `wordpress` | WordPress-specific tests | `@pytest.mark.wordpress` |
| `network` | Tests requiring network access | `@pytest.mark.network` |
| `ssh` | Tests requiring SSH connectivity | `@pytest.mark.ssh` |
| `docker` | Tests requiring Docker | `@pytest.mark.docker` |
| `smoke` | Quick validation tests | `@pytest.mark.smoke` |

### Using Markers

```python
import pytest

@pytest.mark.unit
def test_something():
    assert True

@pytest.mark.integration
@pytest.mark.wordpress
def test_wordpress_connection():
    # Test WordPress connectivity
    pass

@pytest.mark.slow
@pytest.mark.network
def test_large_file_download():
    # Long-running network test
    pass
```

## Writing Tests

### Test File Naming

- Unit tests: `test_<module_name>.py`
- Integration tests: `test_<service>_integration.py`

### Test Function Naming

- Test functions should start with `test_`
- Use descriptive names: `test_read_file_with_offset` instead of `test_read`

### Test Organization

```python
import pytest

class TestFeatureName:
    """Test feature description."""

    def test_specific_behavior(self):
        """Test that specific behavior works correctly."""
        # Arrange
        expected = "value"

        # Act
        actual = function_to_test()

        # Assert
        assert actual == expected
```

### Using Fixtures

Fixtures are defined in `conftest.py` and can be used in any test:

```python
def test_something(temp_dir, mock_skippy_env):
    """Test using shared fixtures."""
    # temp_dir provides a temporary directory
    # mock_skippy_env provides a mocked Skippy environment

    test_file = temp_dir / "test.txt"
    test_file.write_text("content")

    assert test_file.exists()
```

### Available Fixtures

| Fixture | Description |
|---------|-------------|
| `temp_dir` | Temporary directory for test files |
| `mock_skippy_env` | Mocked Skippy environment with directories |
| `sample_file` | Sample text file for testing |
| `mock_env_file` | Sample .env file |

## Test Coverage Goals

- **Overall Coverage**: 60% minimum (enforced in CI/CD)
- **New Code**: 80% minimum
- **Critical Components**: 90% minimum
  - MCP Server core
  - WordPress management
  - Backup/restore operations
  - Security functions

## Continuous Integration

Tests are automatically run on:
- Push to `main` or `develop` branches
- Pull requests to `main`
- Daily schedule (2 AM)
- Manual workflow dispatch

See `.github/workflows/ci.yml` for CI/CD configuration.

## Test Data

### Creating Test Fixtures

Place test data in `tests/fixtures/`:

```python
# tests/fixtures/sample_data.py
SAMPLE_WP_RESPONSE = {
    "version": "6.3",
    "plugins": ["plugin1", "plugin2"]
}
```

### Using Test Fixtures

```python
from tests.fixtures.sample_data import SAMPLE_WP_RESPONSE

def test_parse_wp_response():
    result = parse_response(SAMPLE_WP_RESPONSE)
    assert result["version"] == "6.3"
```

## Mocking External Services

### Mocking SSH Connections

```python
from unittest.mock import Mock, patch

@pytest.mark.unit
def test_ssh_command():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            returncode=0,
            stdout="success",
            stderr=""
        )

        result = execute_ssh_command("ls")
        assert result == "success"
```

### Mocking HTTP Requests

```python
import responses

@responses.activate
def test_http_request():
    responses.add(
        responses.GET,
        'http://example.com/api',
        json={'status': 'ok'},
        status=200
    )

    result = make_api_request()
    assert result['status'] == 'ok'
```

## Debugging Tests

### Run Tests in Verbose Mode

```bash
pytest -v
```

### Show Print Statements

```bash
pytest -s
```

### Drop into Debugger on Failure

```bash
pytest --pdb
```

### Run Last Failed Tests

```bash
pytest --lf
```

### Show Local Variables in Tracebacks

```bash
pytest -l
```

## Best Practices

1. **Keep tests fast**: Unit tests should run in milliseconds
2. **Isolate tests**: Each test should be independent
3. **Use descriptive names**: Test names should explain what they test
4. **Follow AAA pattern**: Arrange, Act, Assert
5. **Mock external dependencies**: Don't rely on external services in unit tests
6. **Test edge cases**: Don't just test the happy path
7. **Keep tests simple**: Tests should be easier to understand than the code they test
8. **Don't test implementation details**: Test behavior, not internals
9. **Use fixtures for common setup**: Avoid code duplication
10. **Document complex tests**: Add docstrings explaining what's being tested

## Common Issues

### Import Errors

If you get import errors, ensure pytest can find the modules:

```bash
# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

Or use the `pythonpath` setting in `pytest.ini` (already configured).

### Missing Dependencies

```bash
# Install all test dependencies
pip install -r requirements-test.txt

# Or install package in development mode
pip install -e .
```

### Test Database Issues

For tests requiring a database:
```bash
# Set test database environment variables
export TEST_DB_NAME="skippy_test"
export TEST_DB_USER="test_user"
export TEST_DB_PASSWORD="test_password"
```

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure all tests pass: `pytest`
3. Check coverage: `pytest --cov`
4. Run linters: `pylint`, `flake8`
5. Update this README if adding new test categories

## Related Documentation

- **pytest documentation**: https://docs.pytest.org/
- **pytest-cov documentation**: https://pytest-cov.readthedocs.io/
- **Project architecture**: `../PROJECT_ARCHITECTURE.md`
- **Contributing guide**: `../CONTRIBUTING.md`

---

**Questions or Issues?**
File an issue or consult the project documentation.
