# Contributing to Skippy System Manager

Thank you for your interest in contributing to Skippy System Manager! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Environment Setup](#development-environment-setup)
3. [Project Structure](#project-structure)
4. [Coding Standards](#coding-standards)
5. [Testing Requirements](#testing-requirements)
6. [Git Workflow](#git-workflow)
7. [Pull Request Process](#pull-request-process)
8. [Documentation](#documentation)
9. [Security](#security)
10. [Getting Help](#getting-help)

---

## Getting Started

### Prerequisites

- **OS**: Linux (Ubuntu/Debian recommended)
- **Python**: 3.8 or higher
- **Bash**: 4.0 or higher
- **Git**: 2.0 or higher
- **Node.js**: 14+ (optional, for some scripts)

### First Contribution Checklist

- [ ] Read this contributing guide
- [ ] Review the [Code of Conduct](#code-of-conduct)
- [ ] Check [existing issues](https://github.com/eboncorp/skippy-system-manager/issues)
- [ ] Set up development environment
- [ ] Run tests to ensure everything works
- [ ] Make your changes
- [ ] Write/update tests
- [ ] Update documentation
- [ ] Submit pull request

---

## Development Environment Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/skippy-system-manager.git
cd skippy-system-manager
```

### 2. Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# System dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y jq curl gpg shellcheck
```

### 3. Configure Environment

```bash
# Copy configuration template
cp config.env.example config.env

# Edit config.env with your settings
# See config.env.example for details
nano config.env

# Set proper permissions
chmod 600 config.env

# Validate configuration
source config.env
bash scripts/utility/validate_config.sh
```

### 4. Verify Setup

```bash
# Run tests to verify everything works
pytest

# Check code quality
pylint lib/python/
flake8 lib/python/

# Run shellcheck on scripts
shellcheck scripts/**/*.sh
```

---

## Project Structure

```
skippy-system-manager/
├── .github/workflows/     # CI/CD configuration
├── mcp-servers/           # MCP server implementation
├── scripts/               # Automation scripts (19 categories)
├── lib/python/            # Shared Python libraries
├── tests/                 # Test suite
├── documentation/         # Project documentation
├── conversations/         # Session logs
├── config.env.example     # Configuration template
├── SCRIPT_STATUS.md       # Script status tracking
├── PROJECT_ARCHITECTURE.md # Architecture documentation
└── CONTRIBUTING.md        # This file
```

For detailed architecture, see [PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md).

---

## Coding Standards

### Python Code

#### Style Guide

- **PEP 8**: Follow PEP 8 style guide
- **Line Length**: Maximum 100 characters
- **Indentation**: 4 spaces (no tabs)
- **Imports**: Organize imports (stdlib, third-party, local)
- **Type Hints**: Use type hints for function signatures (Python 3.8+)

#### Example

```python
#!/usr/bin/env python3
"""
Module description.

Version: 1.0.0
"""

from typing import Optional, List
import os
from pathlib import Path

from lib.python.skippy_logger import get_logger
from lib.python.skippy_validator import validate_path


logger = get_logger(__name__)


def process_files(
    directory: Path,
    pattern: str = "*.txt",
    recursive: bool = False,
) -> List[Path]:
    """
    Process files in a directory.

    Args:
        directory: Directory to search
        pattern: File pattern to match
        recursive: Whether to search recursively

    Returns:
        List of matching file paths

    Raises:
        ValidationError: If directory is invalid
    """
    # Validate input
    validated_dir = validate_path(directory, must_exist=True)

    # Implementation
    if recursive:
        files = list(validated_dir.rglob(pattern))
    else:
        files = list(validated_dir.glob(pattern))

    logger.info(f"Found {len(files)} files matching {pattern}")
    return files
```

#### Linting

```bash
# Run pylint
pylint lib/python/your_module.py

# Run flake8
flake8 lib/python/your_module.py

# Auto-format with black (optional)
black lib/python/your_module.py
```

### Shell Scripts

#### Style Guide

- **SheBang**: Use `#!/bin/bash`
- **Set Options**: `set -euo pipefail` at the top
- **Indentation**: 2 spaces
- **Variables**: Use `${variable}` instead of `$variable`
- **Functions**: Document with comments
- **Error Handling**: Check return codes

#### Example

```bash
#!/bin/bash
# Script Name: example_script_v1.0.0.sh
# Version: 1.0.0
# Purpose: Example script demonstrating coding standards
# Usage: ./example_script_v1.0.0.sh [options]

set -euo pipefail

# Constants
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_FILE="/var/log/skippy/example.log"

# Functions
log_info() {
    local message="$1"
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - ${message}" | tee -a "${LOG_FILE}"
}

log_error() {
    local message="$1"
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - ${message}" >&2 | tee -a "${LOG_FILE}"
}

# Main
main() {
    log_info "Script started"

    # Your code here

    log_info "Script completed successfully"
}

# Run main function
main "$@"
```

#### Linting

```bash
# Run shellcheck
shellcheck scripts/your_script.sh
```

### Naming Conventions

#### Files

- Scripts: `script_name_v1.0.0.ext`
- Python modules: `module_name.py` (lowercase with underscores)
- Test files: `test_module_name.py`

#### Variables

- Python: `snake_case` for variables and functions
- Python: `PascalCase` for classes
- Python: `UPPER_CASE` for constants
- Bash: `lowercase_with_underscores` for variables
- Bash: `UPPERCASE` for constants

---

## Testing Requirements

### Running Tests

```bash
# Run all tests
pytest

# Run specific test category
pytest -m unit
pytest -m integration

# Run with coverage
pytest --cov
```

### Writing Tests

#### Unit Tests

```python
import pytest
from your_module import your_function


@pytest.mark.unit
class TestYourFunction:
    """Test your_function behavior."""

    def test_normal_case(self):
        """Test normal operation."""
        result = your_function("input")
        assert result == "expected_output"

    def test_edge_case(self):
        """Test edge case."""
        result = your_function("")
        assert result == ""

    def test_error_case(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            your_function(None)
```

#### Integration Tests

```python
@pytest.mark.integration
def test_database_integration():
    """Test database operations."""
    # Setup
    db = setup_test_database()

    # Test
    result = query_database(db, "SELECT * FROM test")

    # Assert
    assert len(result) > 0

    # Cleanup
    cleanup_test_database(db)
```

### Test Coverage

- **Minimum**: 60% overall coverage
- **New Code**: 80% coverage for new features
- **Critical Components**: 90% coverage for MCP server, security, backups

---

## Git Workflow

### Branching Strategy

```
main
 ├── develop
 ├── feature/feature-name
 ├── bugfix/bug-description
 ├── hotfix/critical-fix
 └── release/v1.2.0
```

### Creating a Feature Branch

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ...

# Commit changes
git add .
git commit -m "feat: add new feature description"

# Push to your fork
git push origin feature/your-feature-name
```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

#### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

#### Examples

```bash
# Feature
git commit -m "feat: add input validation library"

# Bug fix
git commit -m "fix: resolve path traversal vulnerability in file operations"

# Documentation
git commit -m "docs: update contributing guide with testing requirements"

# Refactor
git commit -m "refactor: consolidate duplicate code in MCP server"
```

---

## Pull Request Process

### Before Submitting

1. **Update your branch** with latest main:
   ```bash
   git checkout main
   git pull origin main
   git checkout your-branch
   git rebase main
   ```

2. **Run all tests**:
   ```bash
   pytest
   pylint lib/python/
   flake8 lib/python/
   shellcheck scripts/**/*.sh
   ```

3. **Update documentation**:
   - Add/update docstrings
   - Update README if needed
   - Update SCRIPT_STATUS.md if adding scripts
   - Log conversation in conversations/

4. **Ensure code quality**:
   - No linting errors
   - Code coverage meets requirements
   - All tests pass

### Submitting Pull Request

1. **Push to your fork**:
   ```bash
   git push origin your-branch
   ```

2. **Create pull request** on GitHub

3. **Fill out PR template**:
   - Description of changes
   - Related issues (e.g., "Fixes #123")
   - Testing performed
   - Screenshots (if UI changes)

4. **Wait for review**:
   - Address reviewer feedback
   - Make requested changes
   - Push updates to same branch

### PR Review Criteria

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] Code coverage meets requirements
- [ ] Documentation is updated
- [ ] No security vulnerabilities introduced
- [ ] Commit messages follow conventional format
- [ ] Changes are backward compatible (or documented)

---

## Documentation

### Required Documentation

1. **Code Documentation**:
   - Docstrings for all functions/classes
   - Inline comments for complex logic
   - Type hints for function signatures

2. **Script Documentation**:
   - Header comment with version, purpose, usage
   - Function documentation
   - Example usage

3. **User Documentation**:
   - Update README if needed
   - Add/update protocol documents
   - Update SCRIPT_STATUS.md

### Documentation Style

```python
def function_name(param1: str, param2: int = 0) -> bool:
    """
    Short description (one line).

    Longer description explaining what the function does,
    any important details, and how it should be used.

    Args:
        param1: Description of param1
        param2: Description of param2 (default: 0)

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is invalid
        FileNotFoundError: When file doesn't exist

    Example:
        >>> function_name("test", 5)
        True
    """
    # Implementation
    pass
```

---

## Security

### Security Guidelines

1. **Never commit secrets**:
   - No passwords, API keys, tokens in code
   - Use `.env` files (gitignored)
   - Use environment variables

2. **Input validation**:
   - Always validate user input
   - Use `lib/python/skippy_validator.py`
   - Prevent injection attacks

3. **Safe file operations**:
   - Validate file paths
   - Prevent directory traversal
   - Check file permissions

4. **Secure defaults**:
   - Fail securely
   - Minimal permissions
   - Principle of least privilege

### Reporting Security Issues

**Do not open public issues for security vulnerabilities.**

Instead, email security concerns to: [security@example.com]

Include:
- Description of vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

---

## Code Review Process

### As an Author

1. **Self-review** your code before submitting
2. **Test thoroughly** - don't rely on reviewers to find bugs
3. **Provide context** in PR description
4. **Respond promptly** to feedback
5. **Be open** to suggestions and criticism

### As a Reviewer

1. **Be constructive** and respectful
2. **Focus on code**, not the person
3. **Explain reasoning** for requested changes
4. **Approve** when ready, or request changes clearly
5. **Follow up** if changes requested

---

## Getting Help

### Resources

- **Documentation**: Check `documentation/` directory
- **Architecture**: See `PROJECT_ARCHITECTURE.md`
- **Script Status**: See `SCRIPT_STATUS.md`
- **Issues**: Search existing issues on GitHub
- **Conversations**: Review `conversations/` for examples

### Asking Questions

1. **Check existing documentation** first
2. **Search closed issues** for similar questions
3. **Open a new issue** with:
   - Clear, descriptive title
   - What you're trying to do
   - What you've tried
   - Relevant code/logs
   - System information

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: Questions, ideas, general discussion
- **Pull Requests**: Code review, implementation discussion

---

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity, level of experience, nationality, personal appearance, race, religion, or sexual identity.

### Our Standards

**Positive behavior**:
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what's best for the community
- Showing empathy towards others

**Unacceptable behavior**:
- Trolling, insulting/derogatory comments, personal attacks
- Public or private harassment
- Publishing others' private information
- Other conduct which could reasonably be considered inappropriate

### Enforcement

Project maintainers are responsible for clarifying standards and will take appropriate corrective action in response to unacceptable behavior.

---

## License

By contributing to Skippy System Manager, you agree that your contributions will be licensed under the same license as the project.

---

## Acknowledgments

Thank you to all contributors who help make Skippy System Manager better!

### Contributors

- List of contributors (automatically generated)

---

## Quick Reference

### Common Commands

```bash
# Setup
git clone <repo>
pip install -r requirements.txt requirements-test.txt
cp config.env.example config.env

# Development
git checkout -b feature/my-feature
# ... make changes ...
git commit -m "feat: description"
git push origin feature/my-feature

# Testing
pytest                    # All tests
pytest -m unit           # Unit tests only
pytest --cov             # With coverage
pylint lib/python/       # Python linting
flake8 lib/python/       # Python style
shellcheck scripts/**/*.sh  # Shell linting

# Pull Request
# Create PR on GitHub
# Address review feedback
# Merge when approved
```

---

**Questions?** Open an issue or check existing documentation.

**Ready to contribute?** Pick an issue and get started!

Thank you for contributing to Skippy System Manager! 🚀
