# Claude Code Reference Guide
**Version**: 1.0.0
**Last Updated**: 2025-11-10
**Purpose**: Quick reference for AI assistants working on Skippy System Manager

---

## 🎯 Quick Start for Claude Code

When working on this repository, **ALWAYS**:

1. ✅ Check this file first before making changes
2. ✅ Use the standard libraries (validation, logging, errors)
3. ✅ Follow the naming conventions
4. ✅ Write tests for new code
5. ✅ Update documentation
6. ✅ Run validators before committing

---

## 📚 Table of Contents

1. [Repository Overview](#repository-overview)
2. [Standard Libraries (MUST USE)](#standard-libraries-must-use)
3. [File Naming Conventions](#file-naming-conventions)
4. [Script Template](#script-template)
5. [Testing Requirements](#testing-requirements)
6. [Common Workflows](#common-workflows)
7. [Where Things Are](#where-things-are)
8. [Pre-Commit Checklist](#pre-commit-checklist)
9. [Common Mistakes to Avoid](#common-mistakes-to-avoid)
10. [Quick Commands](#quick-commands)

---

## Repository Overview

### What is Skippy?
A comprehensive automation and management suite for:
- Infrastructure automation and monitoring
- WordPress website management
- System administration tasks
- Backup and disaster recovery
- Security auditing

### Architecture
```
Hybrid System:
├── MCP Server (mcp-servers/general-server/server.py)
│   └── 43+ tools for AI-powered automation
├── Script Library (scripts/)
│   └── 319+ standalone automation scripts
└── Shared Libraries (lib/)
    ├── Python (lib/python/)
    └── Bash (lib/bash/) ← NEW! Use these!
```

### Key Statistics
- **Total Scripts**: 319+
- **Languages**: Python (156), Bash (163)
- **MCP Tools**: 43+
- **Test Coverage Target**: 80% (currently building up)

---

## Standard Libraries (MUST USE)

### ⭐ Always Import These in New Scripts

#### For Bash Scripts

```bash
#!/bin/bash
# Script Name
# Version: 1.0.0
# Purpose: Brief description
# Usage: ./script_name_v1.0.0.sh [options]

set -euo pipefail

# Load configuration
if [[ -f "${SKIPPY_BASE_PATH}/config.env" ]]; then
    source "${SKIPPY_BASE_PATH}/config.env"
fi

# Load Skippy libraries
source "${SKIPPY_BASE_PATH}/lib/bash/skippy_logging.sh"
source "${SKIPPY_BASE_PATH}/lib/bash/skippy_errors.sh"
source "${SKIPPY_BASE_PATH}/lib/bash/skippy_validation.sh"

# Initialize
SCRIPT_NAME="$(basename "$0")"
init_logging "/var/log/skippy/${SCRIPT_NAME}.log" "INFO"
setup_error_trap

# Your code here...
```

#### For Python Scripts

```python
#!/usr/bin/env python3
"""
Script Name
Version: 1.0.0
Purpose: Brief description
Usage: python3 script_name_v1.0.0.py [options]
"""

import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib" / "python"))

from skippy_logger import SkippyLogger
from skippy_validator import SkippyValidator
from skippy_errors import SkippyError

# Initialize
logger = SkippyLogger(__name__)
validator = SkippyValidator()

# Your code here...
```

---

## File Naming Conventions

### ⚠️ CRITICAL: Always Follow This Pattern

```bash
# Pattern: {descriptive_name}_v{MAJOR}.{MINOR}.{PATCH}.{extension}

# ✅ CORRECT:
scripts/backup/full_backup_v1.0.0.sh
scripts/wordpress/theme_updater_v2.1.0.sh
lib/python/skippy_validator_v1.0.0.py

# ❌ WRONG:
scripts/backup.sh
scripts/wp_update.sh
lib/validator.py
```

### Versioning Rules
- **MAJOR** (1.x.x): Breaking changes, incompatible API changes
- **MINOR** (x.1.x): New features, backward compatible
- **PATCH** (x.x.1): Bug fixes, minor improvements

### When to Increment
```bash
# Bug fix: v1.0.0 → v1.0.1
# New feature: v1.0.1 → v1.1.0
# Breaking change: v1.1.0 → v2.0.0
```

---

## Script Template

### Bash Script Template

```bash
#!/bin/bash
################################################################################
# Script Name: descriptive_name_v1.0.0.sh
# Version: 1.0.0
# Purpose: What does this script do?
# Usage: ./descriptive_name_v1.0.0.sh [options]
#
# Options:
#   --help              Show this help message
#   --verbose           Enable verbose output
#   --dry-run           Show what would be done without doing it
#
# Examples:
#   ./descriptive_name_v1.0.0.sh --verbose
#   ./descriptive_name_v1.0.0.sh --dry-run
#
# Exit Codes:
#   0 - Success
#   1 - General error
#   2 - Invalid arguments
#
# Dependencies:
#   - bash >= 4.0
#   - Required commands: jq, curl
#
# Author: Your Name
# Created: YYYY-MM-DD
# Modified: YYYY-MM-DD
################################################################################

set -euo pipefail

# Load libraries
if [[ -f "${SKIPPY_BASE_PATH}/config.env" ]]; then
    source "${SKIPPY_BASE_PATH}/config.env"
fi

source "${SKIPPY_BASE_PATH}/lib/bash/skippy_logging.sh"
source "${SKIPPY_BASE_PATH}/lib/bash/skippy_errors.sh"
source "${SKIPPY_BASE_PATH}/lib/bash/skippy_validation.sh"

# Configuration
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_VERSION="1.0.0"

# Options
VERBOSE=false
DRY_RUN=false

# Initialize
init_logging "/var/log/skippy/${SCRIPT_NAME}.log" "INFO"
setup_error_trap

#######################################
# Show help message
#######################################
show_help() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS]

Description of what this script does.

OPTIONS:
    --help              Show this help message
    --verbose           Enable verbose output
    --dry-run           Show what would be done
    --version           Show version

EXAMPLES:
    $SCRIPT_NAME --verbose
    $SCRIPT_NAME --dry-run

EOF
}

#######################################
# Main function
#######################################
main() {
    log_section "Script Name v${SCRIPT_VERSION}"

    # Your logic here
    log_info "Starting process..."

    # Example validation
    assert_command_exists "jq"

    # Example operation
    log_info "Performing operation..."

    log_success "Process completed successfully!"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --help)
            show_help
            exit 0
            ;;
        --verbose)
            VERBOSE=true
            LOG_LEVEL=$LOG_LEVEL_DEBUG
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --version)
            echo "$SCRIPT_VERSION"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit $ERR_INVALID_ARGUMENT
            ;;
    esac
done

# Run main function
main
```

---

## Testing Requirements

### ⚠️ ALL New Python Code MUST Have Tests

#### Test File Naming
```python
# For: lib/python/skippy_new_module.py
# Create: tests/unit/test_skippy_new_module.py

# For: scripts/automation/my_script_v1.0.0.py
# Create: tests/unit/test_my_script.py
```

#### Test Template

```python
"""
Unit tests for skippy_new_module
"""
import pytest
import sys
from pathlib import Path

# Add lib directory to path
lib_path = Path(__file__).parent.parent.parent / "lib" / "python"
sys.path.insert(0, str(lib_path))

from skippy_new_module import MyClass


@pytest.mark.unit
class TestMyClass:
    """Test cases for MyClass"""

    def test_initialization(self):
        """Test class can be initialized"""
        obj = MyClass()
        assert obj is not None

    def test_method_with_valid_input(self):
        """Test method with valid input"""
        obj = MyClass()
        result = obj.my_method("valid_input")
        assert result == "expected_output"

    def test_method_with_invalid_input(self):
        """Test method raises error with invalid input"""
        obj = MyClass()
        with pytest.raises(ValueError):
            obj.my_method("invalid_input")

    def test_method_with_edge_case(self, tmp_path):
        """Test method with edge case"""
        obj = MyClass()
        # Use tmp_path for file operations
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        result = obj.process_file(str(test_file))
        assert result == "expected"
```

#### Running Tests

```bash
# Run all tests
pytest

# Run only unit tests
pytest -m unit

# Run with coverage
pytest --cov

# Run specific test file
pytest tests/unit/test_skippy_logger.py

# Run specific test
pytest tests/unit/test_skippy_logger.py::TestSkippyLogger::test_logger_initialization
```

### Coverage Requirements
- **Overall**: 80% minimum
- **Critical components**: 90% minimum (security, backup, error handling)
- **New code**: 80% minimum

---

## Common Workflows

### Workflow 1: Adding a New Script

```bash
# 1. Create script with proper naming
touch scripts/category/my_new_script_v1.0.0.sh
chmod +x scripts/category/my_new_script_v1.0.0.sh

# 2. Use the template (see above)
# 3. Add to SCRIPT_INDEX.md (if it doesn't auto-update)
# 4. Test locally
./scripts/category/my_new_script_v1.0.0.sh --dry-run

# 5. Write tests (if Python)
# 6. Update documentation
# 7. Validate configuration
./scripts/utility/validate_config_v2.0.0.sh

# 8. Run tests
pytest

# 9. Commit with descriptive message
git add scripts/category/my_new_script_v1.0.0.sh
git commit -m "feat: Add new script for [purpose]"
```

### Workflow 2: Fixing a Bug

```bash
# 1. Identify the bug location
# 2. Write a failing test first (TDD)
# 3. Fix the bug
# 4. Verify test passes
pytest tests/unit/test_affected_module.py

# 5. Run full test suite
pytest

# 6. Update version (patch increment)
# Old: my_script_v1.0.0.sh
# New: my_script_v1.0.1.sh

# 7. Commit
git commit -m "fix: [description] (closes #issue)"
```

### Workflow 3: Adding a Feature

```bash
# 1. Check if similar functionality exists
grep -r "similar_function" scripts/

# 2. Design the feature
# 3. Write tests first (TDD)
# 4. Implement the feature
# 5. Update version (minor increment)
# Old: my_script_v1.0.1.sh
# New: my_script_v1.1.0.sh

# 6. Update documentation
# 7. Commit
git commit -m "feat: Add [feature description]"
```

---

## Where Things Are

### 🗂️ Directory Structure Quick Reference

```bash
skippy-system-manager/
│
├── 📁 lib/                          # Shared libraries
│   ├── bash/                        # ⭐ NEW! Use these libraries
│   │   ├── skippy_validation.sh    # Input validation
│   │   ├── skippy_logging.sh       # Logging system
│   │   └── skippy_errors.sh        # Error handling
│   └── python/                      # Python libraries
│       ├── skippy_logger.py         # Logger class
│       ├── skippy_validator.py      # Validator class
│       ├── skippy_errors.py         # Error classes
│       └── skippy_performance.py    # Performance utilities
│
├── 📁 scripts/                      # All automation scripts
│   ├── automation/                  # 27 scripts - Document scanning, etc.
│   ├── backup/                      # 9 scripts - Backup operations
│   ├── deployment/                  # Deployment automation
│   ├── maintenance/                 # System maintenance
│   ├── monitoring/                  # System monitoring
│   ├── security/                    # Security tools
│   ├── utility/                     # ⭐ NEW! Config validator, path scanner
│   ├── wordpress/                   # WordPress management
│   └── legacy_system_managers/      # ⚠️ Do not modify (legacy)
│
├── 📁 tests/                        # Test suite
│   ├── unit/                        # ⭐ NEW! Unit tests go here
│   ├── integration/                 # Integration tests
│   ├── conftest.py                  # Pytest fixtures
│   └── README.md                    # Testing documentation
│
├── 📁 mcp-servers/                  # MCP server
│   └── general-server/
│       ├── server.py                # Main MCP server (43+ tools)
│       └── .env                     # Configuration (gitignored)
│
├── 📁 documentation/                # All documentation
│   ├── protocols/                   # 16+ protocol documents
│   └── guides/                      # User guides
│
├── 📁 conversations/                # Session logs (180+)
│
├── 📄 config.env.example            # Configuration template
├── 📄 pytest.ini                    # ⭐ NEW! Pytest configuration
├── 📄 requirements.txt              # Python dependencies
├── 📄 requirements-test.txt         # Test dependencies
│
├── 📄 SECURITY_AUDIT_RESULTS.md     # ⭐ NEW! Security audit
├── 📄 IMPROVEMENT_RECOMMENDATIONS.md # ⭐ NEW! 29 improvements
├── 📄 IMPLEMENTATION_SUMMARY.md     # ⭐ NEW! What we did
└── 📄 CLAUDE_CODE_REFERENCE.md      # ⭐ THIS FILE!
```

### Finding Things

```bash
# Find a script by name
find scripts -name "*backup*" -type f

# Find scripts in a category
ls scripts/wordpress/

# Find all Python scripts
find scripts -name "*.py" | grep -v archive

# Search for a function
grep -r "function_name" scripts/ lib/

# Find all active scripts (not archived)
find scripts -type f \( -name "*.sh" -o -name "*.py" \) ! -path "*/archive/*"
```

---

## Pre-Commit Checklist

### ✅ Before Every Commit

```bash
# 1. Run validators
./scripts/utility/validate_config_v2.0.0.sh

# 2. Check for hardcoded paths (if you modified scripts)
./scripts/utility/fix_hardcoded_paths_v1.0.0.sh --report-only

# 3. Run tests (if Python code changed)
pytest

# 4. Check syntax
# For bash:
bash -n your_script.sh

# For python:
python3 -m py_compile your_script.py

# 5. Update version number if needed
# 6. Update documentation
# 7. Check git status
git status

# 8. Review your changes
git diff

# 9. Stage files
git add <files>

# 10. Commit with proper message
git commit -m "type: description"
```

### Commit Message Format

```bash
# Format: <type>: <description>
#
# Types:
#   feat:     New feature
#   fix:      Bug fix
#   docs:     Documentation only
#   style:    Code style (formatting, etc.)
#   refactor: Code refactoring
#   test:     Adding tests
#   chore:    Maintenance tasks

# Examples:
git commit -m "feat: Add backup encryption support"
git commit -m "fix: Correct path validation in uploader"
git commit -m "docs: Update configuration guide"
git commit -m "test: Add unit tests for validator"
```

---

## Common Mistakes to Avoid

### ❌ DON'T Do These Things

1. **Hardcoded Paths**
   ```bash
   # ❌ WRONG:
   backup_dir="/home/dave/backups"

   # ✅ CORRECT:
   backup_dir="${SKIPPY_BACKUP_PATH}/backups"
   ```

2. **No Input Validation**
   ```bash
   # ❌ WRONG:
   rm -rf "$user_input"

   # ✅ CORRECT:
   if safe_path=$(validate_path "$user_input"); then
       rm -rf "$safe_path"
   fi
   ```

3. **No Error Handling**
   ```bash
   # ❌ WRONG:
   curl https://example.com/file.tar.gz > file.tar.gz
   tar xzf file.tar.gz

   # ✅ CORRECT:
   if ! curl https://example.com/file.tar.gz > file.tar.gz; then
       log_error "Download failed"
       exit $ERR_NETWORK_ERROR
   fi

   if ! tar xzf file.tar.gz; then
       log_error "Extraction failed"
       exit $ERR_GENERAL
   fi
   ```

4. **Shell=True in Python**
   ```python
   # ❌ WRONG:
   subprocess.run(f"rm {filename}", shell=True)

   # ✅ CORRECT:
   subprocess.run(["rm", filename])
   # Or even better:
   Path(filename).unlink()
   ```

5. **No Tests**
   ```python
   # ❌ WRONG: Add new function without tests

   # ✅ CORRECT: Always write tests
   # 1. Write test first (TDD)
   # 2. Implement function
   # 3. Verify test passes
   ```

6. **Ignoring Existing Libraries**
   ```bash
   # ❌ WRONG: Recreate logging functionality
   echo "[INFO] Starting process..."

   # ✅ CORRECT: Use existing library
   source "${SKIPPY_BASE_PATH}/lib/bash/skippy_logging.sh"
   log_info "Starting process..."
   ```

7. **Wrong File Naming**
   ```bash
   # ❌ WRONG:
   scripts/backup.sh
   scripts/wp-update.sh

   # ✅ CORRECT:
   scripts/backup/full_backup_v1.0.0.sh
   scripts/wordpress/update_wordpress_v1.0.0.sh
   ```

8. **Modifying Legacy Code**
   ```bash
   # ❌ WRONG: Edit files in legacy_system_managers/

   # ✅ CORRECT: Create new version in appropriate directory
   cp scripts/legacy_system_managers/old_script.sh scripts/category/new_script_v1.0.0.sh
   # Then modify new_script_v1.0.0.sh
   ```

---

## Quick Commands

### Development

```bash
# Validate configuration
./scripts/utility/validate_config_v2.0.0.sh

# Check for hardcoded paths
./scripts/utility/fix_hardcoded_paths_v1.0.0.sh --report-only

# Scan dependencies
python3 scripts/utility/scan_dependencies_v1.0.0.py --all-categories

# Run tests
pytest                              # All tests
pytest -m unit                      # Unit tests only
pytest -m integration               # Integration tests only
pytest --cov                        # With coverage
pytest -v                           # Verbose

# Check coverage
pytest --cov --cov-report=html
open htmlcov/index.html             # View coverage report
```

### Git Operations

```bash
# Create feature branch
git checkout -b feature/my-feature

# Stage changes
git add <files>

# Commit with message
git commit -m "type: description"

# Push to remote
git push -u origin feature/my-feature

# Check status
git status
git diff                            # Unstaged changes
git diff --cached                   # Staged changes
```

### SSH Key Migration

```bash
# Generate SSH keys
./scripts/utility/ssh_key_migration_guide_v1.0.0.sh --generate

# Install on server
./scripts/utility/ssh_key_migration_guide_v1.0.0.sh --install

# Test connection
./scripts/utility/ssh_key_migration_guide_v1.0.0.sh --test
```

### Finding Information

```bash
# List all scripts in a category
ls scripts/wordpress/

# Search for a pattern
grep -r "pattern" scripts/

# Find script by name
find scripts -name "*backup*"

# Count scripts by type
find scripts -name "*.sh" | wc -l   # Bash scripts
find scripts -name "*.py" | wc -l   # Python scripts

# View script documentation
head -50 scripts/path/to/script.sh  # Read header comments
```

---

## Environment Variables

### Required Variables (Must be set)

```bash
export SKIPPY_BASE_PATH="/path/to/skippy"
export WORDPRESS_BASE_PATH="/path/to/wordpress"
```

### Optional Variables (With defaults)

```bash
# Paths
export SKIPPY_SCRIPTS_PATH="${SKIPPY_BASE_PATH}/scripts"
export SKIPPY_CONVERSATIONS_PATH="${SKIPPY_BASE_PATH}/conversations"
export SKIPPY_PROTOCOLS_PATH="${SKIPPY_BASE_PATH}/documentation/protocols"
export SKIPPY_BACKUP_PATH="${SKIPPY_BASE_PATH}/backups"

# Remote server
export EBON_HOST="user@hostname"
export EBON_PORT="22"
export SSH_PRIVATE_KEY="${HOME}/.ssh/id_rsa_skippy"

# WordPress
export WP_SITE_URL="https://yoursite.com"

# Logging
export LOG_LEVEL="INFO"
export SKIPPY_LOG_FILE="/var/log/skippy/main.log"

# Alerts
export ALERT_EMAIL_TO="admin@example.com"
export WEBHOOK_URL="https://hooks.example.com/webhook"
```

---

## Library Function Quick Reference

### Validation Library

```bash
source "${SKIPPY_BASE_PATH}/lib/bash/skippy_validation.sh"

# Path validation
safe_path=$(validate_path "$user_input")

# Filename validation
safe_filename=$(validate_filename "$filename")

# URL validation
safe_url=$(validate_url "$url")

# Email validation
safe_email=$(validate_email "$email")

# IP validation
safe_ip=$(validate_ip "$ip_address")

# Port validation
safe_port=$(validate_port "$port")

# Integer validation
safe_int=$(validate_integer "$number" 0 100)  # min=0, max=100

# Boolean validation
bool_value=$(validate_boolean "$input")  # Returns "true" or "false"

# File/directory checks
validate_file_exists "$filepath"
validate_directory_exists "$dirpath"
```

### Logging Library

```bash
source "${SKIPPY_BASE_PATH}/lib/bash/skippy_logging.sh"

# Initialize (optional)
init_logging "/var/log/skippy/script.log" "INFO"

# Log messages
log_debug "Debug message"
log_info "Info message"
log_warn "Warning message"
log_error "Error message"
log_fatal "Fatal error message"
log_success "Success message"

# Log sections
log_section "Section Name"

# Progress bar
for i in {1..100}; do
    log_progress $i 100 "Processing"
    sleep 0.1
done
```

### Error Handling Library

```bash
source "${SKIPPY_BASE_PATH}/lib/bash/skippy_errors.sh"

# Setup automatic error handling
setup_error_trap

# Handle errors manually
handle_error $ERR_FILE_NOT_FOUND "File not found: $file" $LINENO

# Assertions
assert_command_exists "git"
assert_file_exists "$config_file"
assert_directory_exists "$backup_dir"
assert_not_empty "$VARIABLE" "VARIABLE"

# Retry commands
retry_command "curl https://example.com" 3 2  # 3 retries, 2s initial delay

# Error tracking
echo "Errors: $(get_error_count)"
if has_errors; then
    echo "Script encountered errors"
fi
```

---

## Decision Trees

### When to Create a New Script vs. Modify Existing?

```
Is the functionality similar to an existing script?
├─ YES → Is the existing script in active use?
│  ├─ YES → Create new version (increment version number)
│  └─ NO → Can modify if in archive/, otherwise create new
└─ NO → Create entirely new script with v1.0.0
```

### Which Directory Should My Script Go In?

```
What does your script do?
├─ Backup/restore operations → scripts/backup/
├─ WordPress management → scripts/wordpress/
├─ System monitoring → scripts/monitoring/
├─ Security scanning → scripts/security/
├─ Network operations → scripts/network/
├─ Deployment tasks → scripts/deployment/
├─ System maintenance → scripts/maintenance/
├─ Document processing → scripts/automation/
├─ Utility functions → scripts/utility/
└─ Testing → scripts/testing/ (or tests/ for unit tests)
```

### When to Write Tests?

```
Did you write Python code?
├─ YES → MUST write unit tests (target 80% coverage)
└─ NO → Is it a critical operation? (security, backup, data)
    ├─ YES → SHOULD write integration tests
    └─ NO → Optional but encouraged
```

---

## Code Review Checklist

When reviewing code (or reviewing your own), check:

### Functionality
- [ ] Does it solve the stated problem?
- [ ] Are edge cases handled?
- [ ] Is error handling comprehensive?

### Security
- [ ] Input validation for all user inputs?
- [ ] No hardcoded credentials?
- [ ] No shell=True in subprocess calls?
- [ ] Path traversal prevention?
- [ ] SQL injection prevention (if applicable)?

### Code Quality
- [ ] Uses standard libraries (validation, logging, errors)?
- [ ] Follows naming conventions?
- [ ] Proper version number?
- [ ] Comprehensive comments and docstrings?
- [ ] No code duplication?

### Testing
- [ ] Unit tests written (for Python)?
- [ ] Tests pass locally?
- [ ] Coverage meets minimum (80%)?

### Documentation
- [ ] Header comment block complete?
- [ ] Usage examples provided?
- [ ] README updated (if needed)?
- [ ] CHANGELOG updated (if needed)?

### Git
- [ ] Commit message follows format?
- [ ] No sensitive data in commit?
- [ ] Reasonable commit size (not too large)?

---

## Troubleshooting

### "Library not found" Error

```bash
# Problem: source: lib/bash/skippy_validation.sh: No such file or directory

# Solution: Set SKIPPY_BASE_PATH
export SKIPPY_BASE_PATH="/path/to/skippy-system-manager"
source "${SKIPPY_BASE_PATH}/lib/bash/skippy_validation.sh"
```

### "pytest: command not found"

```bash
# Install test dependencies
pip install -r requirements-test.txt
```

### "Import Error" in Python Tests

```bash
# Add lib to Python path
export PYTHONPATH="${SKIPPY_BASE_PATH}/lib/python:$PYTHONPATH"
pytest
```

### Configuration Validation Fails

```bash
# Run validator to see what's wrong
./scripts/utility/validate_config_v2.0.0.sh

# Fix issues, then re-run
```

---

## Advanced Topics

### Adding a New MCP Tool

1. Edit `mcp-servers/general-server/server.py`
2. Add new tool function with `@mcp.tool()` decorator
3. Include comprehensive docstring
4. Add input validation
5. Add error handling
6. Update tool count in file header
7. Test tool locally
8. Document in MCP server README

### Creating a New Protocol

1. Create file: `documentation/protocols/new_protocol_v1.0.0.md`
2. Use existing protocol as template
3. Include: Context, Guidelines, Examples, Related protocols
4. Link from other relevant protocols
5. Update protocol index

### Integrating with External Systems

When integrating with external systems:
1. Store credentials in config.env (gitignored)
2. Never hardcode credentials
3. Use environment variables
4. Add connection validation
5. Implement retry logic
6. Add comprehensive error messages

---

## Resources

### Documentation Files
- `README.md` - Project overview
- `PROJECT_ARCHITECTURE.md` - System architecture
- `SECURITY_AUDIT_RESULTS.md` - Security audit
- `IMPROVEMENT_RECOMMENDATIONS.md` - 29 improvements
- `IMPLEMENTATION_SUMMARY.md` - What was implemented
- `CONTRIBUTING.md` - Contribution guidelines

### Key Scripts
- `scripts/utility/validate_config_v2.0.0.sh` - Config validator
- `scripts/utility/fix_hardcoded_paths_v1.0.0.sh` - Path scanner
- `scripts/utility/ssh_key_migration_guide_v1.0.0.sh` - SSH setup
- `scripts/utility/scan_dependencies_v1.0.0.py` - Dependency scanner

### Testing
- `pytest.ini` - Pytest configuration
- `tests/conftest.py` - Test fixtures
- `requirements-test.txt` - Test dependencies

---

## Quick Tips for Claude Code

### When Starting a New Task

1. **Read this file first** - You're doing that now! ✅
2. **Check existing code** - Don't reinvent the wheel
3. **Use standard libraries** - validation, logging, errors
4. **Follow conventions** - naming, structure, versioning
5. **Write tests** - TDD when possible
6. **Update docs** - Keep documentation current

### When Stuck

1. **Search existing code**: `grep -r "similar_pattern" scripts/`
2. **Check protocols**: `ls documentation/protocols/`
3. **Read tests**: `cat tests/unit/test_*.py` for examples
4. **Run validators**: `./scripts/utility/validate_config_v2.0.0.sh`
5. **Check this file**: You're in the right place!

### Quality Mantras

- ✅ **Validate all inputs** - Use validation library
- ✅ **Log everything** - Use logging library
- ✅ **Handle errors gracefully** - Use error library
- ✅ **Test thoroughly** - Write unit tests
- ✅ **Document completely** - Future you will thank you

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-10 | Initial version - Comprehensive Claude Code reference |

---

## Questions?

If you encounter something not covered in this guide:
1. Check `IMPLEMENTATION_SUMMARY.md` for recent changes
2. Check `IMPROVEMENT_RECOMMENDATIONS.md` for planned work
3. Check protocol files in `documentation/protocols/`
4. Check existing similar scripts for patterns
5. When in doubt, ask the human! 🙂

---

**Remember**: This guide is your friend. Refer to it often!

**Happy coding!** 🚀

---

**Last Updated**: 2025-11-10
**Maintained By**: Skippy Development Team
**For**: Claude Code and AI Assistants
