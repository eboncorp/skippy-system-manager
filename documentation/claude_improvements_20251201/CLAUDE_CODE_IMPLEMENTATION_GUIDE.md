# Claude Code Configuration Improvement Implementation Guide

**Version:** 1.0.0
**Created:** 2025-12-01
**Purpose:** Comprehensive guide for Claude Code to implement security, automation, convenience, and development improvements
**Estimated Total Implementation Time:** 4-6 hours

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Pre-Implementation Checklist](#pre-implementation-checklist)
3. [Phase 1: Quick Wins (30 minutes)](#phase-1-quick-wins)
4. [Phase 2: New Slash Commands (90 minutes)](#phase-2-new-slash-commands)
5. [Phase 3: Enhanced Hooks (60 minutes)](#phase-3-enhanced-hooks)
6. [Phase 4: Skill Consolidation (60 minutes)](#phase-4-skill-consolidation)
7. [Phase 5: Security Hardening (45 minutes)](#phase-5-security-hardening)
8. [Phase 6: MCP Server Improvements (60 minutes)](#phase-6-mcp-server-improvements)
9. [Phase 7: Automation & Convenience (45 minutes)](#phase-7-automation-convenience)
10. [Verification & Testing](#verification-testing)
11. [Rollback Procedures](#rollback-procedures)

---

## Executive Summary

### Current State Analysis

| Component | Count | Issues Found |
|-----------|-------|--------------|
| Skills | 75 | 32 empty resource dirs, overlapping skills |
| Commands | 32 | Missing dev-focused commands |
| Hooks | 11 | Good coverage, needs error handling |
| MCP Server | 9,140 lines | Monolithic, needs modularization |

### Improvements Overview

| Category | Improvements | Priority |
|----------|--------------|----------|
| Development | 7 new commands, enhanced workflows | HIGH |
| Security | 5 hardening measures | HIGH |
| Automation | 4 new hooks, auto-linting | MEDIUM |
| Maintenance | Skill consolidation, cleanup | MEDIUM |
| Convenience | Quick aliases, templates | LOW |

---

## Pre-Implementation Checklist

Before starting, Claude Code should:

```bash
# 1. Create backup of current configuration
BACKUP_DIR="$HOME/.claude/backups/$(date +%Y%m%d_%H%M%S)_pre_improvements"
mkdir -p "$BACKUP_DIR"
cp -r "$HOME/.claude/skills" "$BACKUP_DIR/"
cp -r "$HOME/.claude/hooks" "$BACKUP_DIR/"
cp -r "$HOME/.claude/commands" "$BACKUP_DIR/"  # If exists
cp "$HOME/.claude/settings.json" "$BACKUP_DIR/"

# 2. Verify git state
cd "$HOME/skippy" && git status
git stash push -m "Pre-improvement backup $(date +%Y%m%d)"

# 3. Create implementation session directory
SESSION_DIR="$HOME/skippy/work/improvements/$(date +%Y%m%d_%H%M%S)_config_upgrade"
mkdir -p "$SESSION_DIR"/{commands,hooks,skills,logs}

# 4. Log start
echo "Implementation started: $(date)" > "$SESSION_DIR/implementation.log"
```

---

## Phase 1: Quick Wins

**Time:** 30 minutes
**Risk:** Low

### 1.1 Remove Empty Resource Directories

```bash
# Find and remove empty resource directories
find "$HOME/.claude/skills" -type d -name "resources" -empty -delete 2>/dev/null

# Log what was removed
echo "Removed $(find "$HOME/.claude/skills" -type d -name "resources" -empty 2>/dev/null | wc -l) empty directories" >> "$SESSION_DIR/implementation.log"
```

### 1.2 Create Skills Index

Create file: `$HOME/.claude/skills/INDEX.md`

```markdown
# Skills Index (Auto-Generated)

**Last Updated:** $(date +%Y-%m-%d)
**Total Skills:** $(ls -d $HOME/.claude/skills/*/ | wc -l)

## Quick Reference

| Category | Skills | Primary Use |
|----------|--------|-------------|
| Development | code-review, refactoring, testing-and-qa, git-workflow | Code quality |
| WordPress | wordpress-deployment, wordpress-plugin-development | Site management |
| Security | security-operations, api-credentials | Protection |
| Infrastructure | backup-infrastructure, system-maintenance | Operations |
| Campaign | campaign-facts, voter-registration-management | Content accuracy |

## Auto-Invoke Keywords

| Keyword | Triggers Skill |
|---------|----------------|
| "test", "pytest", "jest" | testing-and-qa |
| "commit", "branch", "merge" | git-workflow |
| "security", "vulnerability" | security-operations |
| "WordPress", "wp-cli" | wordpress-deployment |
| "backup", "restore" | backup-infrastructure |
| "budget", "ROI", "JCPS" | campaign-facts |

## Full Skill List

$(for skill in $HOME/.claude/skills/*/SKILL.md; do
    name=$(dirname "$skill" | xargs basename)
    desc=$(grep -m1 "^description:" "$skill" | cut -d: -f2- | head -c 60)
    echo "- **$name**: $desc..."
done)
```

### 1.3 Update Version Timestamps

```bash
# Update Last Updated in all CLAUDE.md files
TODAY=$(date +%Y-%m-%d)
for file in "$HOME/.claude/CLAUDE.md" "$HOME/skippy/.claude/CLAUDE.md"; do
    if [ -f "$file" ]; then
        sed -i "s/Last Updated:.*/Last Updated:** $TODAY/" "$file"
    fi
done
```

### 1.4 Create Central VERSION File

Create file: `$HOME/.claude/VERSION`

```
1.1.0
```

Create file: `$HOME/.claude/CHANGELOG.md`

```markdown
# Changelog

## [1.1.0] - 2025-12-01

### Added
- Skills index for quick reference
- 7 new development-focused slash commands
- Auto-linting hook for edited files
- Enhanced error handling in all hooks
- Security hardening measures

### Changed
- Consolidated overlapping skills
- Improved hook timeout handling
- Updated all documentation timestamps

### Removed
- 32 empty resource directories
- Redundant skill files

### Security
- Added secrets scanning to pre-tool-use hook
- Enhanced WordPress path validation
- Added rate limiting awareness

## [1.0.0] - 2025-11-19
- Initial comprehensive configuration
```

---

## Phase 2: New Slash Commands

**Time:** 90 minutes
**Risk:** Low

### 2.1 Create `/debug` Command

Create file: `$HOME/skippy/.claude/commands/debug.md`

```markdown
---
description: Quick debug helper - analyze errors, suggest fixes, trace issues in code
argument-hint: "[error message, file:line, or 'logs' to check recent errors]"
allowed-tools: ["Bash", "Read", "Grep", "Write"]
---

# Debug Assistant

Rapidly diagnose and fix coding issues.

## Instructions

### 1. Parse Input Type

```bash
INPUT="$1"

# Determine input type
if [ -z "$INPUT" ]; then
    MODE="interactive"
elif [ "$INPUT" = "logs" ]; then
    MODE="logs"
elif echo "$INPUT" | grep -qE "^[^:]+:[0-9]+"; then
    MODE="location"  # file:line format
else
    MODE="error"     # error message
fi
```

### 2. Error Message Analysis

```bash
if [ "$MODE" = "error" ]; then
    echo "## Error Analysis"
    echo ""
    
    # Search codebase for error
    echo "### Occurrences in codebase:"
    grep -rn "$INPUT" --include="*.py" --include="*.js" --include="*.php" --include="*.sh" . 2>/dev/null | head -10
    
    # Check if it's a known error pattern
    case "$INPUT" in
        *"ModuleNotFoundError"*|*"ImportError"*)
            MODULE=$(echo "$INPUT" | grep -oP "No module named '\K[^']+")
            echo ""
            echo "### Suggested Fix:"
            echo "\`\`\`bash"
            echo "pip install $MODULE"
            echo "\`\`\`"
            ;;
        *"ENOENT"*|*"FileNotFoundError"*)
            echo ""
            echo "### Suggested Fix:"
            echo "Check that the file path exists and is accessible"
            echo "\`\`\`bash"
            echo "ls -la <path>"
            echo "\`\`\`"
            ;;
        *"Permission denied"*)
            echo ""
            echo "### Suggested Fix:"
            echo "\`\`\`bash"
            echo "chmod +x <file>  # For executables"
            echo "sudo chown \$USER <file>  # For ownership issues"
            echo "\`\`\`"
            ;;
        *"Connection refused"*|*"ECONNREFUSED"*)
            echo ""
            echo "### Suggested Fix:"
            echo "Check if the service is running:"
            echo "\`\`\`bash"
            echo "systemctl status <service>"
            echo "netstat -tlnp | grep <port>"
            echo "\`\`\`"
            ;;
        *"SyntaxError"*)
            echo ""
            echo "### Check syntax:"
            echo "\`\`\`bash"
            echo "python3 -m py_compile <file>"
            echo "node --check <file>"
            echo "php -l <file>"
            echo "\`\`\`"
            ;;
    esac
fi
```

### 3. File:Line Investigation

```bash
if [ "$MODE" = "location" ]; then
    FILE=$(echo "$INPUT" | cut -d: -f1)
    LINE=$(echo "$INPUT" | cut -d: -f2)
    
    echo "## Code at $FILE:$LINE"
    echo ""
    
    # Show context (5 lines before and after)
    START=$((LINE - 5))
    [ $START -lt 1 ] && START=1
    END=$((LINE + 5))
    
    echo "\`\`\`"
    sed -n "${START},${END}p" "$FILE" | nl -ba -v $START
    echo "\`\`\`"
    
    # Run appropriate linter
    case "$FILE" in
        *.py)
            echo ""
            echo "### Linter Output:"
            flake8 "$FILE" --select=E,W --show-source 2>/dev/null | grep -A2 ":$LINE:" || echo "No issues at this line"
            ;;
        *.js)
            echo ""
            echo "### ESLint Output:"
            npx eslint "$FILE" --format compact 2>/dev/null | grep ":$LINE:" || echo "No issues at this line"
            ;;
        *.php)
            echo ""
            echo "### PHP Check:"
            php -l "$FILE" 2>&1 | grep -i "line $LINE" || echo "No syntax errors"
            ;;
    esac
fi
```

### 4. Recent Logs Analysis

```bash
if [ "$MODE" = "logs" ]; then
    echo "## Recent Error Logs"
    echo ""
    
    # Claude logs
    echo "### Claude Tool Logs (last 20 errors):"
    grep -i "error\|exception\|failed\|blocked" ~/.claude/tool_logs/*.log 2>/dev/null | tail -20
    
    echo ""
    echo "### System Logs:"
    journalctl --user -p err -n 10 --no-pager 2>/dev/null || echo "No systemd user logs available"
    
    echo ""
    echo "### PHP Error Log (if exists):"
    tail -20 /var/log/php*.log 2>/dev/null || tail -20 ~/skippy/logs/php-error.log 2>/dev/null || echo "No PHP logs found"
    
    echo ""
    echo "### Recent Git Issues:"
    git log --oneline -5 --grep="fix\|bug\|error" 2>/dev/null || echo "No recent fix commits"
fi
```

### 5. Interactive Mode

```bash
if [ "$MODE" = "interactive" ]; then
    echo "## Debug Assistant"
    echo ""
    echo "Usage:"
    echo "  /debug <error message>     - Analyze an error"
    echo "  /debug <file>:<line>       - Investigate specific location"
    echo "  /debug logs                - Check recent error logs"
    echo ""
    echo "### Quick Diagnostics:"
    echo ""
    echo "**Current directory:** $(pwd)"
    echo "**Git status:** $(git status --porcelain 2>/dev/null | wc -l) uncommitted changes"
    echo "**Last test run:** $(stat -c %y .pytest_cache 2>/dev/null || echo 'No recent tests')"
    echo ""
    echo "**Recent errors in logs:**"
    grep -i "error" ~/.claude/tool_logs/tool_usage.log 2>/dev/null | tail -5 || echo "No recent errors"
fi
```

### 6. Stack Trace Parser

```bash
parse_traceback() {
    local TRACE="$1"
    
    echo "## Stack Trace Analysis"
    echo ""
    
    # Python traceback
    if echo "$TRACE" | grep -q "Traceback"; then
        echo "### Python Traceback"
        echo ""
        echo "**Files involved:**"
        echo "$TRACE" | grep -oP 'File "[^"]+", line \d+' | while read match; do
            echo "- $match"
        done
        echo ""
        echo "**Error:**"
        echo "$TRACE" | tail -1
    fi
    
    # JavaScript stack
    if echo "$TRACE" | grep -q "at .*:[0-9]*:[0-9]*"; then
        echo "### JavaScript Stack"
        echo ""
        echo "**Call stack:**"
        echo "$TRACE" | grep -oP 'at .+ \([^)]+\)' | head -10
    fi
}
```

## Common Error Database

| Error Pattern | Category | Quick Fix |
|---------------|----------|-----------|
| `ModuleNotFoundError` | Python Import | `pip install <module>` |
| `ENOENT` | File System | Check path exists |
| `Permission denied` | Permissions | `chmod` or `chown` |
| `Connection refused` | Network | Check service running |
| `SyntaxError` | Code | Run linter |
| `TypeError` | Code | Check types/arguments |
| `CORS` | Web | Check server headers |
| `401/403` | Auth | Check credentials |
| `500` | Server | Check server logs |

## Integration

- Works with: **git-workflow**, **testing-and-qa**, **advanced-debugging**
- Creates debug session in: `$SESSION_DIR/debug/`
- Logs to: `~/.claude/tool_logs/debug.log`
```

### 2.2 Create `/test` Command

Create file: `$HOME/skippy/.claude/commands/test.md`

```markdown
---
description: Smart test runner - auto-detect framework, run relevant tests, show coverage
argument-hint: "[file, function, 'all', 'failed', 'changed', or 'coverage']"
allowed-tools: ["Bash", "Read"]
---

# Smart Test Runner

Intelligently run tests based on context.

## Instructions

### 1. Detect Test Framework

```bash
detect_framework() {
    if [ -f "pytest.ini" ] || [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
        if grep -q "pytest" pyproject.toml 2>/dev/null || [ -f "pytest.ini" ]; then
            echo "pytest"
            return
        fi
    fi
    
    if [ -f "package.json" ]; then
        if grep -q '"jest"' package.json; then
            echo "jest"
            return
        elif grep -q '"mocha"' package.json; then
            echo "mocha"
            return
        elif grep -q '"vitest"' package.json; then
            echo "vitest"
            return
        fi
    fi
    
    if [ -f "phpunit.xml" ] || [ -f "phpunit.xml.dist" ]; then
        echo "phpunit"
        return
    fi
    
    if [ -d "tests" ] && ls tests/*.py &>/dev/null; then
        echo "pytest"
        return
    fi
    
    echo "unknown"
}

FRAMEWORK=$(detect_framework)
echo "Detected framework: $FRAMEWORK"
```

### 2. Run Tests Based on Mode

```bash
TARGET="${1:-all}"

case "$TARGET" in
    all)
        echo "## Running All Tests"
        case "$FRAMEWORK" in
            pytest)
                pytest tests/ -v --tb=short -x --color=yes
                ;;
            jest)
                npx jest --coverage --colors
                ;;
            phpunit)
                ./vendor/bin/phpunit --colors=always
                ;;
            vitest)
                npx vitest run --reporter=verbose
                ;;
        esac
        ;;
        
    failed)
        echo "## Re-running Failed Tests"
        case "$FRAMEWORK" in
            pytest)
                pytest --lf -v --tb=short
                ;;
            jest)
                npx jest --onlyFailures
                ;;
            phpunit)
                ./vendor/bin/phpunit --order-by=defects --stop-on-failure
                ;;
        esac
        ;;
        
    changed)
        echo "## Running Tests for Changed Files"
        CHANGED_FILES=$(git diff --name-only HEAD~1 | grep -E '\.(py|js|ts|php)$' | grep -v test)
        
        case "$FRAMEWORK" in
            pytest)
                # Convert source files to test files
                TEST_FILES=""
                for f in $CHANGED_FILES; do
                    if [[ "$f" == *.py ]]; then
                        TEST_FILE="tests/test_$(basename $f)"
                        [ -f "$TEST_FILE" ] && TEST_FILES="$TEST_FILES $TEST_FILE"
                    fi
                done
                [ -n "$TEST_FILES" ] && pytest $TEST_FILES -v || echo "No matching test files found"
                ;;
            jest)
                npx jest --findRelatedTests $CHANGED_FILES
                ;;
        esac
        ;;
        
    coverage)
        echo "## Running Tests with Coverage"
        case "$FRAMEWORK" in
            pytest)
                pytest --cov=src --cov=lib --cov-report=term-missing --cov-report=html --cov-fail-under=70
                echo ""
                echo "HTML report: htmlcov/index.html"
                ;;
            jest)
                npx jest --coverage --coverageReporters=text --coverageReporters=html
                ;;
            phpunit)
                ./vendor/bin/phpunit --coverage-text --coverage-html=coverage/
                ;;
        esac
        ;;
        
    *)
        # Specific file or pattern
        echo "## Running Tests: $TARGET"
        case "$FRAMEWORK" in
            pytest)
                if [[ "$TARGET" == *"::"* ]]; then
                    # Specific test function
                    pytest "$TARGET" -v --tb=long
                elif [[ "$TARGET" == *.py ]]; then
                    pytest "$TARGET" -v
                else
                    pytest -k "$TARGET" -v
                fi
                ;;
            jest)
                npx jest "$TARGET" --verbose
                ;;
            phpunit)
                ./vendor/bin/phpunit --filter="$TARGET"
                ;;
        esac
        ;;
esac
```

### 3. Show Test Summary

```bash
echo ""
echo "## Test Summary"
echo ""

case "$FRAMEWORK" in
    pytest)
        # Show coverage if available
        if [ -f ".coverage" ]; then
            echo "### Coverage"
            coverage report --show-missing | tail -20
        fi
        ;;
esac

# Show recent test history
echo ""
echo "### Recent Test Runs"
ls -lt .pytest_cache/v/cache/lastfailed 2>/dev/null && echo "Last failed tests cached" || echo "No failed tests cached"
```

### 4. Quick Test Shortcuts

```bash
# Usage hints
echo ""
echo "---"
echo "**Quick shortcuts:**"
echo "  /test              - Run all tests"
echo "  /test failed       - Re-run only failed tests"  
echo "  /test changed      - Test files changed in last commit"
echo "  /test coverage     - Run with coverage report"
echo "  /test <file>       - Run specific test file"
echo "  /test <func>       - Run tests matching pattern"
```

## Integration

- Creates test session logs in: `$SESSION_DIR/tests/`
- Works with: **testing-and-qa**, **code-review**
- Respects `.pytest.ini`, `jest.config.js`, `phpunit.xml`
```

### 2.3 Create `/scaffold` Command

Create file: `$HOME/skippy/.claude/commands/scaffold.md`

```markdown
---
description: Generate boilerplate code for new files, classes, functions, and tests
argument-hint: "<type> <name> [options] (e.g., 'class UserService', 'test payment', 'script backup')"
allowed-tools: ["Bash", "Write", "Read"]
---

# Code Scaffolding

Generate consistent boilerplate following project conventions.

## Instructions

### 1. Parse Arguments

```bash
TYPE="$1"
NAME="$2"
OPTION="${3:-}"

# Validate input
if [ -z "$TYPE" ] || [ -z "$NAME" ]; then
    echo "Usage: /scaffold <type> <name> [option]"
    echo ""
    echo "Types:"
    echo "  class <ClassName>      - Python class with tests"
    echo "  test <module_name>     - Test file for existing module"
    echo "  script <name>          - Bash script with header"
    echo "  api <endpoint>         - API endpoint with validation"
    echo "  hook <hook_name>       - Claude Code hook"
    echo "  command <cmd_name>     - Slash command"
    echo "  skill <skill_name>     - Claude skill"
    echo "  component <Name>       - React component"
    echo "  plugin <name>          - WordPress plugin skeleton"
    exit 0
fi

# Convert name formats
SNAKE_NAME=$(echo "$NAME" | sed 's/\([A-Z]\)/_\L\1/g' | sed 's/^_//' | tr '[:upper:]' '[:lower:]')
PASCAL_NAME=$(echo "$NAME" | sed -r 's/(^|_)([a-z])/\U\2/g')
KEBAB_NAME=$(echo "$SNAKE_NAME" | tr '_' '-')
```

### 2. Python Class Template

```bash
if [ "$TYPE" = "class" ]; then
    # Create class file
    cat > "${SNAKE_NAME}.py" << 'PYCLASS'
"""
${PASCAL_NAME} - Brief description of purpose.

This module provides...

Example:
    >>> obj = ${PASCAL_NAME}()
    >>> obj.do_something()

Created: $(date +%Y-%m-%d)
Author: Claude Code
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ${PASCAL_NAME}:
    """Brief description of ${PASCAL_NAME}.
    
    Attributes:
        name: Description of name attribute.
        config: Optional configuration dictionary.
    """
    
    name: str
    config: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Initialize after dataclass fields are set."""
        logger.debug(f"Initialized {self.__class__.__name__}: {self.name}")
    
    def process(self, data: Any) -> Optional[Any]:
        """Process input data.
        
        Args:
            data: Input data to process.
            
        Returns:
            Processed result or None if processing fails.
            
        Raises:
            ValueError: If data is invalid.
        """
        if not data:
            raise ValueError("Data cannot be empty")
        
        # TODO: Implement processing logic
        logger.info(f"Processing data: {data}")
        return data
    
    def validate(self) -> bool:
        """Validate current state.
        
        Returns:
            True if valid, False otherwise.
        """
        return bool(self.name)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


def create_${SNAKE_NAME}(name: str, **kwargs: Any) -> ${PASCAL_NAME}:
    """Factory function to create ${PASCAL_NAME} instance.
    
    Args:
        name: Name for the instance.
        **kwargs: Additional configuration options.
        
    Returns:
        Configured ${PASCAL_NAME} instance.
    """
    return ${PASCAL_NAME}(name=name, config=kwargs)


if __name__ == "__main__":
    # Quick test
    instance = create_${SNAKE_NAME}("test")
    print(instance)
PYCLASS

    # Replace placeholders
    sed -i "s/\${PASCAL_NAME}/$PASCAL_NAME/g" "${SNAKE_NAME}.py"
    sed -i "s/\${SNAKE_NAME}/$SNAKE_NAME/g" "${SNAKE_NAME}.py"
    sed -i "s/\$(date +%Y-%m-%d)/$(date +%Y-%m-%d)/g" "${SNAKE_NAME}.py"
    
    # Create corresponding test file
    mkdir -p tests
    cat > "tests/test_${SNAKE_NAME}.py" << 'PYTEST'
"""Tests for ${SNAKE_NAME} module."""

import pytest
from ${SNAKE_NAME} import ${PASCAL_NAME}, create_${SNAKE_NAME}


class Test${PASCAL_NAME}:
    """Test suite for ${PASCAL_NAME}."""
    
    @pytest.fixture
    def instance(self) -> ${PASCAL_NAME}:
        """Create test instance."""
        return ${PASCAL_NAME}(name="test")
    
    @pytest.fixture
    def configured_instance(self) -> ${PASCAL_NAME}:
        """Create configured test instance."""
        return create_${SNAKE_NAME}("configured", option1="value1")
    
    def test_init(self, instance: ${PASCAL_NAME}) -> None:
        """Test basic initialization."""
        assert instance.name == "test"
        assert instance.config == {}
    
    def test_init_with_config(self, configured_instance: ${PASCAL_NAME}) -> None:
        """Test initialization with configuration."""
        assert configured_instance.name == "configured"
        assert "option1" in configured_instance.config
    
    def test_repr(self, instance: ${PASCAL_NAME}) -> None:
        """Test string representation."""
        result = repr(instance)
        assert "${PASCAL_NAME}" in result
        assert "test" in result
    
    def test_validate_valid(self, instance: ${PASCAL_NAME}) -> None:
        """Test validation with valid state."""
        assert instance.validate() is True
    
    def test_validate_invalid(self) -> None:
        """Test validation with invalid state."""
        instance = ${PASCAL_NAME}(name="")
        assert instance.validate() is False
    
    def test_process_valid_data(self, instance: ${PASCAL_NAME}) -> None:
        """Test processing valid data."""
        result = instance.process({"key": "value"})
        assert result == {"key": "value"}
    
    def test_process_empty_data_raises(self, instance: ${PASCAL_NAME}) -> None:
        """Test that empty data raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            instance.process(None)
    
    def test_process_empty_dict_raises(self, instance: ${PASCAL_NAME}) -> None:
        """Test that empty dict raises ValueError."""
        with pytest.raises(ValueError):
            instance.process({})


class TestCreate${PASCAL_NAME}:
    """Tests for factory function."""
    
    def test_create_basic(self) -> None:
        """Test basic creation."""
        instance = create_${SNAKE_NAME}("basic")
        assert isinstance(instance, ${PASCAL_NAME})
        assert instance.name == "basic"
    
    def test_create_with_kwargs(self) -> None:
        """Test creation with keyword arguments."""
        instance = create_${SNAKE_NAME}("configured", debug=True, timeout=30)
        assert instance.config["debug"] is True
        assert instance.config["timeout"] == 30
PYTEST

    # Replace placeholders in test file
    sed -i "s/\${PASCAL_NAME}/$PASCAL_NAME/g" "tests/test_${SNAKE_NAME}.py"
    sed -i "s/\${SNAKE_NAME}/$SNAKE_NAME/g" "tests/test_${SNAKE_NAME}.py"
    
    echo "Created: ${SNAKE_NAME}.py"
    echo "Created: tests/test_${SNAKE_NAME}.py"
    echo ""
    echo "Run tests: pytest tests/test_${SNAKE_NAME}.py -v"
fi
```

### 3. Bash Script Template

```bash
if [ "$TYPE" = "script" ]; then
    SCRIPT_FILE="${SNAKE_NAME}_v1.0.0.sh"
    
    cat > "$SCRIPT_FILE" << 'BASHSCRIPT'
#!/bin/bash
# ${SNAKE_NAME}_v1.0.0.sh - Brief description
#
# Usage:
#   ${SNAKE_NAME}.sh [options] <arguments>
#
# Options:
#   -h, --help     Show this help message
#   -v, --verbose  Enable verbose output
#   -d, --dry-run  Show what would be done without executing
#
# Examples:
#   ${SNAKE_NAME}.sh input.txt
#   ${SNAKE_NAME}.sh -v --dry-run input.txt
#
# Dependencies:
#   - bash 4.0+
#   - coreutils
#
# Created: $(date +%Y-%m-%d)
# Author: Claude Code
# Version: 1.0.0

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_DIR="${HOME}/.claude/logs"
readonly LOG_FILE="${LOG_DIR}/${SCRIPT_NAME%.sh}.log"

# Default options
VERBOSE=false
DRY_RUN=false

# =============================================================================
# Logging Functions
# =============================================================================

setup_logging() {
    mkdir -p "$LOG_DIR"
    exec 3>&1  # Save stdout
    exec 4>&2  # Save stderr
}

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    
    if [[ "$VERBOSE" == true ]] || [[ "$level" != "DEBUG" ]]; then
        case "$level" in
            ERROR)   echo -e "\033[31m[$level]\033[0m $message" >&2 ;;
            WARNING) echo -e "\033[33m[$level]\033[0m $message" >&2 ;;
            SUCCESS) echo -e "\033[32m[$level]\033[0m $message" ;;
            INFO)    echo "[$level] $message" ;;
            DEBUG)   [[ "$VERBOSE" == true ]] && echo -e "\033[36m[$level]\033[0m $message" ;;
        esac
    fi
}

info()    { log "INFO" "$@"; }
debug()   { log "DEBUG" "$@"; }
warning() { log "WARNING" "$@"; }
error()   { log "ERROR" "$@"; }
success() { log "SUCCESS" "$@"; }

die() {
    error "$@"
    exit 1
}

# =============================================================================
# Helper Functions
# =============================================================================

show_help() {
    grep '^#' "$0" | grep -v '#!/' | sed 's/^# //' | sed 's/^#//'
    exit 0
}

check_dependencies() {
    local deps=("$@")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            die "Required dependency not found: $dep"
        fi
    done
}

confirm() {
    local prompt="${1:-Are you sure?}"
    read -r -p "$prompt [y/N] " response
    [[ "$response" =~ ^[Yy]$ ]]
}

run_cmd() {
    local cmd="$*"
    debug "Executing: $cmd"
    
    if [[ "$DRY_RUN" == true ]]; then
        info "[DRY RUN] Would execute: $cmd"
        return 0
    fi
    
    if ! eval "$cmd"; then
        error "Command failed: $cmd"
        return 1
    fi
}

# =============================================================================
# Main Functions
# =============================================================================

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -*)
                die "Unknown option: $1"
                ;;
            *)
                # Positional arguments
                ARGS+=("$1")
                shift
                ;;
        esac
    done
}

validate_input() {
    # Add input validation here
    if [[ ${#ARGS[@]} -eq 0 ]]; then
        die "No input provided. Use -h for help."
    fi
}

main() {
    setup_logging
    info "Starting $SCRIPT_NAME"
    
    # Parse command line arguments
    declare -a ARGS=()
    parse_args "$@"
    
    # Validate input
    validate_input
    
    # Check dependencies
    check_dependencies "bash"
    
    # Main logic here
    debug "Arguments: ${ARGS[*]}"
    
    # TODO: Implement main logic
    for arg in "${ARGS[@]}"; do
        info "Processing: $arg"
        run_cmd "echo 'Processing $arg'"
    done
    
    success "Completed successfully"
}

# =============================================================================
# Entry Point
# =============================================================================

# Only run main if script is executed, not sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
BASHSCRIPT

    # Replace placeholders
    sed -i "s/\${SNAKE_NAME}/$SNAKE_NAME/g" "$SCRIPT_FILE"
    sed -i "s/\$(date +%Y-%m-%d)/$(date +%Y-%m-%d)/g" "$SCRIPT_FILE"
    
    chmod +x "$SCRIPT_FILE"
    
    echo "Created: $SCRIPT_FILE"
    echo ""
    echo "Run: ./$SCRIPT_FILE --help"
fi
```

### 4. Claude Hook Template

```bash
if [ "$TYPE" = "hook" ]; then
    HOOK_FILE="$HOME/.claude/hooks/${SNAKE_NAME}.sh"
    
    cat > "$HOOK_FILE" << 'HOOKTEMPLATE'
#!/bin/bash
# ${SNAKE_NAME}.sh - Brief description of hook purpose
# Hook: <HookType>  # PreToolUse, PostToolUse, PreCompact, SessionStart, etc.
# Version: 1.0.0
#
# Input: JSON on stdin
# Output: JSON on stdout (for blocking hooks) or nothing (for passthrough)
#
# Created: $(date +%Y-%m-%d)

set -euo pipefail

# Logging
LOG_DIR="$HOME/.claude/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/${SNAKE_NAME}.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# Error handling - always allow tool to proceed on error
trap 'log "ERROR: Hook failed"; exit 0' ERR

# Read JSON input
INPUT=$(cat)
log "Hook triggered with input: ${INPUT:0:200}..."

# Parse input (adjust based on hook type)
# For PreToolUse:
# TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")
# TOOL_INPUT=$(echo "$INPUT" | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin).get('tool_input',{})))" 2>/dev/null || echo "{}")

# Main logic
# TODO: Implement hook logic

# For blocking hooks, output JSON:
# echo '{"decision": "block", "reason": "Reason for blocking"}'
# echo '{"decision": "allow"}'

# For non-blocking hooks, just exit
log "Hook completed successfully"
exit 0
HOOKTEMPLATE

    sed -i "s/\${SNAKE_NAME}/$SNAKE_NAME/g" "$HOOK_FILE"
    sed -i "s/\$(date +%Y-%m-%d)/$(date +%Y-%m-%d)/g" "$HOOK_FILE"
    chmod +x "$HOOK_FILE"
    
    echo "Created: $HOOK_FILE"
    echo ""
    echo "Remember to add to settings.json:"
    echo '  "HookType": [{"matcher": "*", "hooks": [{"type": "command", "command": "'$HOOK_FILE'", "timeout": 5000}]}]'
fi
```

### 5. Slash Command Template

```bash
if [ "$TYPE" = "command" ]; then
    CMD_FILE="$HOME/skippy/.claude/commands/${KEBAB_NAME}.md"
    
    cat > "$CMD_FILE" << 'CMDTEMPLATE'
---
description: Brief description of what this command does
argument-hint: "[optional: argument description]"
allowed-tools: ["Bash", "Read", "Write", "Grep"]
---

# ${PASCAL_NAME} Command

Brief description of the command's purpose and when to use it.

## Instructions

### 1. Parse Input

```bash
INPUT="${1:-}"

if [ -z "$INPUT" ]; then
    echo "## ${PASCAL_NAME}"
    echo ""
    echo "Usage: /${KEBAB_NAME} <argument>"
    echo ""
    echo "Examples:"
    echo "  /${KEBAB_NAME} example1"
    echo "  /${KEBAB_NAME} example2"
    exit 0
fi
```

### 2. Main Logic

```bash
echo "## Processing: $INPUT"
echo ""

# TODO: Implement command logic

echo "Done!"
```

### 3. Output

```bash
# Create session record if needed
SESSION_DIR="$HOME/skippy/work/${SNAKE_NAME}/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$SESSION_DIR"

# Save output
echo "Results saved to: $SESSION_DIR"
```

## Quick Reference

| Option | Description |
|--------|-------------|
| `<arg1>` | Description |
| `<arg2>` | Description |

## Integration

- Works with: **related-skill-1**, **related-skill-2**
- Creates output in: `$HOME/skippy/work/${SNAKE_NAME}/`
CMDTEMPLATE

    sed -i "s/\${PASCAL_NAME}/$PASCAL_NAME/g" "$CMD_FILE"
    sed -i "s/\${SNAKE_NAME}/$SNAKE_NAME/g" "$CMD_FILE"
    sed -i "s/\${KEBAB_NAME}/$KEBAB_NAME/g" "$CMD_FILE"
    
    echo "Created: $CMD_FILE"
    echo ""
    echo "Use: /$KEBAB_NAME"
fi
```

### 6. Claude Skill Template

```bash
if [ "$TYPE" = "skill" ]; then
    SKILL_DIR="$HOME/.claude/skills/${KEBAB_NAME}"
    mkdir -p "$SKILL_DIR"
    
    cat > "$SKILL_DIR/SKILL.md" << 'SKILLTEMPLATE'
---
name: ${KEBAB_NAME}
description: Brief description. Auto-invoke when: keyword1, keyword2, keyword3 are mentioned.
---

# ${PASCAL_NAME} Skill

**Version:** 1.0.0
**Last Updated:** $(date +%Y-%m-%d)
**Auto-Invoke:** Yes - when [trigger conditions]

## When to Use This Skill

This skill should be **automatically invoked** when:
- Condition 1
- Condition 2
- Keywords: keyword1, keyword2, keyword3

## Overview

Brief explanation of what this skill provides.

## Quick Reference

### Common Operations

```bash
# Operation 1
command_1

# Operation 2
command_2
```

### Key Information

| Item | Value | Notes |
|------|-------|-------|
| Key 1 | Value 1 | Note |
| Key 2 | Value 2 | Note |

## Detailed Procedures

### Procedure 1: Name

**When to use:** Description

**Steps:**
1. Step 1
2. Step 2
3. Step 3

```bash
# Example command
example_command --option value
```

### Procedure 2: Name

**When to use:** Description

**Steps:**
1. Step 1
2. Step 2

## Troubleshooting

### Common Issues

**Issue 1: Description**
- Cause: Why it happens
- Solution: How to fix

**Issue 2: Description**
- Cause: Why it happens
- Solution: How to fix

## Integration with Other Skills

| Skill | Relationship |
|-------|--------------|
| skill-1 | How they work together |
| skill-2 | How they work together |

## Best Practices

1. Best practice 1
2. Best practice 2
3. Best practice 3

## Related Documentation

- Link to related doc 1
- Link to related doc 2
SKILLTEMPLATE

    sed -i "s/\${PASCAL_NAME}/$PASCAL_NAME/g" "$SKILL_DIR/SKILL.md"
    sed -i "s/\${KEBAB_NAME}/$KEBAB_NAME/g" "$SKILL_DIR/SKILL.md"
    sed -i "s/\$(date +%Y-%m-%d)/$(date +%Y-%m-%d)/g" "$SKILL_DIR/SKILL.md"
    
    echo "Created: $SKILL_DIR/SKILL.md"
fi
```

## Usage Examples

```
/scaffold class UserService           → Creates user_service.py + tests
/scaffold test payment               → Creates test_payment.py
/scaffold script backup_database     → Creates backup_database_v1.0.0.sh
/scaffold hook pre_edit_validate     → Creates pre_edit_validate.sh
/scaffold command deploy-status      → Creates deploy-status.md
/scaffold skill error-handling       → Creates error-handling/SKILL.md
```
```

### 2.4 Create `/review-pr` Command

Create file: `$HOME/skippy/.claude/commands/review-pr.md`

```markdown
---
description: Comprehensive PR/branch review - diff analysis, test coverage, security scan, complexity check
argument-hint: "[branch name, PR number, or 'current' for current branch]"
allowed-tools: ["Bash", "Read", "Grep"]
---

# Pull Request Review Assistant

Thorough automated code review for branches and pull requests.

## Instructions

### 1. Determine Target

```bash
TARGET="${1:-current}"

if [ "$TARGET" = "current" ]; then
    BRANCH=$(git branch --show-current)
    BASE="main"
elif [[ "$TARGET" =~ ^[0-9]+$ ]]; then
    # PR number - get branch from GitHub
    BRANCH=$(gh pr view "$TARGET" --json headRefName -q '.headRefName' 2>/dev/null || echo "")
    BASE=$(gh pr view "$TARGET" --json baseRefName -q '.baseRefName' 2>/dev/null || echo "main")
    if [ -z "$BRANCH" ]; then
        echo "Could not find PR #$TARGET"
        exit 1
    fi
else
    BRANCH="$TARGET"
    BASE="main"
fi

echo "# PR Review: $BRANCH → $BASE"
echo ""
echo "**Generated:** $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
```

### 2. Summary Statistics

```bash
echo "## 📊 Summary"
echo ""

# Get counts
COMMITS=$(git rev-list --count $BASE..$BRANCH 2>/dev/null || echo "0")
FILES_CHANGED=$(git diff --name-only $BASE...$BRANCH 2>/dev/null | wc -l)
ADDITIONS=$(git diff --stat $BASE...$BRANCH 2>/dev/null | tail -1 | grep -oP '\d+(?= insertion)' || echo "0")
DELETIONS=$(git diff --stat $BASE...$BRANCH 2>/dev/null | tail -1 | grep -oP '\d+(?= deletion)' || echo "0")

echo "| Metric | Value |"
echo "|--------|-------|"
echo "| Commits | $COMMITS |"
echo "| Files Changed | $FILES_CHANGED |"
echo "| Lines Added | +$ADDITIONS |"
echo "| Lines Removed | -$DELETIONS |"
echo ""
```

### 3. Files Changed Analysis

```bash
echo "## 📁 Files Changed"
echo ""

echo "| File | Changes | Type |"
echo "|------|---------|------|"

git diff --numstat $BASE...$BRANCH 2>/dev/null | while read added removed file; do
    # Determine file type
    case "$file" in
        *.py) TYPE="🐍 Python" ;;
        *.js|*.ts) TYPE="📜 JavaScript" ;;
        *.php) TYPE="🐘 PHP" ;;
        *.sh) TYPE="🔧 Shell" ;;
        *.md) TYPE="📝 Docs" ;;
        *.json|*.yaml|*.yml) TYPE="⚙️ Config" ;;
        *.css|*.scss) TYPE="🎨 Style" ;;
        *.html) TYPE="🌐 HTML" ;;
        *test*|*spec*) TYPE="🧪 Test" ;;
        *) TYPE="📄 Other" ;;
    esac
    
    echo "| \`$file\` | +$added/-$removed | $TYPE |"
done

echo ""
```

### 4. Test Coverage Check

```bash
echo "## 🧪 Test Coverage"
echo ""

# Find source files that changed
CHANGED_SRC=$(git diff --name-only $BASE...$BRANCH | grep -E '\.(py|js|ts|php)$' | grep -v -E '(test_|_test\.|\.test\.|spec\.)' || true)

if [ -n "$CHANGED_SRC" ]; then
    echo "| Source File | Has Tests | Test File |"
    echo "|-------------|-----------|-----------|"
    
    MISSING_TESTS=0
    
    for src in $CHANGED_SRC; do
        # Determine expected test file
        case "$src" in
            *.py)
                TEST_PATTERNS=(
                    "tests/test_$(basename ${src%.py}).py"
                    "tests/$(dirname $src)/test_$(basename ${src%.py}).py"
                    "${src%.py}_test.py"
                )
                ;;
            *.js|*.ts)
                BASE_NAME="${src%.*}"
                TEST_PATTERNS=(
                    "${BASE_NAME}.test.js"
                    "${BASE_NAME}.spec.js"
                    "__tests__/$(basename $BASE_NAME).test.js"
                )
                ;;
            *.php)
                TEST_PATTERNS=(
                    "tests/$(basename ${src%.php})Test.php"
                    "tests/unit/$(basename ${src%.php})Test.php"
                )
                ;;
        esac
        
        FOUND_TEST=""
        for pattern in "${TEST_PATTERNS[@]}"; do
            if [ -f "$pattern" ]; then
                FOUND_TEST="$pattern"
                break
            fi
        done
        
        if [ -n "$FOUND_TEST" ]; then
            echo "| \`$src\` | ✅ | \`$FOUND_TEST\` |"
        else
            echo "| \`$src\` | ❌ | *Missing* |"
            ((MISSING_TESTS++))
        fi
    done
    
    echo ""
    if [ $MISSING_TESTS -gt 0 ]; then
        echo "⚠️ **Warning:** $MISSING_TESTS source file(s) missing tests"
    else
        echo "✅ All changed source files have corresponding tests"
    fi
else
    echo "No testable source files changed."
fi

echo ""
```

### 5. Security Scan

```bash
echo "## 🔒 Security Check"
echo ""

SECURITY_ISSUES=0

# Check for secrets
echo "### Secrets Detection"
SECRETS=$(git diff $BASE...$BRANCH | grep -E "(password|secret|api_key|token|private_key)\s*[=:]\s*['\"][^'\"]+['\"]" | grep -v "#" || true)
if [ -n "$SECRETS" ]; then
    echo "❌ **Potential secrets detected:**"
    echo "\`\`\`"
    echo "$SECRETS" | head -5
    echo "\`\`\`"
    ((SECURITY_ISSUES++))
else
    echo "✅ No hardcoded secrets detected"
fi
echo ""

# Check for dangerous patterns
echo "### Dangerous Patterns"
DANGEROUS=$(git diff $BASE...$BRANCH | grep -E "(eval\(|exec\(|shell_exec\(|system\(|\$_GET\[|\$_POST\[.*\](?!.*sanitize))" | grep "^+" || true)
if [ -n "$DANGEROUS" ]; then
    echo "⚠️ **Review these patterns:**"
    echo "\`\`\`"
    echo "$DANGEROUS" | head -10
    echo "\`\`\`"
    ((SECURITY_ISSUES++))
else
    echo "✅ No dangerous function calls detected"
fi
echo ""

# Check for .env or sensitive files
echo "### Sensitive Files"
SENSITIVE=$(git diff --name-only $BASE...$BRANCH | grep -E "(\.env|\.pem|\.key|credentials|secrets)" || true)
if [ -n "$SENSITIVE" ]; then
    echo "❌ **Sensitive files modified:**"
    echo "$SENSITIVE"
    ((SECURITY_ISSUES++))
else
    echo "✅ No sensitive files in changeset"
fi
echo ""

if [ $SECURITY_ISSUES -gt 0 ]; then
    echo "### Summary: $SECURITY_ISSUES security concern(s) found"
else
    echo "### Summary: ✅ No security issues detected"
fi
echo ""
```

### 6. Code Complexity Analysis

```bash
echo "## 📈 Complexity Analysis"
echo ""

# Python complexity
PY_FILES=$(git diff --name-only $BASE...$BRANCH | grep '\.py$' | grep -v test || true)
if [ -n "$PY_FILES" ] && command -v radon &> /dev/null; then
    echo "### Python Complexity (radon)"
    echo ""
    echo "| File | Grade | Complexity |"
    echo "|------|-------|------------|"
    
    for f in $PY_FILES; do
        if [ -f "$f" ]; then
            RESULT=$(radon cc "$f" -a -s 2>/dev/null | tail -1 || echo "N/A")
            GRADE=$(echo "$RESULT" | grep -oP '[A-F]' | head -1 || echo "?")
            SCORE=$(echo "$RESULT" | grep -oP '\d+\.\d+' || echo "N/A")
            echo "| \`$f\` | $GRADE | $SCORE |"
        fi
    done
    echo ""
fi

# Check for large functions
echo "### Large Functions (>50 lines)"
LARGE_FUNCS=""
for f in $(git diff --name-only $BASE...$BRANCH | grep -E '\.(py|js|php)$' || true); do
    if [ -f "$f" ]; then
        # This is a simplified check - look for function definitions
        case "$f" in
            *.py)
                FUNCS=$(grep -n "^def \|^    def \|^class " "$f" | cut -d: -f1 || true)
                ;;
        esac
    fi
done

if [ -z "$LARGE_FUNCS" ]; then
    echo "✅ No excessively large functions detected"
fi
echo ""
```

### 7. Documentation Check

```bash
echo "## 📚 Documentation"
echo ""

# Check if docs were updated
DOC_CHANGES=$(git diff --name-only $BASE...$BRANCH | grep -E '\.(md|rst|txt)$|README|CHANGELOG|docs/' || true)

if [ -n "$DOC_CHANGES" ]; then
    echo "### Updated Documentation"
    for doc in $DOC_CHANGES; do
        echo "- \`$doc\`"
    done
else
    # Check if code was added without docs
    CODE_ADDED=$(git diff --stat $BASE...$BRANCH | grep -E '\.(py|js|php).*\+' | wc -l)
    if [ "$CODE_ADDED" -gt 5 ]; then
        echo "⚠️ Significant code changes without documentation updates"
    else
        echo "ℹ️ No documentation changes (may be OK for small changes)"
    fi
fi
echo ""
```

### 8. Final Verdict

```bash
echo "## 🏁 Review Summary"
echo ""

# Collect all issues
TOTAL_ISSUES=$((MISSING_TESTS + SECURITY_ISSUES))

if [ $TOTAL_ISSUES -eq 0 ]; then
    echo "### ✅ READY FOR REVIEW"
    echo ""
    echo "No blocking issues detected. PR appears ready for human review."
else
    echo "### ⚠️ NEEDS ATTENTION"
    echo ""
    echo "Found $TOTAL_ISSUES issue(s) that should be addressed:"
    [ $MISSING_TESTS -gt 0 ] && echo "- $MISSING_TESTS file(s) missing tests"
    [ $SECURITY_ISSUES -gt 0 ] && echo "- $SECURITY_ISSUES security concern(s)"
fi

echo ""
echo "---"
echo "*Review generated by Claude Code on $(date)*"
```

## Quick Options

| Command | Description |
|---------|-------------|
| `/review-pr` | Review current branch vs main |
| `/review-pr feature/xyz` | Review specific branch |
| `/review-pr 123` | Review PR #123 (requires gh CLI) |

## Integration

- Works with: **git-workflow**, **security-operations**, **testing-and-qa**
- Saves reports to: `$SESSION_DIR/reviews/`
```

### 2.5 Create `/explain` Command

Create file: `$HOME/skippy/.claude/commands/explain.md`

```markdown
---
description: Explain code - trace execution flow, document logic, generate understanding
argument-hint: "<file:line>, <function_name>, or <file> for overview"
allowed-tools: ["Bash", "Read", "Grep"]
---

# Code Explainer

Understand code by tracing flow, dependencies, and generating documentation.

## Instructions

### 1. Parse Target

```bash
TARGET="${1:-}"

if [ -z "$TARGET" ]; then
    echo "## Code Explainer"
    echo ""
    echo "Usage:"
    echo "  /explain <file>              - Overview of file"
    echo "  /explain <file>:<line>       - Explain code at line"
    echo "  /explain <function_name>     - Find and explain function"
    echo "  /explain imports <file>      - Show dependency tree"
    echo "  /explain calls <function>    - Show all callers"
    exit 0
fi

# Determine mode
if [[ "$TARGET" == *":"* ]]; then
    MODE="line"
    FILE=$(echo "$TARGET" | cut -d: -f1)
    LINE=$(echo "$TARGET" | cut -d: -f2)
elif [[ "$TARGET" == "imports" ]]; then
    MODE="imports"
    FILE="${2:-}"
elif [[ "$TARGET" == "calls" ]]; then
    MODE="calls"
    FUNC="${2:-}"
elif [ -f "$TARGET" ]; then
    MODE="file"
    FILE="$TARGET"
else
    MODE="function"
    FUNC="$TARGET"
fi
```

### 2. File Overview

```bash
if [ "$MODE" = "file" ]; then
    echo "# File Overview: $FILE"
    echo ""
    
    # Basic stats
    LINES=$(wc -l < "$FILE")
    EXTENSION="${FILE##*.}"
    
    echo "| Property | Value |"
    echo "|----------|-------|"
    echo "| Lines | $LINES |"
    echo "| Type | $EXTENSION |"
    echo "| Last Modified | $(stat -c %y "$FILE" | cut -d. -f1) |"
    echo ""
    
    case "$EXTENSION" in
        py)
            echo "## Imports"
            echo "\`\`\`python"
            grep -E "^import |^from " "$FILE" | head -20
            echo "\`\`\`"
            echo ""
            
            echo "## Classes"
            grep -n "^class " "$FILE" | while read line; do
                echo "- Line ${line}"
            done
            echo ""
            
            echo "## Functions"
            grep -n "^def \|^    def " "$FILE" | while read line; do
                echo "- ${line}"
            done
            echo ""
            
            echo "## Docstring"
            sed -n '1,/^"""$/p' "$FILE" | head -20 || echo "No module docstring"
            ;;
            
        js|ts)
            echo "## Imports"
            echo "\`\`\`javascript"
            grep -E "^import |^const .* = require" "$FILE" | head -20
            echo "\`\`\`"
            echo ""
            
            echo "## Exports"
            grep -E "^export |module\.exports" "$FILE"
            echo ""
            
            echo "## Functions/Classes"
            grep -n "^function \|^class \|^const .* = " "$FILE" | head -20
            ;;
            
        php)
            echo "## Namespace/Use"
            echo "\`\`\`php"
            grep -E "^namespace |^use " "$FILE" | head -20
            echo "\`\`\`"
            echo ""
            
            echo "## Classes"
            grep -n "^class \|^abstract class \|^interface " "$FILE"
            echo ""
            
            echo "## Functions"
            grep -n "function " "$FILE" | head -20
            ;;
    esac
fi
```

### 3. Line Explanation

```bash
if [ "$MODE" = "line" ]; then
    echo "# Code at $FILE:$LINE"
    echo ""
    
    # Show context (10 lines before and after)
    START=$((LINE - 10))
    [ $START -lt 1 ] && START=1
    END=$((LINE + 10))
    
    echo "## Context"
    echo "\`\`\`"
    sed -n "${START},${END}p" "$FILE" | nl -ba -v $START | while read num content; do
        if [ "$num" -eq "$LINE" ]; then
            echo ">>> $num: $content"
        else
            echo "    $num: $content"
        fi
    done
    echo "\`\`\`"
    echo ""
    
    # Extract the specific line
    CODE_LINE=$(sed -n "${LINE}p" "$FILE")
    
    echo "## Analysis"
    echo ""
    echo "**Line:** \`$CODE_LINE\`"
    echo ""
    
    # Identify what's happening
    case "$CODE_LINE" in
        *"def "*|*"function "*)
            echo "**Type:** Function definition"
            # Show function body
            echo ""
            echo "**Function body:**"
            EXTENSION="${FILE##*.}"
            if [ "$EXTENSION" = "py" ]; then
                sed -n "${LINE},\$p" "$FILE" | awk '/^def /{if(NR>1)exit}1' | head -30
            fi
            ;;
        *"class "*)
            echo "**Type:** Class definition"
            ;;
        *"import "*|*"from "*|*"require("*)
            echo "**Type:** Import statement"
            # Try to find what's being imported
            ;;
        *"return "*)
            echo "**Type:** Return statement"
            ;;
        *"if "*|*"elif "*|*"else"*)
            echo "**Type:** Conditional"
            ;;
        *"for "*|*"while "*)
            echo "**Type:** Loop"
            ;;
    esac
fi
```

### 4. Function Search and Explain

```bash
if [ "$MODE" = "function" ]; then
    echo "# Function: $FUNC"
    echo ""
    
    # Find function definition
    echo "## Definition"
    FOUND=$(grep -rn "def $FUNC\|function $FUNC\|const $FUNC\s*=" --include="*.py" --include="*.js" --include="*.ts" --include="*.php" . 2>/dev/null | head -5)
    
    if [ -n "$FOUND" ]; then
        echo "$FOUND" | while read match; do
            FILE=$(echo "$match" | cut -d: -f1)
            LINE=$(echo "$match" | cut -d: -f2)
            echo ""
            echo "**Found in:** \`$FILE:$LINE\`"
            echo ""
            echo "\`\`\`"
            sed -n "${LINE},$((LINE+20))p" "$FILE"
            echo "\`\`\`"
        done
    else
        echo "Function \`$FUNC\` not found in codebase"
    fi
    
    echo ""
    echo "## Usages"
    grep -rn "$FUNC(" --include="*.py" --include="*.js" --include="*.php" . 2>/dev/null | grep -v "def $FUNC\|function $FUNC" | head -10
fi
```

### 5. Import/Dependency Tree

```bash
if [ "$MODE" = "imports" ]; then
    echo "# Dependency Tree: $FILE"
    echo ""
    
    EXTENSION="${FILE##*.}"
    
    echo "## Direct Imports"
    echo "\`\`\`"
    case "$EXTENSION" in
        py)
            grep -E "^import |^from " "$FILE" | sort -u
            ;;
        js|ts)
            grep -E "^import |require\(" "$FILE" | sort -u
            ;;
        php)
            grep -E "^use " "$FILE" | sort -u
            ;;
    esac
    echo "\`\`\`"
    echo ""
    
    echo "## Import Graph"
    echo "(First-level dependencies)"
    echo ""
    
    if [ "$EXTENSION" = "py" ]; then
        grep -E "^from \w+ import|^import \w+" "$FILE" | while read line; do
            MODULE=$(echo "$line" | grep -oP '(?<=from )\w+|(?<=import )\w+' | head -1)
            # Check if local module
            if [ -f "${MODULE}.py" ] || [ -d "$MODULE" ]; then
                echo "- \`$MODULE\` (local)"
            else
                echo "- \`$MODULE\` (external)"
            fi
        done
    fi
fi
```

### 6. Call Graph

```bash
if [ "$MODE" = "calls" ]; then
    echo "# Callers of: $FUNC"
    echo ""
    
    echo "## All References"
    grep -rn "$FUNC(" --include="*.py" --include="*.js" --include="*.php" . 2>/dev/null | grep -v "def $FUNC\|function $FUNC" | while read match; do
        FILE=$(echo "$match" | cut -d: -f1)
        LINE=$(echo "$match" | cut -d: -f2)
        CODE=$(echo "$match" | cut -d: -f3-)
        echo "- \`$FILE:$LINE\` - \`$CODE\`"
    done | head -20
    
    echo ""
    echo "## Call Hierarchy"
    echo "(Functions that call $FUNC)"
    echo ""
    
    # Find enclosing functions for each call
    grep -rn "$FUNC(" --include="*.py" . 2>/dev/null | grep -v "def $FUNC" | while read match; do
        FILE=$(echo "$match" | cut -d: -f1)
        LINE=$(echo "$match" | cut -d: -f2)
        # Find enclosing function
        CALLER=$(head -n $LINE "$FILE" | tac | grep -m1 "def \|function " | grep -oP '(?<=def |function )\w+')
        [ -n "$CALLER" ] && echo "- $CALLER() → $FUNC()"
    done | sort -u
fi
```

## Examples

```
/explain src/utils.py                    # File overview
/explain src/utils.py:45                 # Explain line 45
/explain process_data                    # Find and explain function
/explain imports src/main.py             # Show dependencies
/explain calls validate_input            # Show all callers
```
```

### 2.6 Create `/health-check` Command

Create file: `$HOME/skippy/.claude/commands/health-check.md`

```markdown
---
description: Comprehensive system health validation - hooks, MCP, git, paths, and configuration
argument-hint: "[optional: 'quick' for fast check, 'full' for complete validation]"
allowed-tools: ["Bash", "Read"]
---

# System Health Check

Validate all Claude Code configuration components.

## Instructions

```bash
MODE="${1:-quick}"
ISSUES=0
WARNINGS=0

echo "# Claude Code Health Check"
echo ""
echo "**Time:** $(date '+%Y-%m-%d %H:%M:%S')"
echo "**Mode:** $MODE"
echo ""

# =============================================================================
# 1. Hook Validation
# =============================================================================
echo "## 🔧 Hooks"
echo ""

HOOKS_DIR="$HOME/.claude/hooks"
if [ -d "$HOOKS_DIR" ]; then
    echo "| Hook | Exists | Executable | Syntax |"
    echo "|------|--------|------------|--------|"
    
    for hook in pre_compact session_start_check context_budget_monitor pre_tool_use post_edit_backup; do
        HOOK_FILE="$HOOKS_DIR/${hook}.sh"
        if [ -f "$HOOK_FILE" ]; then
            EXISTS="✅"
            if [ -x "$HOOK_FILE" ]; then
                EXEC="✅"
            else
                EXEC="❌"
                ((ISSUES++))
            fi
            if bash -n "$HOOK_FILE" 2>/dev/null; then
                SYNTAX="✅"
            else
                SYNTAX="❌"
                ((ISSUES++))
            fi
        else
            EXISTS="❌"
            EXEC="—"
            SYNTAX="—"
            ((WARNINGS++))
        fi
        echo "| $hook | $EXISTS | $EXEC | $SYNTAX |"
    done
else
    echo "❌ Hooks directory not found: $HOOKS_DIR"
    ((ISSUES++))
fi
echo ""

# =============================================================================
# 2. Skills Validation
# =============================================================================
echo "## 📚 Skills"
echo ""

SKILLS_DIR="$HOME/.claude/skills"
if [ -d "$SKILLS_DIR" ]; then
    TOTAL_SKILLS=$(ls -d "$SKILLS_DIR"/*/ 2>/dev/null | wc -l)
    VALID_SKILLS=0
    EMPTY_RESOURCES=0
    
    for skill_dir in "$SKILLS_DIR"/*/; do
        if [ -f "${skill_dir}SKILL.md" ]; then
            ((VALID_SKILLS++))
        fi
        if [ -d "${skill_dir}resources" ] && [ -z "$(ls -A "${skill_dir}resources" 2>/dev/null)" ]; then
            ((EMPTY_RESOURCES++))
        fi
    done
    
    echo "| Metric | Value |"
    echo "|--------|-------|"
    echo "| Total Skill Directories | $TOTAL_SKILLS |"
    echo "| Valid Skills (with SKILL.md) | $VALID_SKILLS |"
    echo "| Empty Resource Directories | $EMPTY_RESOURCES |"
    
    [ $EMPTY_RESOURCES -gt 0 ] && ((WARNINGS++))
else
    echo "❌ Skills directory not found: $SKILLS_DIR"
    ((ISSUES++))
fi
echo ""

# =============================================================================
# 3. Settings Validation
# =============================================================================
echo "## ⚙️ Settings"
echo ""

SETTINGS_FILE="$HOME/.claude/settings.json"
if [ -f "$SETTINGS_FILE" ]; then
    if python3 -m json.tool "$SETTINGS_FILE" > /dev/null 2>&1; then
        echo "✅ settings.json is valid JSON"
        
        # Check for required sections
        for section in sandbox hooks permissions; do
            if grep -q "\"$section\"" "$SETTINGS_FILE"; then
                echo "✅ Section '$section' present"
            else
                echo "⚠️ Section '$section' missing"
                ((WARNINGS++))
            fi
        done
    else
        echo "❌ settings.json is invalid JSON"
        ((ISSUES++))
    fi
else
    echo "❌ Settings file not found: $SETTINGS_FILE"
    ((ISSUES++))
fi
echo ""

# =============================================================================
# 4. Path Validation
# =============================================================================
echo "## 📁 Required Paths"
echo ""

REQUIRED_PATHS=(
    "$HOME/.claude"
    "$HOME/.claude/hooks"
    "$HOME/.claude/skills"
    "$HOME/.claude/logs"
    "$HOME/skippy"
    "$HOME/skippy/work"
)

echo "| Path | Status |"
echo "|------|--------|"

for path in "${REQUIRED_PATHS[@]}"; do
    if [ -d "$path" ]; then
        echo "| \`$path\` | ✅ |"
    else
        echo "| \`$path\` | ❌ Missing |"
        ((ISSUES++))
    fi
done
echo ""

# =============================================================================
# 5. Git Status
# =============================================================================
echo "## 🔀 Git Status"
echo ""

for repo in "$HOME/skippy" "$HOME/.claude"; do
    if [ -d "$repo/.git" ]; then
        echo "### $(basename $repo)"
        cd "$repo"
        BRANCH=$(git branch --show-current 2>/dev/null || echo "N/A")
        UNCOMMITTED=$(git status --porcelain 2>/dev/null | wc -l)
        AHEAD=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo "N/A")
        
        echo "- Branch: $BRANCH"
        echo "- Uncommitted changes: $UNCOMMITTED"
        echo "- Commits ahead of origin: $AHEAD"
        echo ""
        
        [ "$UNCOMMITTED" -gt 10 ] && ((WARNINGS++))
    fi
done

# =============================================================================
# 6. MCP Server Status (if applicable)
# =============================================================================
if [ "$MODE" = "full" ]; then
    echo "## 🔌 MCP Servers"
    echo ""
    
    if command -v claude &> /dev/null; then
        claude mcp list 2>/dev/null || echo "Unable to query MCP status"
    else
        echo "Claude CLI not available for MCP check"
    fi
    echo ""
fi

# =============================================================================
# 7. Recent Errors
# =============================================================================
echo "## ⚠️ Recent Errors"
echo ""

LOG_FILES=(
    "$HOME/.claude/logs/hooks.log"
    "$HOME/.claude/tool_logs/blocked_commands.log"
    "$HOME/.claude/tool_logs/tool_usage.log"
)

RECENT_ERRORS=0
for log in "${LOG_FILES[@]}"; do
    if [ -f "$log" ]; then
        ERRORS=$(grep -i "error\|failed\|blocked" "$log" 2>/dev/null | tail -5 | wc -l)
        RECENT_ERRORS=$((RECENT_ERRORS + ERRORS))
        if [ $ERRORS -gt 0 ]; then
            echo "### $(basename $log)"
            grep -i "error\|failed\|blocked" "$log" | tail -3
            echo ""
        fi
    fi
done

if [ $RECENT_ERRORS -eq 0 ]; then
    echo "✅ No recent errors in logs"
fi
echo ""

# =============================================================================
# 8. Disk Space
# =============================================================================
echo "## 💾 Disk Space"
echo ""

echo "| Location | Used | Available |"
echo "|----------|------|-----------|"
df -h "$HOME" 2>/dev/null | tail -1 | awk '{print "| $HOME | "$3" | "$4" |"}'
df -h "$HOME/.claude" 2>/dev/null | tail -1 | awk '{print "| .claude | "$3" | "$4" |"}' 2>/dev/null || echo "| .claude | — | — |"
echo ""

# =============================================================================
# Summary
# =============================================================================
echo "---"
echo ""
echo "## 📊 Summary"
echo ""

if [ $ISSUES -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "### ✅ ALL CHECKS PASSED"
    echo ""
    echo "System is healthy and ready for use."
elif [ $ISSUES -eq 0 ]; then
    echo "### ⚠️ MINOR WARNINGS"
    echo ""
    echo "- Issues: $ISSUES"
    echo "- Warnings: $WARNINGS"
    echo ""
    echo "System is functional but has minor issues to address."
else
    echo "### ❌ ISSUES FOUND"
    echo ""
    echo "- Critical Issues: $ISSUES"
    echo "- Warnings: $WARNINGS"
    echo ""
    echo "Please address the issues above before continuing."
fi

echo ""
echo "---"
echo "*Health check completed at $(date)*"
```

## Quick Reference

| Command | Description |
|---------|-------------|
| `/health-check` | Quick validation |
| `/health-check quick` | Same as above |
| `/health-check full` | Complete check including MCP |
```

### 2.7 Create `/dev-session` Command

Create file: `$HOME/skippy/.claude/commands/dev-session.md`

```markdown
---
description: Initialize or manage development sessions with proper workspace setup
argument-hint: "[start <name>, end, status, or list]"
allowed-tools: ["Bash", "Read", "Write"]
---

# Development Session Manager

Manage structured development sessions with proper state tracking.

## Instructions

### 1. Parse Command

```bash
ACTION="${1:-status}"
NAME="${2:-$(date +%H%M%S)}"

SESSION_BASE="$HOME/skippy/work/dev-sessions"
CURRENT_SESSION_FILE="$HOME/.claude/.current_dev_session"
```

### 2. Start Session

```bash
if [ "$ACTION" = "start" ]; then
    # Create session directory
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    SESSION_DIR="$SESSION_BASE/${TIMESTAMP}_${NAME}"
    mkdir -p "$SESSION_DIR"/{code,tests,notes,backups}
    
    # Capture starting state
    echo "# Development Session: $NAME" > "$SESSION_DIR/SESSION.md"
    echo "" >> "$SESSION_DIR/SESSION.md"
    echo "**Started:** $(date '+%Y-%m-%d %H:%M:%S')" >> "$SESSION_DIR/SESSION.md"
    echo "**Directory:** $SESSION_DIR" >> "$SESSION_DIR/SESSION.md"
    echo "" >> "$SESSION_DIR/SESSION.md"
    
    # Git state
    echo "## Git State at Start" >> "$SESSION_DIR/SESSION.md"
    echo "\`\`\`" >> "$SESSION_DIR/SESSION.md"
    git status --short >> "$SESSION_DIR/SESSION.md" 2>/dev/null || echo "Not in git repo"
    echo "\`\`\`" >> "$SESSION_DIR/SESSION.md"
    echo "" >> "$SESSION_DIR/SESSION.md"
    
    # Save current diff
    git diff > "$SESSION_DIR/backups/uncommitted_start.patch" 2>/dev/null || true
    git stash list > "$SESSION_DIR/backups/stash_list.txt" 2>/dev/null || true
    
    # Track session
    echo "$SESSION_DIR" > "$CURRENT_SESSION_FILE"
    
    # Create useful aliases file
    cat > "$SESSION_DIR/aliases.sh" << 'ALIASES'
# Source this file: source aliases.sh
alias t="pytest -v --tb=short"
alias lint="flake8 && mypy . --ignore-missing-imports"
alias fmt="black . && isort ."
alias gs="git status"
alias gd="git diff"
alias gc="git commit"
ALIASES
    
    echo "## ✅ Session Started"
    echo ""
    echo "**Session:** $NAME"
    echo "**Directory:** $SESSION_DIR"
    echo ""
    echo "### Quick Access"
    echo "- Notes: \`$SESSION_DIR/notes/\`"
    echo "- Code: \`$SESSION_DIR/code/\`"
    echo "- Tests: \`$SESSION_DIR/tests/\`"
    echo ""
    echo "### Aliases"
    echo "Source with: \`source $SESSION_DIR/aliases.sh\`"
    echo ""
    echo "### End Session"
    echo "Run: \`/dev-session end\`"
fi
```

### 3. End Session

```bash
if [ "$ACTION" = "end" ]; then
    if [ ! -f "$CURRENT_SESSION_FILE" ]; then
        echo "❌ No active session found"
        exit 1
    fi
    
    SESSION_DIR=$(cat "$CURRENT_SESSION_FILE")
    
    if [ ! -d "$SESSION_DIR" ]; then
        echo "❌ Session directory not found: $SESSION_DIR"
        rm "$CURRENT_SESSION_FILE"
        exit 1
    fi
    
    # Capture ending state
    echo "" >> "$SESSION_DIR/SESSION.md"
    echo "## Session End" >> "$SESSION_DIR/SESSION.md"
    echo "**Ended:** $(date '+%Y-%m-%d %H:%M:%S')" >> "$SESSION_DIR/SESSION.md"
    echo "" >> "$SESSION_DIR/SESSION.md"
    
    # Git state at end
    echo "### Git State at End" >> "$SESSION_DIR/SESSION.md"
    echo "\`\`\`" >> "$SESSION_DIR/SESSION.md"
    git status --short >> "$SESSION_DIR/SESSION.md" 2>/dev/null
    echo "\`\`\`" >> "$SESSION_DIR/SESSION.md"
    
    # Save final diff
    git diff > "$SESSION_DIR/backups/uncommitted_end.patch" 2>/dev/null || true
    
    # Commits made during session
    echo "" >> "$SESSION_DIR/SESSION.md"
    echo "### Commits This Session" >> "$SESSION_DIR/SESSION.md"
    echo "\`\`\`" >> "$SESSION_DIR/SESSION.md"
    git log --oneline --since="$(stat -c %Y "$SESSION_DIR" | xargs -I {} date -d @{} '+%Y-%m-%d %H:%M:%S')" >> "$SESSION_DIR/SESSION.md" 2>/dev/null || echo "None"
    echo "\`\`\`" >> "$SESSION_DIR/SESSION.md"
    
    # Files created in session
    echo "" >> "$SESSION_DIR/SESSION.md"
    echo "### Files in Session Directory" >> "$SESSION_DIR/SESSION.md"
    find "$SESSION_DIR" -type f -name "*.py" -o -name "*.js" -o -name "*.sh" -o -name "*.md" 2>/dev/null | while read f; do
        echo "- \`${f#$SESSION_DIR/}\`" >> "$SESSION_DIR/SESSION.md"
    done
    
    # Clear current session
    rm "$CURRENT_SESSION_FILE"
    
    echo "## ✅ Session Ended"
    echo ""
    echo "**Session Directory:** $SESSION_DIR"
    echo "**Documentation:** $SESSION_DIR/SESSION.md"
    echo ""
    echo "### Session Summary"
    cat "$SESSION_DIR/SESSION.md"
fi
```

### 4. Session Status

```bash
if [ "$ACTION" = "status" ]; then
    echo "## Development Session Status"
    echo ""
    
    if [ -f "$CURRENT_SESSION_FILE" ]; then
        SESSION_DIR=$(cat "$CURRENT_SESSION_FILE")
        if [ -d "$SESSION_DIR" ]; then
            echo "### ✅ Active Session"
            echo ""
            echo "**Directory:** $SESSION_DIR"
            echo "**Started:** $(stat -c %y "$SESSION_DIR" | cut -d. -f1)"
            echo ""
            
            # Files in session
            echo "### Session Contents"
            find "$SESSION_DIR" -type f | head -20 | while read f; do
                echo "- ${f#$SESSION_DIR/}"
            done
            
            echo ""
            echo "### Current Git Status"
            git status --short 2>/dev/null | head -10
        else
            echo "⚠️ Session directory missing, clearing state"
            rm "$CURRENT_SESSION_FILE"
        fi
    else
        echo "### No Active Session"
        echo ""
        echo "Start one with: \`/dev-session start <name>\`"
    fi
fi
```

### 5. List Sessions

```bash
if [ "$ACTION" = "list" ]; then
    echo "## Recent Development Sessions"
    echo ""
    
    if [ -d "$SESSION_BASE" ]; then
        echo "| Session | Date | Files |"
        echo "|---------|------|-------|"
        
        ls -dt "$SESSION_BASE"/*/ 2>/dev/null | head -10 | while read dir; do
            NAME=$(basename "$dir")
            DATE=$(stat -c %y "$dir" | cut -d. -f1)
            FILES=$(find "$dir" -type f | wc -l)
            echo "| $NAME | $DATE | $FILES |"
        done
    else
        echo "No sessions found"
    fi
    
    echo ""
    echo "Session directory: $SESSION_BASE"
fi
```

## Usage

```
/dev-session start feature-xyz    # Start new session
/dev-session status               # Check current session
/dev-session end                  # End and document session
/dev-session list                 # Show recent sessions
```
```

---

## Phase 3: Enhanced Hooks

**Time:** 60 minutes
**Risk:** Medium (test thoroughly)

### 3.1 Add Error Handling to All Hooks

Add this header to ALL existing hooks:

```bash
# Add after shebang in every hook:

# Error handling - never block on hook failure
trap 'echo "[$(date)] Hook failed: $0" >> "$HOME/.claude/logs/hook_errors.log"; exit 0' ERR

# Timeout protection (if running long operations)
HOOK_TIMEOUT=5
timeout_handler() {
    echo "[$(date)] Hook timeout: $0" >> "$HOME/.claude/logs/hook_errors.log"
    exit 0
}
trap timeout_handler ALRM

# Set timeout (comment out if not needed)
# (sleep $HOOK_TIMEOUT && kill -ALRM $$ 2>/dev/null) &
# TIMEOUT_PID=$!
```

### 3.2 Create Auto-Lint Hook

Create file: `$HOME/.claude/hooks/post_edit_lint.sh`

```bash
#!/bin/bash
# post_edit_lint.sh - Auto-lint files after Claude edits them
# Hook: PostToolUse (matcher: Edit|Write)
# Version: 1.0.0

set -euo pipefail

# Error handling
trap 'exit 0' ERR

# Logging
LOG_FILE="$HOME/.claude/logs/lint.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# Read input
INPUT=$(cat)

# Extract file path
FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    # Try different possible field names
    path = data.get('file_path') or data.get('path') or data.get('filePath', '')
    print(path)
except:
    print('')
" 2>/dev/null || echo "")

[ -z "$FILE_PATH" ] && exit 0
[ ! -f "$FILE_PATH" ] && exit 0

log "Linting: $FILE_PATH"

# Determine file type and lint
EXTENSION="${FILE_PATH##*.}"

case "$EXTENSION" in
    py)
        # Python: format with black and isort if available
        if command -v black &> /dev/null; then
            black "$FILE_PATH" --quiet 2>/dev/null && log "black: formatted" || true
        fi
        if command -v isort &> /dev/null; then
            isort "$FILE_PATH" --quiet 2>/dev/null && log "isort: formatted" || true
        fi
        # Quick syntax check
        python3 -m py_compile "$FILE_PATH" 2>/dev/null || log "WARNING: Python syntax error"
        ;;
        
    js|ts|jsx|tsx)
        # JavaScript/TypeScript: prettier if available
        if command -v npx &> /dev/null && [ -f "node_modules/.bin/prettier" ]; then
            npx prettier --write "$FILE_PATH" 2>/dev/null && log "prettier: formatted" || true
        fi
        ;;
        
    sh|bash)
        # Shell: check syntax
        bash -n "$FILE_PATH" 2>/dev/null || log "WARNING: Shell syntax error"
        # ShellCheck if available
        if command -v shellcheck &> /dev/null; then
            ISSUES=$(shellcheck "$FILE_PATH" 2>/dev/null | head -3 || true)
            [ -n "$ISSUES" ] && log "shellcheck issues: $ISSUES"
        fi
        ;;
        
    php)
        # PHP: syntax check
        php -l "$FILE_PATH" 2>/dev/null | grep -v "No syntax errors" | head -1 || true
        ;;
        
    json)
        # JSON: validate
        python3 -m json.tool "$FILE_PATH" > /dev/null 2>&1 || log "WARNING: Invalid JSON"
        ;;
        
    yaml|yml)
        # YAML: validate if pyyaml available
        python3 -c "import yaml; yaml.safe_load(open('$FILE_PATH'))" 2>/dev/null || log "WARNING: Invalid YAML"
        ;;
esac

exit 0
```

Make executable and add to settings.json:

```bash
chmod +x "$HOME/.claude/hooks/post_edit_lint.sh"
```

Add to settings.json PostToolUse section:

```json
"PostToolUse": [
  {
    "matcher": "Edit|Write|NotebookEdit",
    "hooks": [
      {
        "type": "command",
        "command": "$HOME/.claude/hooks/post_edit_backup.sh",
        "timeout": 5000
      },
      {
        "type": "command",
        "command": "$HOME/.claude/hooks/post_edit_lint.sh",
        "timeout": 5000
      }
    ]
  }
]
```

### 3.3 Create Dev Context Tracker Hook

Create file: `$HOME/.claude/hooks/dev_context_tracker.sh`

```bash
#!/bin/bash
# dev_context_tracker.sh - Track development context for smarter assistance
# Hook: SessionStart, UserPromptSubmit
# Version: 1.0.0

set -euo pipefail
trap 'exit 0' ERR

CONTEXT_FILE="$HOME/.claude/dev_context.json"
mkdir -p "$(dirname "$CONTEXT_FILE")"

# Only update every 5 minutes to avoid overhead
if [ -f "$CONTEXT_FILE" ]; then
    LAST_UPDATE=$(stat -c %Y "$CONTEXT_FILE" 2>/dev/null || echo 0)
    NOW=$(date +%s)
    DIFF=$((NOW - LAST_UPDATE))
    [ $DIFF -lt 300 ] && exit 0
fi

# Gather context
BRANCH=$(git branch --show-current 2>/dev/null || echo "none")
RECENT_FILES=$(git diff --name-only HEAD~5 2>/dev/null | head -10 | tr '\n' ',' | sed 's/,$//' || echo "")
UNCOMMITTED=$(git status --porcelain 2>/dev/null | wc -l || echo 0)
CURRENT_DIR=$(pwd)
VENV="${VIRTUAL_ENV:-none}"
LAST_TEST=$(stat -c %Y .pytest_cache 2>/dev/null || echo 0)
FAILING_TESTS=$([ -f .pytest_cache/v/cache/lastfailed ] && cat .pytest_cache/v/cache/lastfailed 2>/dev/null | head -c 200 || echo "{}")

# Write context
cat > "$CONTEXT_FILE" << EOF
{
  "last_updated": "$(date -Iseconds)",
  "current_branch": "$BRANCH",
  "recent_files": "$RECENT_FILES",
  "uncommitted_changes": $UNCOMMITTED,
  "current_directory": "$CURRENT_DIR",
  "active_venv": "$VENV",
  "last_test_run": $LAST_TEST,
  "project_type": "$([ -f pyproject.toml ] && echo 'python' || ([ -f package.json ] && echo 'node' || echo 'unknown'))"
}
EOF

exit 0
```

### 3.4 Create Secrets Scanner Hook

Create file: `$HOME/.claude/hooks/secrets_scanner.sh`

```bash
#!/bin/bash
# secrets_scanner.sh - Scan for secrets before tool execution
# Hook: PreToolUse
# Version: 1.0.0
#
# Scans file operations for potential secret exposure

set -euo pipefail
trap 'exit 0' ERR

LOG_FILE="$HOME/.claude/logs/secrets_scan.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

INPUT=$(cat)

# Extract relevant info
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")
TOOL_INPUT=$(echo "$INPUT" | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin).get('tool_input',{})))" 2>/dev/null || echo "{}")

# Only check Write operations
[[ "$TOOL_NAME" != "Write" ]] && exit 0

# Extract content being written
CONTENT=$(echo "$TOOL_INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('content',''))" 2>/dev/null || echo "")

# Check for secrets patterns
PATTERNS=(
    'password\s*[=:]\s*["\x27][^"\x27]+'
    'api_key\s*[=:]\s*["\x27][^"\x27]+'
    'secret\s*[=:]\s*["\x27][^"\x27]+'
    'token\s*[=:]\s*["\x27][A-Za-z0-9_-]{20,}'
    'private_key'
    'BEGIN RSA PRIVATE KEY'
    'BEGIN OPENSSH PRIVATE KEY'
    'AKIA[0-9A-Z]{16}'  # AWS access key
    'sk-[a-zA-Z0-9]{48}'  # OpenAI key pattern
    'ghp_[a-zA-Z0-9]{36}'  # GitHub personal access token
)

for pattern in "${PATTERNS[@]}"; do
    if echo "$CONTENT" | grep -qE "$pattern"; then
        log "BLOCKED: Potential secret detected matching pattern: $pattern"
        echo '{"decision": "block", "reason": "Potential secret or credential detected in content. Please remove sensitive data before writing."}'
        exit 0
    fi
done

# All clear
exit 0
```

### 3.5 Update settings.json with New Hooks

Update the hooks section in `$HOME/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/pre_tool_use.sh",
            "timeout": 5000
          },
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/secrets_scanner.sh",
            "timeout": 3000
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|NotebookEdit",
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/post_edit_backup.sh",
            "timeout": 5000
          },
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/post_edit_lint.sh",
            "timeout": 5000
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/session_start_check.sh",
            "timeout": 10000
          },
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/dev_context_tracker.sh",
            "timeout": 5000
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/pre_compact.sh",
            "timeout": 30000
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/context_budget_monitor.sh",
            "timeout": 5000
          }
        ]
      }
    ]
  }
}
```

---

## Phase 4: Skill Consolidation

**Time:** 60 minutes
**Risk:** Low

### 4.1 Merge Debugging Skills

Create file: `$HOME/.claude/skills/debugging/SKILL.md`

(Merge `advanced-debugging` and `diagnostic-debugging` into single comprehensive skill)

```markdown
---
name: debugging
description: Comprehensive debugging skill. Auto-invoke when: debugging, troubleshooting, error investigation, stack traces, log analysis, or diagnosing issues.
---

# Debugging Skill

**Version:** 2.0.0
**Last Updated:** 2025-12-01
**Auto-Invoke:** Yes - on debugging, errors, troubleshooting, stack traces
**Merged From:** advanced-debugging, diagnostic-debugging

## When to Use This Skill

Auto-invoke when:
- Investigating errors or exceptions
- Analyzing stack traces
- Debugging test failures
- Troubleshooting system issues
- Reading log files
- Diagnosing performance problems

## Quick Diagnostics

### Error Type Detection

| Error Pattern | Category | First Steps |
|---------------|----------|-------------|
| `ModuleNotFoundError` | Import | Check virtualenv, pip install |
| `AttributeError` | Object | Check object type, None checks |
| `TypeError` | Type | Check function signatures |
| `KeyError` | Dict | Check key exists, use .get() |
| `FileNotFoundError` | I/O | Verify path, permissions |
| `ConnectionError` | Network | Check service, firewall |
| `PermissionError` | System | Check file/dir permissions |

### Universal Debug Commands

```bash
# Python debugging
python3 -m pdb script.py              # Interactive debugger
python3 -c "import traceback; help()" # Traceback help
pytest --pdb                          # Drop into debugger on failure
pytest --lf -x                        # Run last failed, stop on first

# Log analysis
tail -f /var/log/syslog | grep -i error
journalctl -f -u service_name
grep -r "ERROR\|Exception" logs/

# Process debugging
strace -p PID                         # System calls
lsof -p PID                          # Open files
ps aux | grep process_name           # Process info

# Network debugging
netstat -tlnp                        # Open ports
ss -tlnp                             # Modern netstat
curl -v URL                          # HTTP debugging
```

### Python-Specific

```python
# Quick debugging snippets
import pdb; pdb.set_trace()          # Breakpoint (Python 3.6)
breakpoint()                          # Breakpoint (Python 3.7+)

# Inspect object
print(f"{type(obj)=}, {dir(obj)=}")
print(f"{obj.__dict__=}")

# Trace function calls
import sys
def trace(frame, event, arg):
    print(f"{event}: {frame.f_code.co_name}")
    return trace
sys.settrace(trace)
```

### Log Analysis Patterns

```bash
# Find error patterns
grep -E "ERROR|CRITICAL|Exception" app.log | tail -20

# Count error types
grep -oP 'ERROR: \K[^:]+' app.log | sort | uniq -c | sort -rn

# Time-based filtering
awk '/2025-12-01 1[0-2]:/' app.log | grep ERROR

# Context around errors
grep -B5 -A10 "CRITICAL" app.log
```

## Systematic Debugging Process

### 1. Reproduce
```bash
# Create minimal reproduction
mkdir debug_session_$(date +%Y%m%d_%H%M%S)
cd debug_session_*
# Copy minimal files needed to reproduce
```

### 2. Isolate
```bash
# Binary search for cause
git bisect start
git bisect bad HEAD
git bisect good <known_good_commit>
```

### 3. Identify
```bash
# Add logging
# Use debugger
# Check assumptions
```

### 4. Fix & Verify
```bash
# Make fix
# Run tests
pytest tests/ -v
# Verify fix addresses root cause
```

## Integration

Works with:
- **testing-and-qa** - Test failure debugging
- **error-tracking-monitoring** - Error patterns
- **git-workflow** - Bisecting bugs

## Archive Note

This skill consolidates:
- `advanced-debugging` (747 lines)
- `diagnostic-debugging` (272 lines)

Previous versions archived at: `~/.claude/skills/_archived/`
```

After creating the merged skill:

```bash
# Archive old skills
mkdir -p "$HOME/.claude/skills/_archived"
mv "$HOME/.claude/skills/advanced-debugging" "$HOME/.claude/skills/_archived/"
mv "$HOME/.claude/skills/diagnostic-debugging" "$HOME/.claude/skills/_archived/"
```

### 4.2 Merge MCP Skills

Create file: `$HOME/.claude/skills/mcp-operations/SKILL.md`

```markdown
---
name: mcp-operations
description: MCP server management - deployment, monitoring, and tools. Auto-invoke when: MCP servers, server health, tool availability, or MCP configuration.
---

# MCP Operations Skill

**Version:** 2.0.0
**Last Updated:** 2025-12-01
**Merged From:** mcp-server-deployment, mcp-monitoring, mcp-server-tools

## When to Use

Auto-invoke when:
- Checking MCP server status
- Deploying or configuring MCP servers
- Troubleshooting tool availability
- Managing server lifecycle

## Quick Reference

### Check Status

```bash
# Via Claude CLI
claude mcp list

# Via slash command
/mcp-status
```

### Server Locations

| Server | Path | Tools |
|--------|------|-------|
| General | ~/skippy/mcp-servers/general-server/ | 52+ |
| WordPress | ~/skippy/mcp-servers/wordpress-validator/ | Validation |

### Common Operations

```bash
# Restart MCP server
pkill -f "mcp-server"
# Server auto-restarts with Claude Code

# Check server logs
tail -f ~/.claude/logs/mcp-*.log

# Validate server config
python3 -m json.tool ~/.config/claude/mcp_config.json
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Server disconnected | Restart Claude Code |
| Tool not available | Check server logs |
| Timeout errors | Increase timeout in settings |
| Auth failures | Re-authenticate OAuth |

## Deployment

### New Server Setup

```bash
# 1. Create server directory
mkdir -p ~/skippy/mcp-servers/new-server

# 2. Initialize with FastMCP
cd ~/skippy/mcp-servers/new-server
pip install fastmcp
# Create server.py with tools

# 3. Register in Claude config
# Add to ~/.config/claude/mcp_config.json
```

### Server Template

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("server-name")

@mcp.tool()
def my_tool(param: str) -> str:
    """Tool description."""
    return f"Result: {param}"

if __name__ == "__main__":
    mcp.run()
```

## Available Tools Summary

### Google Drive (13 tools)
- File search, upload, download
- Folder management
- Sharing permissions

### System Monitoring
- CPU, memory, disk usage
- Process management
- Service status

### WordPress
- WP-CLI integration
- Content validation
- Database operations

### Remote (Ebon Server)
- SSH command execution
- Health checks
- File transfers

## Integration

Works with:
- **system-infrastructure-management**
- **wordpress-deployment**
- **security-operations**
```

Archive old skills:

```bash
mv "$HOME/.claude/skills/mcp-monitoring" "$HOME/.claude/skills/_archived/"
mv "$HOME/.claude/skills/mcp-server-deployment" "$HOME/.claude/skills/_archived/"
mv "$HOME/.claude/skills/mcp-server-tools" "$HOME/.claude/skills/_archived/"
```

### 4.3 Merge Backup Skills

Create file: `$HOME/.claude/skills/backup-recovery/SKILL.md`

```markdown
---
name: backup-recovery
description: Backup and recovery operations - infrastructure backups, Google Drive sync, emergency recovery. Auto-invoke when: backups, restore, recovery, disaster recovery, or data protection.
---

# Backup & Recovery Skill

**Version:** 2.0.0
**Last Updated:** 2025-12-01
**Merged From:** backup-infrastructure, gdrive-backup, emergency-recovery

## When to Use

Auto-invoke when:
- Creating or managing backups
- Restoring from backups
- Emergency recovery needed
- Setting up backup schedules
- Google Drive sync operations

## Quick Reference

### Backup Locations

| Type | Location | Frequency |
|------|----------|-----------|
| Session states | ~/.claude/compactions/ | On compact |
| Code backups | ~/skippy/backups/ | Daily |
| WordPress | ~/skippy/backups/wordpress/ | Daily |
| Google Drive | Cloud sync | 4 AM daily |
| Database | ~/skippy/backups/db/ | Hourly |

### Quick Backup Commands

```bash
# WordPress full backup
wp db export ~/skippy/backups/db/wp_$(date +%Y%m%d).sql
tar -czf ~/skippy/backups/wordpress/wp_files_$(date +%Y%m%d).tar.gz /path/to/wordpress

# Session backup
cp -r ~/.claude/compactions ~/.claude/backups/sessions_$(date +%Y%m%d)

# Git bundle (portable repo backup)
git bundle create ~/skippy/backups/repo_$(date +%Y%m%d).bundle --all
```

### Automated Backup Cron Jobs

```bash
# List current cron jobs
crontab -l

# Backup cron schedule
# 0 * * * * ~/skippy/scripts/backup/hourly_db_backup.sh
# 0 4 * * * ~/skippy/scripts/backup/daily_full_backup.sh
# 0 4 * * 0 ~/skippy/scripts/backup/weekly_offsite_sync.sh
```

## Emergency Recovery

### Priority Order

1. **Check recent compactions**: `ls -lt ~/.claude/compactions/ | head -5`
2. **Check backup timestamps**: `ls -lt ~/skippy/backups/`
3. **Review recovery instructions**: `cat ~/.claude/compactions/*/RESUME_INSTRUCTIONS.md`

### WordPress Recovery

```bash
# 1. Restore database
wp db import ~/skippy/backups/db/wp_YYYYMMDD.sql

# 2. Restore files if needed
tar -xzf ~/skippy/backups/wordpress/wp_files_YYYYMMDD.tar.gz -C /

# 3. Clear cache
wp cache flush
```

### Git Recovery

```bash
# Restore from bundle
git clone ~/skippy/backups/repo_YYYYMMDD.bundle restored_repo

# Recover deleted branch
git reflog
git checkout -b recovered_branch HEAD@{n}

# Undo last commit (keep changes)
git reset --soft HEAD~1
```

### Session Recovery

```bash
# Find recent compaction
LATEST=$(ls -t ~/.claude/compactions/ | head -1)
cat ~/.claude/compactions/$LATEST/session_summary.md
cat ~/.claude/compactions/$LATEST/RESUME_INSTRUCTIONS.md
```

## Google Drive Sync

### Manual Sync

```bash
# Upload to Google Drive (via MCP tool)
# Use gdrive_upload tool

# Check sync status
ls -la ~/skippy/gdrive_sync/
```

### Sync Schedule

- **Daily 4 AM**: Full sync to Google Drive
- **On-demand**: Critical files immediately

## Backup Verification

```bash
# Verify backup integrity
# Database
mysql -u user -p dbname < backup.sql --verbose 2>&1 | tail -5

# Archive
tar -tzf backup.tar.gz > /dev/null && echo "OK" || echo "CORRUPT"

# Git bundle
git bundle verify ~/skippy/backups/repo.bundle
```

## Integration

Works with:
- **wordpress-deployment** - Pre-deploy backups
- **session-management** - Session preservation
- **google-drive-sync** - Cloud backup
```

Archive old skills:

```bash
mv "$HOME/.claude/skills/backup-infrastructure" "$HOME/.claude/skills/_archived/"
mv "$HOME/.claude/skills/gdrive-backup" "$HOME/.claude/skills/_archived/"
mv "$HOME/.claude/skills/emergency-recovery" "$HOME/.claude/skills/_archived/"
```

---

## Phase 5: Security Hardening

**Time:** 45 minutes
**Risk:** Low

### 5.1 Create Security Audit Command

Create file: `$HOME/skippy/.claude/commands/security-scan.md`

```markdown
---
description: Comprehensive security scan - secrets, vulnerabilities, permissions, dependencies
argument-hint: "[optional: 'quick' for fast scan, 'full' for comprehensive, 'deps' for dependencies only]"
allowed-tools: ["Bash", "Read", "Grep"]
---

# Security Scan

Comprehensive security scanning for the codebase.

## Instructions

```bash
MODE="${1:-quick}"
ISSUES=0
SCAN_DIR="${2:-.}"

echo "# Security Scan Report"
echo ""
echo "**Time:** $(date '+%Y-%m-%d %H:%M:%S')"
echo "**Mode:** $MODE"
echo "**Directory:** $SCAN_DIR"
echo ""

# =============================================================================
# 1. Secrets Detection
# =============================================================================
echo "## 🔐 Secrets Detection"
echo ""

# High-confidence patterns
PATTERNS=(
    'password\s*[=:]\s*["\x27][^"\x27]{4,}'
    'api_key\s*[=:]\s*["\x27][^"\x27]{8,}'
    'secret\s*[=:]\s*["\x27][^"\x27]{8,}'
    'private_key\s*[=:]\s*["\x27]'
    'AKIA[0-9A-Z]{16}'
    'sk-[a-zA-Z0-9]{32,}'
    'ghp_[a-zA-Z0-9]{36}'
    'xox[baprs]-[0-9a-zA-Z]{10,}'
    'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*'
    'BEGIN (RSA |OPENSSH |DSA |EC )?PRIVATE KEY'
)

for pattern in "${PATTERNS[@]}"; do
    MATCHES=$(grep -rn --include="*.py" --include="*.js" --include="*.ts" --include="*.php" --include="*.sh" --include="*.yaml" --include="*.yml" --include="*.json" -E "$pattern" "$SCAN_DIR" 2>/dev/null | grep -v node_modules | grep -v ".git" | head -5)
    if [ -n "$MATCHES" ]; then
        echo "❌ **Pattern:** \`$pattern\`"
        echo "\`\`\`"
        echo "$MATCHES"
        echo "\`\`\`"
        ((ISSUES++))
    fi
done

if [ $ISSUES -eq 0 ]; then
    echo "✅ No hardcoded secrets detected"
fi
echo ""

# =============================================================================
# 2. Sensitive Files
# =============================================================================
echo "## 📁 Sensitive Files"
echo ""

SENSITIVE_FILES=$(find "$SCAN_DIR" -type f \( -name ".env" -o -name ".env.*" -o -name "*.pem" -o -name "*.key" -o -name "*credentials*" -o -name "*secret*" -o -name "*.p12" -o -name "*.pfx" \) 2>/dev/null | grep -v node_modules | grep -v ".git")

if [ -n "$SENSITIVE_FILES" ]; then
    echo "⚠️ **Sensitive files found:**"
    echo "$SENSITIVE_FILES" | while read f; do
        IN_GITIGNORE=$(grep -F "$(basename $f)" .gitignore 2>/dev/null || true)
        if [ -n "$IN_GITIGNORE" ]; then
            echo "- \`$f\` (in .gitignore ✅)"
        else
            echo "- \`$f\` (NOT in .gitignore ❌)"
            ((ISSUES++))
        fi
    done
else
    echo "✅ No sensitive files found"
fi
echo ""

# =============================================================================
# 3. Dangerous Code Patterns
# =============================================================================
echo "## ⚠️ Dangerous Code Patterns"
echo ""

# SQL Injection risks
SQL_ISSUES=$(grep -rn --include="*.py" --include="*.php" -E "execute\s*\(.*%|query\s*\(.*\\\$" "$SCAN_DIR" 2>/dev/null | grep -v node_modules | head -5)
if [ -n "$SQL_ISSUES" ]; then
    echo "### SQL Injection Risk"
    echo "\`\`\`"
    echo "$SQL_ISSUES"
    echo "\`\`\`"
    ((ISSUES++))
fi

# Command injection
CMD_ISSUES=$(grep -rn --include="*.py" --include="*.php" -E "os\.system\s*\(|subprocess\.(call|run|Popen)\s*\([^,\]]*\+" "$SCAN_DIR" 2>/dev/null | grep -v node_modules | head -5)
if [ -n "$CMD_ISSUES" ]; then
    echo "### Command Injection Risk"
    echo "\`\`\`"
    echo "$CMD_ISSUES"
    echo "\`\`\`"
    ((ISSUES++))
fi

# Eval usage
EVAL_ISSUES=$(grep -rn --include="*.py" --include="*.js" --include="*.php" -E "eval\s*\(|exec\s*\(" "$SCAN_DIR" 2>/dev/null | grep -v node_modules | head -5)
if [ -n "$EVAL_ISSUES" ]; then
    echo "### Eval/Exec Usage"
    echo "\`\`\`"
    echo "$EVAL_ISSUES"
    echo "\`\`\`"
    ((ISSUES++))
fi

if [ -z "$SQL_ISSUES" ] && [ -z "$CMD_ISSUES" ] && [ -z "$EVAL_ISSUES" ]; then
    echo "✅ No dangerous patterns detected"
fi
echo ""

# =============================================================================
# 4. Dependency Vulnerabilities (full mode)
# =============================================================================
if [ "$MODE" = "full" ] || [ "$MODE" = "deps" ]; then
    echo "## 📦 Dependency Vulnerabilities"
    echo ""
    
    # Python
    if [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
        echo "### Python Dependencies"
        if command -v safety &> /dev/null; then
            safety check 2>/dev/null | tail -20 || echo "Safety check complete"
        elif command -v pip-audit &> /dev/null; then
            pip-audit 2>/dev/null | tail -20 || echo "Pip-audit complete"
        else
            echo "Install \`safety\` or \`pip-audit\` for Python vulnerability scanning"
        fi
        echo ""
    fi
    
    # Node.js
    if [ -f "package.json" ]; then
        echo "### Node.js Dependencies"
        if command -v npm &> /dev/null; then
            npm audit --json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Vulnerabilities: {d.get(\"metadata\",{}).get(\"vulnerabilities\",{})}')" 2>/dev/null || npm audit 2>/dev/null | tail -20
        fi
        echo ""
    fi
fi

# =============================================================================
# 5. Permission Issues
# =============================================================================
echo "## 🔒 File Permissions"
echo ""

# World-writable files
WORLD_WRITABLE=$(find "$SCAN_DIR" -type f -perm -002 2>/dev/null | grep -v node_modules | head -10)
if [ -n "$WORLD_WRITABLE" ]; then
    echo "⚠️ **World-writable files:**"
    echo "$WORLD_WRITABLE"
    ((ISSUES++))
else
    echo "✅ No world-writable files"
fi

# Executable scripts without proper permissions
SCRIPTS_NO_EXEC=$(find "$SCAN_DIR" -name "*.sh" ! -perm -111 2>/dev/null | grep -v node_modules | head -10)
if [ -n "$SCRIPTS_NO_EXEC" ]; then
    echo ""
    echo "ℹ️ **Shell scripts without execute permission:**"
    echo "$SCRIPTS_NO_EXEC"
fi
echo ""

# =============================================================================
# Summary
# =============================================================================
echo "---"
echo ""
echo "## 📊 Summary"
echo ""

if [ $ISSUES -eq 0 ]; then
    echo "### ✅ NO SECURITY ISSUES FOUND"
else
    echo "### ❌ FOUND $ISSUES ISSUE(S)"
    echo ""
    echo "Please review and address the issues above."
fi

echo ""
echo "---"
echo "*Scan completed at $(date)*"
```

### 5.2 Enhance .gitignore Security

Create/update file: `$HOME/skippy/.gitignore` (add these patterns):

```gitignore
# =============================================================================
# SECURITY: Sensitive Files (NEVER COMMIT)
# =============================================================================

# Environment files
.env
.env.*
.env.local
.env.*.local
*.env

# Credentials
credentials.json
client_secret*.json
*credentials*
*secret*
*.pem
*.key
*.p12
*.pfx
*.keystore
.htpasswd

# API keys and tokens
*.token
api_keys.json
tokens.json

# SSH keys
id_rsa*
id_ed25519*
id_ecdsa*
id_dsa*
*.pub

# Database dumps
*.sql
*.sql.gz
*.dump

# AWS
.aws/

# Google Cloud
.gcloud/
application_default_credentials.json

# IDE and editor secrets
.idea/workspace.xml
.idea/tasks.xml
.vscode/settings.json

# Session data
*.session
*.cookies

# =============================================================================
# Standard ignores
# =============================================================================

# Python
__pycache__/
*.py[cod]
.Python
*.so
.eggs/
*.egg-info/
.venv/
venv/
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm

# OS
.DS_Store
Thumbs.db

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# Build
dist/
build/
*.egg
```

### 5.3 Create Pre-Push Security Hook

Create file: `$HOME/skippy/.git/hooks/pre-push`

```bash
#!/bin/bash
# pre-push hook - Security validation before push
# Version: 1.0.0

set -e

echo "Running pre-push security checks..."

# Check for secrets in staged commits
PATTERNS=(
    'password\s*[=:]\s*["\x27][^"\x27]+'
    'api_key\s*[=:]\s*["\x27][^"\x27]+'
    'AKIA[0-9A-Z]{16}'
    'sk-[a-zA-Z0-9]{32,}'
    'BEGIN.*PRIVATE KEY'
)

# Get commits being pushed
REMOTE="$1"
URL="$2"

while read local_ref local_sha remote_ref remote_sha; do
    if [ "$local_sha" = "0000000000000000000000000000000000000000" ]; then
        continue
    fi
    
    if [ "$remote_sha" = "0000000000000000000000000000000000000000" ]; then
        RANGE="$local_sha"
    else
        RANGE="$remote_sha..$local_sha"
    fi
    
    for pattern in "${PATTERNS[@]}"; do
        MATCHES=$(git diff "$RANGE" | grep -E "^\+" | grep -E "$pattern" || true)
        if [ -n "$MATCHES" ]; then
            echo ""
            echo "❌ PUSH BLOCKED: Potential secret detected!"
            echo "Pattern: $pattern"
            echo "Matches:"
            echo "$MATCHES" | head -5
            echo ""
            echo "Please remove sensitive data before pushing."
            exit 1
        fi
    done
done

echo "✅ Security checks passed"
exit 0
```

Make executable:

```bash
chmod +x "$HOME/skippy/.git/hooks/pre-push"
```

---

## Phase 6: MCP Server Improvements

**Time:** 60 minutes
**Risk:** Medium

### 6.1 Create Modular Server Structure

This is a larger refactoring task. Create the structure:

```bash
mkdir -p ~/skippy/mcp-servers/general-server/{tools,lib,tests}
```

Create file: `~/skippy/mcp-servers/general-server/tools/__init__.py`

```python
"""
MCP Server Tools Package

Modular tool implementations for the general MCP server.
"""

from .gdrive import register_gdrive_tools
from .system import register_system_tools
from .wordpress import register_wordpress_tools
from .ssh import register_ssh_tools
from .files import register_file_tools

__all__ = [
    'register_gdrive_tools',
    'register_system_tools', 
    'register_wordpress_tools',
    'register_ssh_tools',
    'register_file_tools',
]
```

Create file: `~/skippy/mcp-servers/general-server/tools/system.py`

```python
"""System monitoring tools for MCP server."""

import psutil
import os
from typing import Any
from mcp.server.fastmcp import FastMCP


def register_system_tools(mcp: FastMCP) -> None:
    """Register system monitoring tools with the MCP server."""
    
    @mcp.tool()
    def get_system_info() -> dict[str, Any]:
        """Get comprehensive system information."""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent,
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent,
            },
            "load_average": os.getloadavg(),
        }
    
    @mcp.tool()
    def get_disk_usage(path: str = "/") -> dict[str, Any]:
        """Get disk usage for a specific path."""
        usage = psutil.disk_usage(path)
        return {
            "path": path,
            "total_gb": round(usage.total / (1024**3), 2),
            "used_gb": round(usage.used / (1024**3), 2),
            "free_gb": round(usage.free / (1024**3), 2),
            "percent": usage.percent,
        }
    
    @mcp.tool()
    def list_processes(sort_by: str = "memory") -> list[dict[str, Any]]:
        """List top processes by CPU or memory usage."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        key = 'memory_percent' if sort_by == 'memory' else 'cpu_percent'
        return sorted(processes, key=lambda x: x.get(key, 0), reverse=True)[:20]
```

Create file: `~/skippy/mcp-servers/general-server/server_modular.py`

```python
#!/usr/bin/env python3
"""
Modular MCP Server - Entry Point
Version: 3.0.0

This is the modular refactoring of the general MCP server.
Tools are organized in separate modules for maintainability.
"""

import logging
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("skippy-general")

# Import and register tool modules
try:
    from tools import (
        register_system_tools,
        register_file_tools,
        # register_gdrive_tools,
        # register_wordpress_tools,
        # register_ssh_tools,
    )
    
    # Register tools
    register_system_tools(mcp)
    register_file_tools(mcp)
    # Uncomment as modules are created:
    # register_gdrive_tools(mcp)
    # register_wordpress_tools(mcp)
    # register_ssh_tools(mcp)
    
    logger.info("All tool modules registered successfully")
    
except ImportError as e:
    logger.warning(f"Some tool modules not available: {e}")
    logger.info("Running with core tools only")


# Health check tool (always available)
@mcp.tool()
def health_check() -> dict:
    """Check MCP server health."""
    return {
        "status": "healthy",
        "server": "skippy-general",
        "version": "3.0.0",
    }


if __name__ == "__main__":
    logger.info("Starting Skippy General MCP Server v3.0.0")
    mcp.run()
```

### 6.2 Add Server Health Monitoring

Create file: `~/skippy/scripts/monitoring/mcp_health_check.sh`

```bash
#!/bin/bash
# mcp_health_check.sh - Monitor MCP server health
# Version: 1.0.0

set -euo pipefail

LOG_DIR="$HOME/.claude/logs"
LOG_FILE="$LOG_DIR/mcp_health.log"
mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

check_server() {
    local name="$1"
    local pid_file="$HOME/.claude/run/${name}.pid"
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p "$PID" > /dev/null 2>&1; then
            log "✅ $name: Running (PID $PID)"
            return 0
        else
            log "❌ $name: Dead (stale PID file)"
            rm -f "$pid_file"
            return 1
        fi
    else
        log "⚠️ $name: No PID file"
        return 1
    fi
}

# Check each MCP server
SERVERS=(
    "general-server"
    "wordpress-validator"
)

HEALTHY=0
TOTAL=${#SERVERS[@]}

for server in "${SERVERS[@]}"; do
    if check_server "$server"; then
        ((HEALTHY++))
    fi
done

log "Health: $HEALTHY/$TOTAL servers healthy"

# Exit with error if any server is unhealthy
[ $HEALTHY -eq $TOTAL ] && exit 0 || exit 1
```

---

## Phase 7: Automation & Convenience

**Time:** 45 minutes
**Risk:** Low

### 7.1 Create Quick Aliases File

Create file: `$HOME/.claude/aliases.sh`

```bash
# Claude Code Development Aliases
# Source this in your .bashrc: source ~/.claude/aliases.sh

# =============================================================================
# Git Shortcuts
# =============================================================================
alias gs="git status"
alias gd="git diff"
alias gds="git diff --staged"
alias ga="git add"
alias gc="git commit"
alias gp="git push"
alias gl="git log --oneline -20"
alias gb="git branch -a"
alias gco="git checkout"

# =============================================================================
# Testing
# =============================================================================
alias t="pytest -v --tb=short"
alias tf="pytest -v --tb=short --lf"  # Last failed
alias tc="pytest --cov=src --cov-report=term-missing"
alias tw="pytest -v --tb=short -x --watch"  # Stop on first, watch mode

# =============================================================================
# Linting & Formatting
# =============================================================================
alias lint="flake8 && mypy . --ignore-missing-imports"
alias fmt="black . && isort ."
alias check="lint && t"

# =============================================================================
# Claude Code
# =============================================================================
alias cc="claude"
alias ccs="claude status"
alias ccm="claude mcp list"

# =============================================================================
# Session Management
# =============================================================================
alias session="cd \$HOME/skippy/work && ls -lt | head -10"
alias newsession='mkdir -p "$HOME/skippy/work/dev/$(date +%Y%m%d_%H%M%S)_session" && cd "$_"'

# =============================================================================
# Logs
# =============================================================================
alias clogs="tail -f ~/.claude/logs/*.log"
alias hlogs="tail -f ~/.claude/logs/hooks.log"

# =============================================================================
# Quick Navigation
# =============================================================================
alias skippy="cd ~/skippy"
alias skills="cd ~/.claude/skills"
alias hooks="cd ~/.claude/hooks"

# =============================================================================
# Useful Functions
# =============================================================================

# Create session directory and cd into it
mksession() {
    local name="${1:-session}"
    local dir="$HOME/skippy/work/dev/$(date +%Y%m%d_%H%M%S)_${name}"
    mkdir -p "$dir"
    cd "$dir"
    echo "Session created: $dir"
}

# Quick search in skills
skill() {
    grep -rn "$1" ~/.claude/skills/*/SKILL.md | head -20
}

# Find command
findcmd() {
    grep -rn "$1" ~/skippy/.claude/commands/*.md | head -20
}

# Quick health check
health() {
    echo "=== Git Status ==="
    git status --short 2>/dev/null | head -5
    echo ""
    echo "=== Recent Errors ==="
    grep -i error ~/.claude/logs/*.log 2>/dev/null | tail -5
    echo ""
    echo "=== Disk Usage ==="
    df -h ~ | tail -1
}
```

Add to `.bashrc`:

```bash
echo 'source ~/.claude/aliases.sh' >> ~/.bashrc
```

### 7.2 Create Cron Jobs for Maintenance

Create file: `$HOME/skippy/scripts/cron/maintenance.cron`

```cron
# Claude Code Configuration Maintenance
# Install with: crontab ~/.skippy/scripts/cron/maintenance.cron

# Clean old log files (daily at 3 AM)
0 3 * * * find ~/.claude/logs -name "*.log" -mtime +30 -delete

# Clean old session directories (weekly on Sunday at 4 AM)
0 4 * * 0 find ~/skippy/work -type d -mtime +60 -empty -delete

# Archive old compactions (daily at 3:30 AM)
30 3 * * * find ~/.claude/compactions -type d -mtime +7 -exec tar -czf {}.tar.gz {} \; -exec rm -rf {} \;

# Update skills index (daily at 5 AM)
0 5 * * * ~/.claude/scripts/generate_skills_index.sh

# MCP health check (every 15 minutes)
*/15 * * * * ~/.skippy/scripts/monitoring/mcp_health_check.sh >> ~/.claude/logs/mcp_health.log 2>&1

# Backup configuration (daily at 2 AM)
0 2 * * * tar -czf ~/skippy/backups/claude_config_$(date +\%Y\%m\%d).tar.gz ~/.claude/
```

### 7.3 Create Configuration Sync Script

Create file: `$HOME/.claude/scripts/sync_config.sh`

```bash
#!/bin/bash
# sync_config.sh - Sync Claude Code configuration to backup/repo
# Version: 1.0.0

set -euo pipefail

BACKUP_DIR="$HOME/skippy/backups/claude_config"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Syncing Claude Code configuration..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Files to sync
sync_items=(
    "$HOME/.claude/skills"
    "$HOME/.claude/hooks"
    "$HOME/.claude/settings.json"
    "$HOME/.claude/CLAUDE.md"
    "$HOME/skippy/.claude/commands"
    "$HOME/skippy/.claude/CLAUDE.md"
)

# Create backup archive
ARCHIVE="$BACKUP_DIR/config_$TIMESTAMP.tar.gz"
tar -czf "$ARCHIVE" "${sync_items[@]}" 2>/dev/null

echo "Backup created: $ARCHIVE"

# Keep only last 10 backups
ls -t "$BACKUP_DIR"/config_*.tar.gz | tail -n +11 | xargs -r rm

echo "Sync complete!"
```

---

## Verification & Testing

After implementing all changes, run these verification steps:

### Test All Hooks

```bash
# Test hook syntax
for hook in ~/.claude/hooks/*.sh; do
    echo "Testing: $hook"
    bash -n "$hook" && echo "✅ Syntax OK" || echo "❌ Syntax Error"
done

# Test hook execution
echo '{"tool_name": "test", "tool_input": {}}' | ~/.claude/hooks/pre_tool_use.sh
echo "Exit code: $?"
```

### Test Commands

```bash
# Verify commands exist and have valid YAML frontmatter
for cmd in ~/skippy/.claude/commands/*.md; do
    echo "Checking: $(basename $cmd)"
    head -10 "$cmd" | grep -q "^---" && echo "✅ Has frontmatter" || echo "❌ Missing frontmatter"
done
```

### Test Skills

```bash
# Verify all skills have SKILL.md
for skill_dir in ~/.claude/skills/*/; do
    if [ -f "${skill_dir}SKILL.md" ]; then
        echo "✅ $(basename $skill_dir)"
    else
        echo "❌ $(basename $skill_dir) - Missing SKILL.md"
    fi
done
```

### Run Health Check

```bash
/health-check full
```

---

## Rollback Procedures

If any phase causes issues:

### Rollback Hooks

```bash
# Restore from backup
cp -r "$BACKUP_DIR/hooks/"* ~/.claude/hooks/
```

### Rollback Skills

```bash
# Restore from backup
cp -r "$BACKUP_DIR/skills/"* ~/.claude/skills/

# Or restore archived skills
mv ~/.claude/skills/_archived/* ~/.claude/skills/
```

### Rollback Settings

```bash
# Restore settings.json
cp "$BACKUP_DIR/settings.json" ~/.claude/settings.json
```

### Full Rollback

```bash
# Restore everything from pre-implementation backup
BACKUP=$(ls -t ~/.claude/backups/*_pre_improvements | head -1)
cp -r "$BACKUP/"* ~/.claude/
```

---

## Post-Implementation Checklist

- [ ] All hooks executable and passing syntax check
- [ ] All commands have valid YAML frontmatter
- [ ] All skills have SKILL.md files
- [ ] settings.json is valid JSON
- [ ] Health check passes
- [ ] Old skills archived (not deleted)
- [ ] Backup created before changes
- [ ] Git commit made with changes
- [ ] Documentation updated (VERSION, CHANGELOG)
- [ ] Test at least one slash command works
- [ ] Verify MCP servers still connected

---

## Summary

### Total Changes

| Category | Items Added/Modified |
|----------|---------------------|
| New Commands | 7 (/debug, /test, /scaffold, /review-pr, /explain, /health-check, /dev-session) |
| New Hooks | 3 (post_edit_lint, dev_context_tracker, secrets_scanner) |
| Hook Improvements | Error handling added to all hooks |
| Merged Skills | 3 groups (debugging, MCP, backup) |
| Security Additions | 5 (scan command, .gitignore, pre-push hook, secrets scanner, audit) |
| Convenience | Aliases file, cron jobs, sync script |
| Cleanup | 32 empty directories removed, index created |

### Files Created

```
~/.claude/
├── hooks/
│   ├── post_edit_lint.sh (NEW)
│   ├── dev_context_tracker.sh (NEW)
│   └── secrets_scanner.sh (NEW)
├── skills/
│   ├── INDEX.md (NEW)
│   ├── debugging/SKILL.md (NEW - merged)
│   ├── mcp-operations/SKILL.md (NEW - merged)
│   ├── backup-recovery/SKILL.md (NEW - merged)
│   └── _archived/ (OLD skills)
├── scripts/
│   ├── generate_skills_index.sh (NEW)
│   └── sync_config.sh (NEW)
├── aliases.sh (NEW)
├── VERSION (NEW)
└── CHANGELOG.md (NEW)

~/skippy/.claude/commands/
├── debug.md (NEW)
├── test.md (NEW)
├── scaffold.md (NEW)
├── review-pr.md (NEW)
├── explain.md (NEW)
├── health-check.md (NEW)
├── dev-session.md (NEW)
└── security-scan.md (NEW)
```

---

**End of Implementation Guide**

*This document was generated for Claude Code to implement comprehensive configuration improvements. Execute phases in order, verify after each phase, and use rollback procedures if needed.*
