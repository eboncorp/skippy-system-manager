# Claude Code Configuration Improvement Report

**Generated:** 2025-12-01
**Target System:** Skippy System Manager + Campaign Infrastructure
**Current State:** 75 skills, 32 commands, 9,140-line MCP server, 11 hooks
**Implementation Agent:** Claude Code

---

## Executive Summary

This document provides a comprehensive implementation plan to enhance the Claude Code configuration with improvements focused on:

1. **Development Productivity** - New commands and skills for faster coding
2. **Security Hardening** - Additional protections and automated scanning
3. **Automation** - Reduce manual work through smart hooks
4. **Consolidation** - Merge redundant skills, clean up unused resources
5. **Convenience** - Quality-of-life improvements for daily workflows

**Estimated Total Implementation Time:** 4-6 hours
**Priority:** High-value items first, nice-to-haves last

---

## Table of Contents

1. [Phase 1: New Slash Commands (Development)](#phase-1-new-slash-commands-development)
2. [Phase 2: New Hooks (Automation)](#phase-2-new-hooks-automation)
3. [Phase 3: Security Enhancements](#phase-3-security-enhancements)
4. [Phase 4: Skill Consolidation](#phase-4-skill-consolidation)
5. [Phase 5: Convenience Features](#phase-5-convenience-features)
6. [Phase 6: Infrastructure Cleanup](#phase-6-infrastructure-cleanup)
7. [Implementation Checklist](#implementation-checklist)

---

## Phase 1: New Slash Commands (Development)

### 1.1 Create `/debug` Command

**Location:** `~/.claude/commands/debug.md`

**Purpose:** Quick error analysis, stack trace parsing, and fix suggestions.

```markdown
---
description: Analyze errors, parse stack traces, suggest fixes, and trace issues through codebase
argument-hint: "[error message, file:line, or 'logs' to check recent errors]"
allowed-tools: ["Bash", "Read", "Grep", "Write"]
---

# Debug Assistant

Quick error analysis and debugging helper.

## Instructions

When invoked, determine the debug mode based on argument:

### Mode 1: Error Message Analysis
If argument looks like an error message:

```bash
ERROR="$1"

echo "## Error Analysis"
echo "**Input:** $ERROR"
echo ""

# Search codebase for error
echo "### Occurrences in Codebase"
grep -rn "$ERROR" --include="*.py" --include="*.js" --include="*.php" --include="*.sh" . 2>/dev/null | head -20

# Check recent logs
echo ""
echo "### Recent Log Entries"
find ~/.claude/logs /var/log -name "*.log" -mmin -60 2>/dev/null | xargs grep -l "$ERROR" 2>/dev/null | head -5
```

### Mode 2: File:Line Investigation
If argument matches `file:line` pattern:

```bash
FILE=$(echo "$1" | cut -d: -f1)
LINE=$(echo "$1" | cut -d: -f2)

echo "## Context Around Line $LINE in $FILE"
sed -n "$((LINE-10)),$((LINE+10))p" "$FILE" | nl -ba -v $((LINE-10))

echo ""
echo "### Function/Class Context"
grep -n "def \|class \|function " "$FILE" | awk -F: -v line="$LINE" '$1 < line {latest=$0} END {print latest}'
```

### Mode 3: Recent Logs Check
If argument is "logs" or empty:

```bash
echo "## Recent Error Logs"

# Claude logs
echo "### Claude Tool Logs (Last Hour)"
find ~/.claude/logs -name "*.log" -mmin -60 -exec tail -20 {} \; 2>/dev/null

# System logs
echo ""
echo "### Blocked Commands"
tail -20 ~/.claude/tool_logs/blocked_commands.log 2>/dev/null || echo "No blocked commands"

# WordPress errors
echo ""
echo "### WordPress Debug Log"
WP_DEBUG="/home/dave/skippy/rundaverun_local_site/app/public/wp-content/debug.log"
[ -f "$WP_DEBUG" ] && tail -30 "$WP_DEBUG" || echo "No WordPress debug log"
```

### Quick Fixes Database
After analysis, suggest fixes based on patterns:

```bash
suggest_fix() {
  case "$1" in
    *"ModuleNotFoundError"*)
      echo "**Fix:** pip install $(echo "$1" | grep -oP "No module named '\K[^']+")"
      ;;
    *"ENOENT"*|*"No such file"*)
      echo "**Fix:** Check if path exists, verify working directory"
      ;;
    *"Permission denied"*)
      echo "**Fix:** chmod +x <file> or check file ownership"
      ;;
    *"Connection refused"*)
      echo "**Fix:** Check if service is running (systemctl status <service>)"
      ;;
    *"SyntaxError"*)
      echo "**Fix:** Check for missing brackets, quotes, or colons"
      ;;
    *"IndentationError"*)
      echo "**Fix:** Fix indentation (use spaces, not tabs)"
      ;;
    *"KeyError"*)
      echo "**Fix:** Check if key exists before access: dict.get('key', default)"
      ;;
    *"TypeError"*)
      echo "**Fix:** Check argument types, add type hints for clarity"
      ;;
    *"ImportError"*)
      echo "**Fix:** Check import path, verify __init__.py exists"
      ;;
    *)
      echo "**Fix:** Search error message online or check documentation"
      ;;
  esac
}
```

### Python Traceback Parser
```bash
parse_python_traceback() {
  echo "$1" | grep -oP 'File "[^"]+", line \d+' | while read match; do
    FILE=$(echo "$match" | grep -oP '(?<=File ")[^"]+')
    LINE=$(echo "$match" | grep -oP '(?<=line )\d+')
    echo "- $FILE:$LINE"
    sed -n "${LINE}p" "$FILE" 2>/dev/null | sed 's/^/  > /'
  done
}
```

### JavaScript Stack Parser
```bash
parse_js_stack() {
  echo "$1" | grep -oP 'at .+ \([^)]+:\d+:\d+\)' | while read match; do
    echo "- $match"
  done
}
```

## Integration
- Works with: error-tracking-monitoring, advanced-debugging
- Logs to: ~/.claude/logs/debug_sessions.log
- Creates session in: /home/dave/skippy/work/debug/
```

---

### 1.2 Create `/test` Command

**Location:** `~/.claude/commands/test.md`

**Purpose:** Smart test runner with framework auto-detection.

```markdown
---
description: Run tests smartly - auto-detect framework, run relevant tests, show coverage
argument-hint: "[file, function, 'all', 'changed', or 'failed']"
allowed-tools: ["Bash", "Read"]
---

# Smart Test Runner

Automatically detects test framework and runs appropriate tests.

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
  
  echo "unknown"
}

FRAMEWORK=$(detect_framework)
echo "## Detected Framework: $FRAMEWORK"
```

### 2. Run Tests Based on Argument
```bash
TARGET="${1:-all}"

run_tests() {
  case "$FRAMEWORK" in
    pytest)
      case "$TARGET" in
        all)
          pytest tests/ -v --tb=short -x
          ;;
        changed)
          # Tests for files changed vs main
          CHANGED=$(git diff --name-only main | grep "\.py$" | grep -v test | sed 's|src/|tests/test_|' | sed 's|\.py$|.py|')
          [ -n "$CHANGED" ] && pytest $CHANGED -v --tb=short || echo "No changed test files"
          ;;
        failed)
          pytest --lf -v --tb=short
          ;;
        coverage)
          pytest tests/ --cov=src --cov-report=term-missing --cov-report=html
          echo "Coverage report: htmlcov/index.html"
          ;;
        *)
          # Specific file or pattern
          pytest "$TARGET" -v --tb=short
          ;;
      esac
      ;;
      
    jest)
      case "$TARGET" in
        all)
          npx jest --coverage
          ;;
        changed)
          npx jest --onlyChanged
          ;;
        failed)
          npx jest --onlyFailures
          ;;
        watch)
          npx jest --watch
          ;;
        *)
          npx jest "$TARGET" --coverage
          ;;
      esac
      ;;
      
    phpunit)
      case "$TARGET" in
        all)
          ./vendor/bin/phpunit --testdox
          ;;
        coverage)
          ./vendor/bin/phpunit --coverage-text
          ;;
        *)
          ./vendor/bin/phpunit --filter="$TARGET"
          ;;
      esac
      ;;
      
    *)
      echo "Unknown test framework. Looking for test files..."
      find . -name "*test*.py" -o -name "*.test.js" -o -name "*Test.php" | head -10
      ;;
  esac
}

run_tests
```

### 3. Quick Coverage Summary
```bash
if [ "$TARGET" = "coverage" ] || [ "$TARGET" = "all" ]; then
  echo ""
  echo "## Coverage Summary"
  case "$FRAMEWORK" in
    pytest)
      pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=0 2>/dev/null | grep -E "^(TOTAL|Name|---)" | tail -5
      ;;
    jest)
      npx jest --coverage --coverageReporters=text-summary 2>/dev/null | tail -10
      ;;
  esac
fi
```

### 4. Test File Validation
```bash
echo ""
echo "## Test Health Check"

# Count tests
case "$FRAMEWORK" in
  pytest)
    TOTAL=$(pytest --collect-only -q 2>/dev/null | tail -1)
    echo "Total tests: $TOTAL"
    ;;
  jest)
    TOTAL=$(npx jest --listTests 2>/dev/null | wc -l)
    echo "Total test files: $TOTAL"
    ;;
esac

# Check for files without tests
echo ""
echo "### Files Possibly Missing Tests"
for f in $(find src lib -name "*.py" -not -name "__init__.py" -not -name "*test*" 2>/dev/null | head -10); do
  BASENAME=$(basename "$f" .py)
  if ! find tests -name "*${BASENAME}*test*.py" -o -name "test_*${BASENAME}*.py" 2>/dev/null | grep -q .; then
    echo "- $f (no matching test file)"
  fi
done
```

## Usage Examples
- `/test` - Run all tests
- `/test changed` - Run tests for changed files only
- `/test failed` - Re-run only failed tests
- `/test coverage` - Run with coverage report
- `/test test_user.py` - Run specific test file
- `/test TestUserLogin` - Run specific test class/function
```

---

### 1.3 Create `/scaffold` Command

**Location:** `~/.claude/commands/scaffold.md`

**Purpose:** Generate boilerplate code for new files, classes, and tests.

```markdown
---
description: Generate boilerplate for classes, functions, tests, scripts, and more
argument-hint: "<type> <name> [options] (e.g., 'class UserService', 'test payment', 'script backup')"
allowed-tools: ["Bash", "Write", "Read"]
---

# Code Scaffolding Generator

Generate standardized boilerplate code following project conventions.

## Instructions

Parse the argument to determine scaffold type:

```bash
TYPE=$(echo "$1" | tr '[:upper:]' '[:lower:]')
NAME="$2"
OPTIONS="${@:3}"

# Convert name to different cases
SNAKE_NAME=$(echo "$NAME" | sed 's/\([A-Z]\)/_\L\1/g' | sed 's/^_//' | tr '[:upper:]' '[:lower:]')
PASCAL_NAME=$(echo "$NAME" | sed -r 's/(^|_)([a-z])/\U\2/g')
CAMEL_NAME=$(echo "$PASCAL_NAME" | sed 's/^\(.\)/\L\1/')
```

### Python Class Scaffold
```bash
if [ "$TYPE" = "class" ] && [[ "$NAME" =~ \.py$ ]] || [ -f "pyproject.toml" ]; then
cat > "${SNAKE_NAME}.py" << 'PYCLASS'
"""
${PASCAL_NAME} - Brief description.

This module provides...

Example:
    >>> obj = ${PASCAL_NAME}()
    >>> obj.do_something()

Created: $(date +%Y-%m-%d)
Author: Generated by Claude Code
"""

from __future__ import annotations

import logging
from typing import Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ${PASCAL_NAME}:
    """
    Brief description of ${PASCAL_NAME}.
    
    Attributes:
        name: Description of name attribute.
        config: Optional configuration dictionary.
    """
    
    name: str
    config: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Initialize after dataclass creation."""
        logger.debug(f"Initialized {self.__class__.__name__}: {self.name}")
    
    def process(self) -> bool:
        """
        Process the main operation.
        
        Returns:
            True if successful, False otherwise.
            
        Raises:
            ValueError: If configuration is invalid.
        """
        if not self.name:
            raise ValueError("Name cannot be empty")
        
        logger.info(f"Processing {self.name}")
        # TODO: Implement processing logic
        return True
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


def main() -> None:
    """Main entry point for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="${PASCAL_NAME} CLI")
    parser.add_argument("name", help="Name to process")
    parser.add_argument("-v", "--verbose", action="store_true")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    obj = ${PASCAL_NAME}(name=args.name)
    obj.process()


if __name__ == "__main__":
    main()
PYCLASS

echo "Created: ${SNAKE_NAME}.py"
fi
```

### Python Test Scaffold
```bash
if [ "$TYPE" = "test" ]; then
cat > "test_${SNAKE_NAME}.py" << 'PYTEST'
"""
Tests for ${SNAKE_NAME} module.

Run with: pytest test_${SNAKE_NAME}.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from ${SNAKE_NAME} import ${PASCAL_NAME}


class Test${PASCAL_NAME}:
    """Test suite for ${PASCAL_NAME}."""
    
    @pytest.fixture
    def instance(self) -> ${PASCAL_NAME}:
        """Create a test instance with default configuration."""
        return ${PASCAL_NAME}(name="test")
    
    @pytest.fixture
    def mock_config(self) -> dict:
        """Provide mock configuration."""
        return {
            "setting1": "value1",
            "setting2": 42,
        }
    
    # ==================== Initialization Tests ====================
    
    def test_init_with_name(self):
        """Should initialize with required name."""
        obj = ${PASCAL_NAME}(name="myname")
        assert obj.name == "myname"
    
    def test_init_with_config(self, mock_config):
        """Should accept optional configuration."""
        obj = ${PASCAL_NAME}(name="test", config=mock_config)
        assert obj.config == mock_config
    
    def test_init_default_config(self):
        """Should have empty config by default."""
        obj = ${PASCAL_NAME}(name="test")
        assert obj.config == {}
    
    # ==================== Core Functionality Tests ====================
    
    def test_process_success(self, instance):
        """Should return True on successful processing."""
        result = instance.process()
        assert result is True
    
    def test_process_empty_name_raises(self):
        """Should raise ValueError for empty name."""
        obj = ${PASCAL_NAME}(name="")
        with pytest.raises(ValueError, match="cannot be empty"):
            obj.process()
    
    # ==================== Edge Cases ====================
    
    @pytest.mark.parametrize("name,expected", [
        ("simple", True),
        ("with spaces", True),
        ("with-dashes", True),
        ("with_underscores", True),
    ])
    def test_process_various_names(self, name, expected):
        """Should handle various name formats."""
        obj = ${PASCAL_NAME}(name=name)
        assert obj.process() == expected
    
    # ==================== Representation Tests ====================
    
    def test_repr(self, instance):
        """Should have readable string representation."""
        assert "${PASCAL_NAME}" in repr(instance)
        assert "test" in repr(instance)
    
    # ==================== Integration Tests ====================
    
    @pytest.mark.integration
    def test_full_workflow(self, mock_config):
        """Should complete full workflow successfully."""
        obj = ${PASCAL_NAME}(name="integration", config=mock_config)
        assert obj.process() is True


# ==================== Fixtures for Complex Scenarios ====================

@pytest.fixture(scope="module")
def shared_resource():
    """Expensive resource shared across tests in module."""
    # Setup
    resource = {"initialized": True}
    yield resource
    # Teardown
    resource.clear()
PYTEST

echo "Created: test_${SNAKE_NAME}.py"
fi
```

### Bash Script Scaffold
```bash
if [ "$TYPE" = "script" ] || [ "$TYPE" = "bash" ]; then
cat > "${SNAKE_NAME}_v1.0.0.sh" << 'BASHSCRIPT'
#!/bin/bash
# ${SNAKE_NAME}_v1.0.0.sh - Brief description
#
# Usage:
#   ${SNAKE_NAME}_v1.0.0.sh [options] <arguments>
#
# Options:
#   -h, --help     Show this help message
#   -v, --verbose  Enable verbose output
#   -d, --dry-run  Show what would be done without executing
#
# Examples:
#   ${SNAKE_NAME}_v1.0.0.sh input.txt
#   ${SNAKE_NAME}_v1.0.0.sh -v --dry-run input.txt
#
# Dependencies:
#   - bash 4.0+
#   - standard Unix tools
#
# Created: $(date +%Y-%m-%d)
# Author: Generated by Claude Code
# Version: 1.0.0

set -euo pipefail

# ==================== Configuration ====================

readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_FILE="${SCRIPT_DIR}/logs/${SCRIPT_NAME%.sh}.log"

# Defaults
VERBOSE=false
DRY_RUN=false

# ==================== Logging ====================

setup_logging() {
    mkdir -p "$(dirname "$LOG_FILE")"
    exec 3>&1  # Save stdout
    exec 4>&2  # Save stderr
}

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    
    if [[ "$VERBOSE" == true ]] || [[ "$level" != "DEBUG" ]]; then
        case "$level" in
            ERROR)   echo -e "\033[31m[$level]\033[0m $message" >&4 ;;
            WARNING) echo -e "\033[33m[$level]\033[0m $message" >&3 ;;
            INFO)    echo -e "\033[32m[$level]\033[0m $message" >&3 ;;
            DEBUG)   echo -e "\033[36m[$level]\033[0m $message" >&3 ;;
            *)       echo "[$level] $message" >&3 ;;
        esac
    fi
}

log_info()    { log "INFO" "$@"; }
log_error()   { log "ERROR" "$@"; }
log_warning() { log "WARNING" "$@"; }
log_debug()   { log "DEBUG" "$@"; }

# ==================== Error Handling ====================

cleanup() {
    local exit_code=$?
    log_debug "Cleaning up (exit code: $exit_code)"
    # Add cleanup tasks here
    exit "$exit_code"
}

trap cleanup EXIT
trap 'log_error "Interrupted"; exit 130' INT TERM

die() {
    log_error "$@"
    exit 1
}

# ==================== Argument Parsing ====================

usage() {
    cat << EOF
Usage: $SCRIPT_NAME [options] <arguments>

Brief description of what this script does.

Options:
    -h, --help      Show this help message and exit
    -v, --verbose   Enable verbose output
    -d, --dry-run   Show what would be done without executing

Examples:
    $SCRIPT_NAME input.txt
    $SCRIPT_NAME -v --dry-run input.txt

EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                usage
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            --)
                shift
                break
                ;;
            -*)
                die "Unknown option: $1"
                ;;
            *)
                break
                ;;
        esac
    done
    
    # Remaining arguments
    ARGS=("$@")
}

# ==================== Validation ====================

validate_dependencies() {
    local deps=("bash" "grep" "sed" "awk")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            die "Required dependency not found: $dep"
        fi
    done
}

validate_input() {
    if [[ ${#ARGS[@]} -lt 1 ]]; then
        die "Missing required argument. Use -h for help."
    fi
    
    local input="${ARGS[0]}"
    if [[ ! -f "$input" ]] && [[ "$input" != "-" ]]; then
        die "Input file not found: $input"
    fi
}

# ==================== Main Logic ====================

run_command() {
    local cmd="$*"
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY RUN] Would execute: $cmd"
        return 0
    fi
    
    log_debug "Executing: $cmd"
    eval "$cmd"
}

process() {
    local input="${ARGS[0]}"
    
    log_info "Processing: $input"
    
    # TODO: Implement main logic here
    run_command "echo 'Processing $input'"
    
    log_info "Processing complete"
}

main() {
    setup_logging
    parse_args "$@"
    validate_dependencies
    validate_input
    
    log_info "Starting $SCRIPT_NAME v1.0.0"
    log_debug "Arguments: ${ARGS[*]}"
    log_debug "Verbose: $VERBOSE, Dry-run: $DRY_RUN"
    
    process
    
    log_info "Done"
}

# ==================== Entry Point ====================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
BASHSCRIPT

chmod +x "${SNAKE_NAME}_v1.0.0.sh"
echo "Created: ${SNAKE_NAME}_v1.0.0.sh"
fi
```

### WordPress Plugin Scaffold
```bash
if [ "$TYPE" = "plugin" ] || [ "$TYPE" = "wp-plugin" ]; then
mkdir -p "${SNAKE_NAME}"
cat > "${SNAKE_NAME}/${SNAKE_NAME}.php" << 'WPPLUGIN'
<?php
/**
 * Plugin Name: ${PASCAL_NAME}
 * Plugin URI: https://rundaverun.org/plugins/${SNAKE_NAME}
 * Description: Brief description of the plugin.
 * Version: 1.0.0
 * Author: Dave Biggers Campaign
 * Author URI: https://rundaverun.org
 * License: GPL-2.0+
 * Text Domain: ${SNAKE_NAME}
 *
 * @package ${PASCAL_NAME}
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Plugin constants
define('${UPPER_NAME}_VERSION', '1.0.0');
define('${UPPER_NAME}_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('${UPPER_NAME}_PLUGIN_URL', plugin_dir_url(__FILE__));

/**
 * Main plugin class.
 */
class ${PASCAL_NAME} {
    
    /**
     * Singleton instance.
     *
     * @var ${PASCAL_NAME}|null
     */
    private static ?${PASCAL_NAME} $instance = null;
    
    /**
     * Get singleton instance.
     *
     * @return ${PASCAL_NAME}
     */
    public static function get_instance(): ${PASCAL_NAME} {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    /**
     * Constructor.
     */
    private function __construct() {
        $this->init_hooks();
    }
    
    /**
     * Initialize WordPress hooks.
     */
    private function init_hooks(): void {
        add_action('init', [$this, 'init']);
        add_action('admin_menu', [$this, 'add_admin_menu']);
        add_action('admin_enqueue_scripts', [$this, 'enqueue_admin_scripts']);
        
        // AJAX handlers
        add_action('wp_ajax_${SNAKE_NAME}_action', [$this, 'handle_ajax']);
    }
    
    /**
     * Plugin initialization.
     */
    public function init(): void {
        load_plugin_textdomain(
            '${SNAKE_NAME}',
            false,
            dirname(plugin_basename(__FILE__)) . '/languages'
        );
    }
    
    /**
     * Add admin menu.
     */
    public function add_admin_menu(): void {
        add_menu_page(
            __('${PASCAL_NAME}', '${SNAKE_NAME}'),
            __('${PASCAL_NAME}', '${SNAKE_NAME}'),
            'manage_options',
            '${SNAKE_NAME}',
            [$this, 'render_admin_page'],
            'dashicons-admin-generic',
            30
        );
    }
    
    /**
     * Enqueue admin scripts.
     *
     * @param string $hook Current admin page hook.
     */
    public function enqueue_admin_scripts(string $hook): void {
        if ('toplevel_page_${SNAKE_NAME}' !== $hook) {
            return;
        }
        
        wp_enqueue_style(
            '${SNAKE_NAME}-admin',
            ${UPPER_NAME}_PLUGIN_URL . 'assets/css/admin.css',
            [],
            ${UPPER_NAME}_VERSION
        );
        
        wp_enqueue_script(
            '${SNAKE_NAME}-admin',
            ${UPPER_NAME}_PLUGIN_URL . 'assets/js/admin.js',
            ['jquery'],
            ${UPPER_NAME}_VERSION,
            true
        );
        
        wp_localize_script('${SNAKE_NAME}-admin', '${CAMEL_NAME}Ajax', [
            'ajaxurl' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('${SNAKE_NAME}_nonce'),
        ]);
    }
    
    /**
     * Render admin page.
     */
    public function render_admin_page(): void {
        if (!current_user_can('manage_options')) {
            wp_die(__('Unauthorized access', '${SNAKE_NAME}'));
        }
        
        include ${UPPER_NAME}_PLUGIN_DIR . 'templates/admin-page.php';
    }
    
    /**
     * Handle AJAX request.
     */
    public function handle_ajax(): void {
        check_ajax_referer('${SNAKE_NAME}_nonce', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_send_json_error(['message' => 'Unauthorized']);
        }
        
        // Sanitize input
        $action = isset($_POST['custom_action']) 
            ? sanitize_text_field(wp_unslash($_POST['custom_action'])) 
            : '';
        
        // Process action
        $result = $this->process_action($action);
        
        wp_send_json_success($result);
    }
    
    /**
     * Process custom action.
     *
     * @param string $action Action to process.
     * @return array Result data.
     */
    private function process_action(string $action): array {
        // TODO: Implement action processing
        return ['action' => $action, 'status' => 'processed'];
    }
}

// Initialize plugin
add_action('plugins_loaded', function() {
    ${PASCAL_NAME}::get_instance();
});

// Activation hook
register_activation_hook(__FILE__, function() {
    // Create database tables, set options, etc.
    update_option('${SNAKE_NAME}_version', ${UPPER_NAME}_VERSION);
});

// Deactivation hook
register_deactivation_hook(__FILE__, function() {
    // Clean up temporary data
});
WPPLUGIN

# Create directory structure
mkdir -p "${SNAKE_NAME}/assets/css"
mkdir -p "${SNAKE_NAME}/assets/js"
mkdir -p "${SNAKE_NAME}/templates"
mkdir -p "${SNAKE_NAME}/includes"

echo "Created: ${SNAKE_NAME}/ (WordPress plugin structure)"
fi
```

### MCP Tool Scaffold
```bash
if [ "$TYPE" = "mcp" ] || [ "$TYPE" = "mcp-tool" ]; then
cat > "${SNAKE_NAME}_tool.py" << 'MCPTOOL'
"""
MCP Tool: ${PASCAL_NAME}

Add to mcp-servers/general-server/server.py

Created: $(date +%Y-%m-%d)
"""

from mcp.server.fastmcp import FastMCP

# Add this function to server.py

@mcp.tool()
async def ${SNAKE_NAME}(
    param1: str,
    param2: int = 10,
    verbose: bool = False
) -> str:
    """
    Brief description of what this tool does.
    
    Args:
        param1: Description of param1
        param2: Description of param2 (default: 10)
        verbose: Enable verbose output
        
    Returns:
        Description of return value
        
    Example:
        result = await ${SNAKE_NAME}("input", param2=20)
    """
    try:
        # Validate input
        if not param1:
            return "Error: param1 is required"
        
        # Log operation
        logger.info(f"${SNAKE_NAME}: Processing {param1}")
        
        # TODO: Implement tool logic
        result = f"Processed: {param1} with param2={param2}"
        
        if verbose:
            result += f"\n[VERBOSE] Additional details..."
        
        return result
        
    except Exception as e:
        logger.error(f"${SNAKE_NAME} failed: {e}")
        return f"Error: {str(e)}"
MCPTOOL

echo "Created: ${SNAKE_NAME}_tool.py (MCP tool template)"
fi
```

## Usage
- `/scaffold class UserService` - Python class with dataclass
- `/scaffold test user_service` - Pytest test file
- `/scaffold script backup_database` - Bash script with full structure
- `/scaffold plugin volunteer-tracker` - WordPress plugin skeleton
- `/scaffold mcp file_processor` - MCP tool template
```

---

### 1.4 Create `/review-pr` Command

**Location:** `~/.claude/commands/review-pr.md`

**Purpose:** Comprehensive PR review with automated analysis.

```markdown
---
description: Full PR review - diff analysis, security scan, test check, complexity metrics
argument-hint: "[branch name, PR number, or empty for current branch]"
allowed-tools: ["Bash", "Read", "Grep"]
---

# Pull Request Review Assistant

Comprehensive automated code review for pull requests.

## Instructions

```bash
TARGET="${1:-$(git branch --show-current)}"
BASE="${2:-main}"

echo "# PR Review: $TARGET → $BASE"
echo "**Generated:** $(date)"
echo ""

# Ensure we have latest
git fetch origin --quiet
```

### 1. Change Summary
```bash
echo "## 📊 Change Summary"
echo ""

# Stats
STATS=$(git diff --stat "$BASE"..."$TARGET" | tail -1)
echo "**Overall:** $STATS"
echo ""

# By file type
echo "### By File Type"
echo "| Type | Files | Additions | Deletions |"
echo "|------|-------|-----------|-----------|"

for ext in py js php sh md css html; do
  FILES=$(git diff --name-only "$BASE"..."$TARGET" | grep -c "\.$ext$" 2>/dev/null || echo "0")
  if [ "$FILES" -gt 0 ]; then
    ADDS=$(git diff "$BASE"..."$TARGET" -- "*.$ext" | grep -c "^+" 2>/dev/null || echo "0")
    DELS=$(git diff "$BASE"..."$TARGET" -- "*.$ext" | grep -c "^-" 2>/dev/null || echo "0")
    echo "| .$ext | $FILES | +$ADDS | -$DELS |"
  fi
done
```

### 2. File-by-File Analysis
```bash
echo ""
echo "## 📁 Files Changed"
echo ""

for file in $(git diff --name-only "$BASE"..."$TARGET"); do
  ADDS=$(git diff "$BASE"..."$TARGET" -- "$file" | grep -c "^+" || echo "0")
  DELS=$(git diff "$BASE"..."$TARGET" -- "$file" | grep -c "^-" || echo "0")
  
  # Complexity indicator
  if [ "$ADDS" -gt 100 ]; then
    INDICATOR="🔴"
  elif [ "$ADDS" -gt 50 ]; then
    INDICATOR="🟡"
  else
    INDICATOR="🟢"
  fi
  
  echo "- $INDICATOR \`$file\` (+$ADDS/-$DELS)"
done
```

### 3. Security Scan
```bash
echo ""
echo "## 🔒 Security Check"
echo ""

ISSUES=0

# Check for secrets
if git diff "$BASE"..."$TARGET" | grep -qiE "(password|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]"; then
  echo "❌ **CRITICAL:** Potential hardcoded secrets detected!"
  git diff "$BASE"..."$TARGET" | grep -niE "(password|secret|api_key|token)\s*=\s*['\"]" | head -5
  ISSUES=$((ISSUES + 1))
else
  echo "✅ No hardcoded secrets detected"
fi

# Check for .env files
if git diff --name-only "$BASE"..."$TARGET" | grep -q "\.env"; then
  echo "❌ **CRITICAL:** .env file in diff!"
  ISSUES=$((ISSUES + 1))
else
  echo "✅ No .env files"
fi

# Check for SQL files
if git diff --name-only "$BASE"..."$TARGET" | grep -q "\.sql$"; then
  echo "⚠️ **WARNING:** SQL file in diff - verify no sensitive data"
  ISSUES=$((ISSUES + 1))
fi

# WordPress security
for file in $(git diff --name-only "$BASE"..."$TARGET" | grep "\.php$"); do
  if git diff "$BASE"..."$TARGET" -- "$file" | grep -q 'echo.*\$_'; then
    echo "⚠️ **WARNING:** Unescaped output in $file"
    ISSUES=$((ISSUES + 1))
  fi
  if git diff "$BASE"..."$TARGET" -- "$file" | grep -q '\$wpdb->query.*\$'; then
    echo "⚠️ **WARNING:** Potential SQL injection in $file"
    ISSUES=$((ISSUES + 1))
  fi
done

echo ""
echo "**Security Issues Found:** $ISSUES"
```

### 4. Test Coverage Check
```bash
echo ""
echo "## 🧪 Test Coverage"
echo ""

MISSING_TESTS=()

for file in $(git diff --name-only "$BASE"..."$TARGET" | grep -E "\.(py|js|php)$" | grep -v "test"); do
  BASENAME=$(basename "$file" | sed 's/\.[^.]*$//')
  
  # Look for corresponding test file
  if ! find tests test -name "*${BASENAME}*test*" -o -name "test_*${BASENAME}*" 2>/dev/null | grep -q .; then
    MISSING_TESTS+=("$file")
  fi
done

if [ ${#MISSING_TESTS[@]} -eq 0 ]; then
  echo "✅ All changed files appear to have tests"
else
  echo "⚠️ **Files possibly missing tests:**"
  for f in "${MISSING_TESTS[@]}"; do
    echo "- \`$f\`"
  done
fi

# Run tests if available
echo ""
echo "### Test Results"
if [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then
  pytest tests/ -v --tb=no -q 2>/dev/null | tail -5 || echo "Tests not run"
fi
```

### 5. Code Quality Metrics
```bash
echo ""
echo "## 📈 Code Quality"
echo ""

# Complexity analysis for Python files
PYTHON_FILES=$(git diff --name-only "$BASE"..."$TARGET" | grep "\.py$")
if [ -n "$PYTHON_FILES" ]; then
  echo "### Python Complexity (radon)"
  echo "\`\`\`"
  for f in $PYTHON_FILES; do
    if [ -f "$f" ]; then
      echo "--- $f ---"
      radon cc "$f" -a -s 2>/dev/null | tail -3 || echo "radon not available"
    fi
  done
  echo "\`\`\`"
fi

# Large functions check
echo ""
echo "### Large Functions (>50 lines)"
for file in $(git diff --name-only "$BASE"..."$TARGET" | grep -E "\.(py|js|php)$"); do
  if [ -f "$file" ]; then
    awk '/^def |^function |^    def /{name=$0; count=0} {count++} /^def |^function |^class |^}$/{if(count>50) print FILENAME":"NR": "name" ("count" lines)"}' "$file" 2>/dev/null
  fi
done || echo "No large functions detected"
```

### 6. Documentation Check
```bash
echo ""
echo "## 📝 Documentation"
echo ""

# Check if README updated for significant changes
if [ $(git diff --stat "$BASE"..."$TARGET" | tail -1 | awk '{print $4}') -gt 100 ]; then
  if git diff --name-only "$BASE"..."$TARGET" | grep -qi "readme"; then
    echo "✅ README updated"
  else
    echo "⚠️ Significant changes but README not updated"
  fi
fi

# Check for TODO/FIXME added
TODOS=$(git diff "$BASE"..."$TARGET" | grep "^+.*TODO\|^+.*FIXME\|^+.*HACK" | wc -l)
if [ "$TODOS" -gt 0 ]; then
  echo "ℹ️ **New TODO/FIXME comments:** $TODOS"
  git diff "$BASE"..."$TARGET" | grep "^+.*TODO\|^+.*FIXME" | head -5 | sed 's/^+/  /'
fi
```

### 7. Review Summary
```bash
echo ""
echo "## 📋 Review Summary"
echo ""

# Calculate review score
SCORE=100

# Deduct for issues
[ "$ISSUES" -gt 0 ] && SCORE=$((SCORE - ISSUES * 10))
[ ${#MISSING_TESTS[@]} -gt 0 ] && SCORE=$((SCORE - ${#MISSING_TESTS[@]} * 5))

if [ "$SCORE" -ge 90 ]; then
  echo "**Overall Score:** 🟢 $SCORE/100"
  echo "**Recommendation:** ✅ Ready to merge"
elif [ "$SCORE" -ge 70 ]; then
  echo "**Overall Score:** 🟡 $SCORE/100"
  echo "**Recommendation:** ⚠️ Address warnings before merge"
else
  echo "**Overall Score:** 🔴 $SCORE/100"
  echo "**Recommendation:** ❌ Requires changes"
fi

echo ""
echo "### Checklist"
echo "- [ ] Code reviewed for logic errors"
echo "- [ ] Security issues addressed"
echo "- [ ] Tests pass and cover changes"
echo "- [ ] Documentation updated if needed"
echo "- [ ] No hardcoded values or secrets"
```

## Usage
- `/review-pr` - Review current branch vs main
- `/review-pr feature/new-login` - Review specific branch
- `/review-pr feature/login develop` - Review against develop
```

---

### 1.5 Create `/explain` Command

**Location:** `~/.claude/commands/explain.md`

```markdown
---
description: Explain code, trace execution flow, generate documentation for complex logic
argument-hint: "<file:line>, <function_name>, or <file> for full analysis"
allowed-tools: ["Bash", "Read", "Grep"]
---

# Code Explainer

Analyze and document code for understanding and onboarding.

## Instructions

```bash
TARGET="$1"

# Determine target type
if [[ "$TARGET" == *":"* ]]; then
  MODE="line"
  FILE=$(echo "$TARGET" | cut -d: -f1)
  LINE=$(echo "$TARGET" | cut -d: -f2)
elif [[ -f "$TARGET" ]]; then
  MODE="file"
  FILE="$TARGET"
else
  MODE="search"
  SEARCH="$TARGET"
fi
```

### File Analysis Mode
```bash
if [ "$MODE" = "file" ]; then
  echo "# Code Analysis: $FILE"
  echo ""
  
  # File metadata
  echo "## 📋 File Info"
  echo "- **Path:** $FILE"
  echo "- **Size:** $(wc -l < "$FILE") lines"
  echo "- **Last Modified:** $(stat -c %y "$FILE" 2>/dev/null || stat -f %Sm "$FILE")"
  echo ""
  
  # Extract docstring/header
  echo "## 📖 Description"
  head -30 "$FILE" | grep -E "^#|^\"\"\"|^/\*|^ \*" | head -10
  echo ""
  
  # List classes/functions
  echo "## 🏗️ Structure"
  echo ""
  
  case "$FILE" in
    *.py)
      echo "### Classes"
      grep -n "^class " "$FILE" | while read line; do
        CLASS=$(echo "$line" | sed 's/class \([^(:]*\).*/\1/')
        LINENUM=$(echo "$line" | cut -d: -f1)
        echo "- \`$CLASS\` (line $LINENUM)"
      done
      
      echo ""
      echo "### Functions"
      grep -n "^def \|^    def " "$FILE" | while read line; do
        FUNC=$(echo "$line" | sed 's/.*def \([^(]*\).*/\1/')
        LINENUM=$(echo "$line" | cut -d: -f1)
        INDENT=$(echo "$line" | grep -o "^[[:space:]]*" | wc -c)
        [ "$INDENT" -gt 1 ] && PREFIX="  " || PREFIX=""
        echo "${PREFIX}- \`$FUNC()\` (line $LINENUM)"
      done
      ;;
      
    *.js|*.ts)
      echo "### Functions/Methods"
      grep -n "function \|const .* = \|=>" "$FILE" | head -20 | while read line; do
        echo "- $(echo "$line" | cut -d: -f1): $(echo "$line" | cut -d: -f2- | head -c 60)..."
      done
      ;;
      
    *.php)
      echo "### Classes"
      grep -n "^class " "$FILE"
      echo ""
      echo "### Functions"
      grep -n "function " "$FILE" | head -20
      ;;
  esac
  
  # Dependencies
  echo ""
  echo "## 📦 Dependencies"
  case "$FILE" in
    *.py)
      grep "^import \|^from " "$FILE" | sort -u
      ;;
    *.js|*.ts)
      grep "^import \|require(" "$FILE" | sort -u
      ;;
    *.php)
      grep "^use \|require\|include" "$FILE" | sort -u
      ;;
  esac
  
  # Find usages
  echo ""
  echo "## 🔗 Used By"
  BASENAME=$(basename "$FILE" | sed 's/\.[^.]*$//')
  grep -rl "import.*$BASENAME\|from.*$BASENAME\|require.*$BASENAME" --include="*.py" --include="*.js" --include="*.php" . 2>/dev/null | head -10
fi
```

### Line Context Mode
```bash
if [ "$MODE" = "line" ]; then
  echo "# Context for $FILE:$LINE"
  echo ""
  
  # Show surrounding code
  echo "## 📍 Code Context"
  echo "\`\`\`"
  sed -n "$((LINE-10)),$((LINE+10))p" "$FILE" | nl -ba -v $((LINE-10))
  echo "\`\`\`"
  echo ""
  
  # Find containing function
  echo "## 🏠 Containing Function"
  awk -v target="$LINE" '
    /^def |^class |^function |^    def / {
      name = $0
      start = NR
    }
    NR == target {
      print "- **Name:** " name
      print "- **Starts at line:** " start
    }
  ' "$FILE"
  
  # Variable tracking
  echo ""
  echo "## 🔍 Variables on This Line"
  sed -n "${LINE}p" "$FILE" | grep -oE '\$?[a-zA-Z_][a-zA-Z0-9_]*' | sort -u | while read var; do
    FIRST=$(grep -n "\b$var\b" "$FILE" | head -1 | cut -d: -f1)
    echo "- \`$var\` - first appears line $FIRST"
  done
fi
```

### Search Mode
```bash
if [ "$MODE" = "search" ]; then
  echo "# Search Results: $SEARCH"
  echo ""
  
  echo "## 📍 Definitions"
  grep -rn "def $SEARCH\|class $SEARCH\|function $SEARCH\|const $SEARCH" --include="*.py" --include="*.js" --include="*.php" . 2>/dev/null | head -10
  
  echo ""
  echo "## 📞 Usages"
  grep -rn "\b$SEARCH\b" --include="*.py" --include="*.js" --include="*.php" . 2>/dev/null | grep -v "def \|class \|function " | head -20
fi
```

## Usage
- `/explain src/utils.py` - Full file analysis
- `/explain src/utils.py:45` - Context around line 45
- `/explain calculate_total` - Find and explain function
```

---

### 1.6 Create `/health-check` Command

**Location:** `~/.claude/commands/health-check.md`

```markdown
---
description: Comprehensive system health check - hooks, MCP, paths, services
argument-hint: "[optional: 'full' for extended checks]"
allowed-tools: ["Bash", "Read"]
---

# System Health Check

Validate entire Claude Code environment.

## Instructions

```bash
FULL="${1:-quick}"
ISSUES=0
WARNINGS=0

echo "# 🏥 System Health Check"
echo "**Time:** $(date)"
echo "**Mode:** $FULL"
echo ""
```

### 1. Hook Validation
```bash
echo "## 🪝 Hooks Status"
echo ""

HOOKS_DIR="$HOME/.claude/hooks"

for hook in pre_compact.sh session_start_check.sh context_budget_monitor.sh pre_tool_use.sh post_edit_backup.sh permission_request.sh stop_hook.sh subagent_stop.sh; do
  HOOK_PATH="$HOOKS_DIR/$hook"
  if [ -f "$HOOK_PATH" ]; then
    if [ -x "$HOOK_PATH" ]; then
      # Test syntax
      if bash -n "$HOOK_PATH" 2>/dev/null; then
        echo "✅ $hook - OK"
      else
        echo "❌ $hook - Syntax error"
        ISSUES=$((ISSUES + 1))
      fi
    else
      echo "⚠️ $hook - Not executable"
      WARNINGS=$((WARNINGS + 1))
    fi
  else
    echo "⚪ $hook - Not found (optional)"
  fi
done
```

### 2. Required Paths
```bash
echo ""
echo "## 📁 Required Paths"
echo ""

PATHS=(
  "$HOME/.claude/skills:Skills directory"
  "$HOME/.claude/commands:Commands directory"
  "$HOME/.claude/logs:Logs directory"
  "$HOME/skippy/work:Work directory"
  "$HOME/skippy/reference:Reference directory"
)

for path_desc in "${PATHS[@]}"; do
  PATH_CHECK=$(echo "$path_desc" | cut -d: -f1)
  DESC=$(echo "$path_desc" | cut -d: -f2)
  
  if [ -d "$PATH_CHECK" ]; then
    COUNT=$(ls -1 "$PATH_CHECK" 2>/dev/null | wc -l)
    echo "✅ $DESC ($COUNT items)"
  else
    echo "❌ $DESC - MISSING: $PATH_CHECK"
    ISSUES=$((ISSUES + 1))
  fi
done
```

### 3. Critical Files
```bash
echo ""
echo "## 📄 Critical Files"
echo ""

FILES=(
  "$HOME/.claude/settings.json:Settings configuration"
  "$HOME/.claude/CLAUDE.md:Main instructions"
  "$HOME/skippy/reference/QUICK_FACTS_SHEET.md:Fact sheet"
)

for file_desc in "${FILES[@]}"; do
  FILE_CHECK=$(echo "$file_desc" | cut -d: -f1)
  DESC=$(echo "$file_desc" | cut -d: -f2)
  
  if [ -f "$FILE_CHECK" ]; then
    SIZE=$(wc -c < "$FILE_CHECK")
    echo "✅ $DESC ($SIZE bytes)"
  else
    echo "❌ $DESC - MISSING"
    ISSUES=$((ISSUES + 1))
  fi
done
```

### 4. MCP Servers
```bash
echo ""
echo "## 🔌 MCP Servers"
echo ""

# Check if MCP server files exist
MCP_DIR="$HOME/skippy/mcp-servers/general-server"
if [ -d "$MCP_DIR" ]; then
  echo "✅ MCP server directory exists"
  
  if [ -f "$MCP_DIR/server.py" ]; then
    TOOLS=$(grep -c "@mcp.tool" "$MCP_DIR/server.py" 2>/dev/null || echo "0")
    echo "✅ server.py ($TOOLS tools defined)"
  fi
  
  # Check for syntax errors
  if python3 -m py_compile "$MCP_DIR/server.py" 2>/dev/null; then
    echo "✅ Python syntax valid"
  else
    echo "❌ Python syntax errors"
    ISSUES=$((ISSUES + 1))
  fi
else
  echo "⚠️ MCP server directory not found"
  WARNINGS=$((WARNINGS + 1))
fi
```

### 5. Git Status
```bash
echo ""
echo "## 🔀 Git Status"
echo ""

if git rev-parse --git-dir > /dev/null 2>&1; then
  BRANCH=$(git branch --show-current)
  UNCOMMITTED=$(git status --porcelain | wc -l)
  AHEAD=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo "?")
  BEHIND=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo "?")
  
  echo "- **Branch:** $BRANCH"
  echo "- **Uncommitted:** $UNCOMMITTED files"
  echo "- **Ahead/Behind main:** +$AHEAD/-$BEHIND"
  
  if [ "$UNCOMMITTED" -gt 10 ]; then
    echo "⚠️ Many uncommitted changes"
    WARNINGS=$((WARNINGS + 1))
  fi
else
  echo "⚪ Not in a git repository"
fi
```

### 6. Disk Space
```bash
echo ""
echo "## 💾 Disk Space"
echo ""

USAGE=$(df -h "$HOME" | tail -1 | awk '{print $5}' | tr -d '%')
AVAIL=$(df -h "$HOME" | tail -1 | awk '{print $4}')

echo "- **Home Usage:** ${USAGE}%"
echo "- **Available:** $AVAIL"

if [ "$USAGE" -gt 90 ]; then
  echo "❌ Disk space critical!"
  ISSUES=$((ISSUES + 1))
elif [ "$USAGE" -gt 80 ]; then
  echo "⚠️ Disk space low"
  WARNINGS=$((WARNINGS + 1))
else
  echo "✅ Disk space OK"
fi
```

### 7. Recent Compactions
```bash
echo ""
echo "## 🗜️ Recent Compactions"
echo ""

COMPACT_DIR="$HOME/.claude/compactions"
if [ -d "$COMPACT_DIR" ]; then
  RECENT=$(ls -1t "$COMPACT_DIR" 2>/dev/null | head -5)
  if [ -n "$RECENT" ]; then
    echo "Last 5 compactions:"
    echo "$RECENT" | while read dir; do
      echo "- $dir"
    done
  else
    echo "No compactions recorded"
  fi
else
  echo "Compaction directory not found"
fi
```

### 8. Extended Checks (Full Mode)
```bash
if [ "$FULL" = "full" ]; then
  echo ""
  echo "## 🔬 Extended Checks"
  echo ""
  
  # Python environment
  echo "### Python Environment"
  echo "- **Version:** $(python3 --version)"
  echo "- **Pip packages:** $(pip list 2>/dev/null | wc -l)"
  
  # Key packages
  for pkg in pytest black flake8 radon bandit; do
    if pip show "$pkg" &>/dev/null; then
      echo "✅ $pkg installed"
    else
      echo "⚪ $pkg not installed"
    fi
  done
  
  # WordPress CLI
  echo ""
  echo "### WordPress CLI"
  if command -v wp &>/dev/null; then
    echo "✅ WP-CLI installed: $(wp --version 2>/dev/null)"
  else
    echo "⚠️ WP-CLI not found"
  fi
  
  # Skill statistics
  echo ""
  echo "### Skill Statistics"
  SKILL_COUNT=$(find "$HOME/.claude/skills" -name "SKILL.md" 2>/dev/null | wc -l)
  SKILL_LINES=$(find "$HOME/.claude/skills" -name "SKILL.md" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')
  echo "- **Skills:** $SKILL_COUNT"
  echo "- **Total Lines:** $SKILL_LINES"
  
  # Empty resource directories
  EMPTY=$(find "$HOME/.claude/skills" -type d -name "resources" -empty 2>/dev/null | wc -l)
  if [ "$EMPTY" -gt 0 ]; then
    echo "⚠️ Empty resource directories: $EMPTY"
  fi
fi
```

### Summary
```bash
echo ""
echo "---"
echo ""
echo "## 📊 Summary"
echo ""

if [ "$ISSUES" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
  echo "# ✅ All Systems Healthy"
elif [ "$ISSUES" -eq 0 ]; then
  echo "# ⚠️ Healthy with $WARNINGS warnings"
else
  echo "# ❌ $ISSUES issues, $WARNINGS warnings"
fi

echo ""
echo "- **Issues:** $ISSUES"
echo "- **Warnings:** $WARNINGS"
echo "- **Checked at:** $(date)"
```

## Usage
- `/health-check` - Quick health check
- `/health-check full` - Extended diagnostics
```

---

## Phase 2: New Hooks (Automation)

### 2.1 Create Auto-Lint Hook

**Location:** `~/.claude/hooks/post_edit_lint.sh`

**Purpose:** Automatically lint/format files after Claude edits them.

```bash
#!/bin/bash
# post_edit_lint.sh - Auto-lint files after edits
# Hook: PostToolUse (matcher: Edit|Write)
# Version: 1.0.0
#
# Automatically formats and lints files after Claude edits them.
# Non-blocking - errors are logged but don't stop execution.

set -uo pipefail

# Read input
INPUT=$(cat)

# Extract file path
FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('file_path', data.get('path', '')))
except:
    print('')
" 2>/dev/null)

[ -z "$FILE_PATH" ] && exit 0
[ ! -f "$FILE_PATH" ] && exit 0

# Log directory
LOG_DIR="$HOME/.claude/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/auto_lint.log"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# Lint based on file type
case "$FILE_PATH" in
  *.py)
    log "Linting Python: $FILE_PATH"
    
    # Format with black (if available)
    if command -v black &>/dev/null; then
      black "$FILE_PATH" --quiet 2>/dev/null && log "  black: OK" || log "  black: FAILED"
    fi
    
    # Sort imports (if available)
    if command -v isort &>/dev/null; then
      isort "$FILE_PATH" --quiet 2>/dev/null && log "  isort: OK" || log "  isort: FAILED"
    fi
    
    # Type check (non-blocking)
    if command -v mypy &>/dev/null; then
      MYPY_RESULT=$(mypy "$FILE_PATH" --ignore-missing-imports 2>&1 | head -3)
      log "  mypy: $MYPY_RESULT"
    fi
    ;;
    
  *.js|*.jsx|*.ts|*.tsx)
    log "Linting JavaScript/TypeScript: $FILE_PATH"
    
    # Prettier
    if command -v npx &>/dev/null && [ -f "package.json" ]; then
      npx prettier --write "$FILE_PATH" 2>/dev/null && log "  prettier: OK" || log "  prettier: FAILED"
    fi
    
    # ESLint (check only)
    if command -v npx &>/dev/null; then
      ESLINT_RESULT=$(npx eslint "$FILE_PATH" --format compact 2>&1 | head -3)
      [ -n "$ESLINT_RESULT" ] && log "  eslint: $ESLINT_RESULT"
    fi
    ;;
    
  *.sh)
    log "Checking shell script: $FILE_PATH"
    
    # ShellCheck
    if command -v shellcheck &>/dev/null; then
      SC_RESULT=$(shellcheck "$FILE_PATH" 2>&1 | head -5)
      if [ -n "$SC_RESULT" ]; then
        log "  shellcheck warnings: $SC_RESULT"
      else
        log "  shellcheck: OK"
      fi
    fi
    
    # Ensure executable
    if [ ! -x "$FILE_PATH" ]; then
      chmod +x "$FILE_PATH"
      log "  Made executable"
    fi
    ;;
    
  *.php)
    log "Checking PHP: $FILE_PATH"
    
    # Syntax check
    PHP_RESULT=$(php -l "$FILE_PATH" 2>&1)
    if echo "$PHP_RESULT" | grep -q "No syntax errors"; then
      log "  php -l: OK"
    else
      log "  php -l: $PHP_RESULT"
    fi
    
    # PHP CodeSniffer (if available)
    if command -v phpcs &>/dev/null; then
      PHPCS_RESULT=$(phpcs "$FILE_PATH" --standard=WordPress --report=summary 2>&1 | tail -3)
      log "  phpcs: $PHPCS_RESULT"
    fi
    ;;
    
  *.json)
    log "Validating JSON: $FILE_PATH"
    
    if python3 -m json.tool "$FILE_PATH" > /dev/null 2>&1; then
      log "  JSON: Valid"
    else
      log "  JSON: INVALID"
    fi
    ;;
    
  *.md)
    log "Checking Markdown: $FILE_PATH"
    
    # Check for common issues
    if grep -q "	" "$FILE_PATH"; then
      log "  Warning: Contains tabs (consider spaces)"
    fi
    ;;
esac

exit 0
```

---

### 2.2 Create Dev Context Tracker Hook

**Location:** `~/.claude/hooks/dev_context_tracker.sh`

**Purpose:** Track development context for smarter session continuity.

```bash
#!/bin/bash
# dev_context_tracker.sh - Track development context
# Hook: UserPromptSubmit
# Version: 1.0.0
#
# Maintains a context file with current development state
# for better session continuity and smarter assistance.

set -uo pipefail

CONTEXT_FILE="$HOME/.claude/dev_context.json"
CONTEXT_DIR=$(dirname "$CONTEXT_FILE")
mkdir -p "$CONTEXT_DIR"

# Get current context
get_git_info() {
  if git rev-parse --git-dir > /dev/null 2>&1; then
    BRANCH=$(git branch --show-current 2>/dev/null || echo "detached")
    UNCOMMITTED=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    LAST_COMMIT=$(git log -1 --format='%s' 2>/dev/null || echo "none")
    REPO=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" || echo "unknown")
  else
    BRANCH="none"
    UNCOMMITTED="0"
    LAST_COMMIT="none"
    REPO="none"
  fi
}

get_recent_files() {
  # Get recently modified files in last hour
  find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.php" -o -name "*.sh" \) \
    -mmin -60 2>/dev/null | head -10 | python3 -c "
import sys, json
files = [line.strip() for line in sys.stdin if line.strip()]
print(json.dumps(files))
" 2>/dev/null || echo "[]"
}

get_test_status() {
  # Quick test check
  if [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then
    LAST_TEST=$(find . -name ".pytest_cache" -mmin -30 2>/dev/null | head -1)
    if [ -n "$LAST_TEST" ]; then
      echo "recent"
    else
      echo "stale"
    fi
  else
    echo "unknown"
  fi
}

# Gather context
get_git_info
RECENT_FILES=$(get_recent_files)
TEST_STATUS=$(get_test_status)
VENV="${VIRTUAL_ENV:-none}"
PWD_SHORT="${PWD/#$HOME/~}"

# Write context file
cat > "$CONTEXT_FILE" << EOF
{
  "last_updated": "$(date -Iseconds)",
  "working_directory": "$PWD_SHORT",
  "git": {
    "repository": "$REPO",
    "branch": "$BRANCH",
    "uncommitted_files": $UNCOMMITTED,
    "last_commit": "$LAST_COMMIT"
  },
  "recent_files": $RECENT_FILES,
  "test_status": "$TEST_STATUS",
  "virtual_env": "$VENV",
  "session_start": "${SESSION_START:-$(date -Iseconds)}"
}
EOF

exit 0
```

---

### 2.3 Create Security Scan Hook

**Location:** `~/.claude/hooks/security_scan.sh`

**Purpose:** Scan for security issues before commits and in edited files.

```bash
#!/bin/bash
# security_scan.sh - Security scanning hook
# Hook: PreToolUse (for git commands) and PostToolUse (for file edits)
# Version: 1.0.0
#
# Scans for security issues in code changes.

set -uo pipefail

INPUT=$(cat)
LOG_DIR="$HOME/.claude/logs"
mkdir -p "$LOG_DIR"
SECURITY_LOG="$LOG_DIR/security_scan.log"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$SECURITY_LOG"
}

# Extract context
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")

scan_file() {
  local file="$1"
  local issues=0
  
  [ ! -f "$file" ] && return 0
  
  # Hardcoded secrets
  if grep -qE "(password|secret|api_key|token|private_key)\s*=\s*['\"][^'\"]{8,}['\"]" "$file" 2>/dev/null; then
    log "SECURITY: Potential hardcoded secret in $file"
    issues=$((issues + 1))
  fi
  
  # AWS keys
  if grep -qE "AKIA[0-9A-Z]{16}" "$file" 2>/dev/null; then
    log "SECURITY: Potential AWS key in $file"
    issues=$((issues + 1))
  fi
  
  # Private keys
  if grep -q "BEGIN.*PRIVATE KEY" "$file" 2>/dev/null; then
    log "SECURITY: Private key in $file"
    issues=$((issues + 1))
  fi
  
  # PHP specific
  if [[ "$file" == *.php ]]; then
    # SQL injection
    if grep -qE '\$wpdb->query\s*\([^)]*\$' "$file" 2>/dev/null; then
      log "SECURITY: Potential SQL injection in $file (use \$wpdb->prepare)"
      issues=$((issues + 1))
    fi
    
    # XSS
    if grep -qE 'echo\s+\$_(GET|POST|REQUEST)' "$file" 2>/dev/null; then
      log "SECURITY: Potential XSS in $file (escape output)"
      issues=$((issues + 1))
    fi
    
    # Direct file access
    if ! grep -q "defined.*ABSPATH" "$file" 2>/dev/null; then
      if ! grep -q "defined.*WPINC" "$file" 2>/dev/null; then
        log "SECURITY: No direct access protection in $file"
        issues=$((issues + 1))
      fi
    fi
  fi
  
  # Python specific
  if [[ "$file" == *.py ]]; then
    # eval/exec
    if grep -qE '\beval\s*\(|\bexec\s*\(' "$file" 2>/dev/null; then
      log "SECURITY: Dangerous eval/exec in $file"
      issues=$((issues + 1))
    fi
    
    # Shell injection
    if grep -qE 'subprocess\.(call|run|Popen).*shell\s*=\s*True' "$file" 2>/dev/null; then
      log "SECURITY: Shell=True in subprocess in $file"
      issues=$((issues + 1))
    fi
    
    # Pickle (insecure deserialization)
    if grep -qE 'pickle\.load' "$file" 2>/dev/null; then
      log "SECURITY: Pickle usage (insecure deserialization) in $file"
      issues=$((issues + 1))
    fi
  fi
  
  return $issues
}

# For git commit commands, scan staged files
if [ "$TOOL_NAME" = "Bash" ]; then
  COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")
  
  if [[ "$COMMAND" == *"git commit"* ]] || [[ "$COMMAND" == *"git push"* ]]; then
    log "Scanning staged files before git operation..."
    
    TOTAL_ISSUES=0
    for file in $(git diff --cached --name-only 2>/dev/null); do
      scan_file "$file"
      TOTAL_ISSUES=$((TOTAL_ISSUES + $?))
    done
    
    if [ "$TOTAL_ISSUES" -gt 0 ]; then
      log "BLOCKED: $TOTAL_ISSUES security issues found"
      echo "{\"decision\": \"block\", \"reason\": \"Security scan found $TOTAL_ISSUES potential issues. Check $SECURITY_LOG for details.\"}"
      exit 0
    fi
  fi
fi

# For file edits, scan the edited file
if [ "$TOOL_NAME" = "Edit" ] || [ "$TOOL_NAME" = "Write" ]; then
  FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',d.get('tool_input',{}).get('path','')))" 2>/dev/null || echo "")
  
  if [ -n "$FILE_PATH" ]; then
    scan_file "$FILE_PATH"
    # Don't block edits, just log
  fi
fi

exit 0
```

---

### 2.4 Update settings.json for New Hooks

**Add to existing hooks configuration:**

```json
{
  "hooks": {
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
            "timeout": 10000
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
          },
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/dev_context_tracker.sh",
            "timeout": 3000
          }
        ]
      }
    ],
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
            "command": "$HOME/.claude/hooks/security_scan.sh",
            "timeout": 5000
          }
        ]
      }
    ]
  }
}
```

---

## Phase 3: Security Enhancements

### 3.1 Create Secrets Scanner Skill

**Location:** `~/.claude/skills/secrets-scanner/SKILL.md`

```markdown
---
name: secrets-scanner
description: Scan for exposed secrets, API keys, passwords, and sensitive data. Auto-invoke before commits, deployments, or when security is mentioned.
---

# Secrets Scanner Skill

**Version:** 1.0.0
**Last Updated:** 2025-12-01
**Priority:** CRITICAL
**Auto-Invoke:** Before git commits, deployments, or security discussions

## When to Use This Skill

Auto-invoke when:
- User mentions "commit", "push", "deploy", "publish"
- Security review or audit requested
- Checking for exposed credentials
- Pre-merge validation

## Quick Scan Commands

### Full Repository Scan
```bash
echo "## Secrets Scan Results"
echo ""

ISSUES=0

# 1. High-entropy strings (potential keys)
echo "### High-Entropy Strings"
grep -rE "[A-Za-z0-9+/]{40,}" --include="*.py" --include="*.js" --include="*.php" --include="*.sh" . 2>/dev/null | grep -v "node_modules\|\.git\|vendor" | head -10

# 2. Common secret patterns
echo ""
echo "### Secret Patterns"

# AWS Keys
AWS=$(grep -rE "AKIA[0-9A-Z]{16}" --include="*.py" --include="*.js" --include="*.env*" . 2>/dev/null | grep -v "\.git")
if [ -n "$AWS" ]; then
  echo "❌ AWS Key found:"
  echo "$AWS"
  ISSUES=$((ISSUES + 1))
fi

# Private Keys
PRIVKEY=$(grep -rl "BEGIN.*PRIVATE KEY" . 2>/dev/null | grep -v "\.git\|node_modules")
if [ -n "$PRIVKEY" ]; then
  echo "❌ Private key files:"
  echo "$PRIVKEY"
  ISSUES=$((ISSUES + 1))
fi

# Hardcoded passwords
PASSWORDS=$(grep -rnE "(password|passwd|pwd)\s*=\s*['\"][^'\"]{4,}['\"]" --include="*.py" --include="*.js" --include="*.php" . 2>/dev/null | grep -v "test\|example\|sample\|\.git")
if [ -n "$PASSWORDS" ]; then
  echo "❌ Hardcoded passwords:"
  echo "$PASSWORDS" | head -10
  ISSUES=$((ISSUES + 1))
fi

# API Keys
APIKEYS=$(grep -rnE "(api_key|apikey|api-key)\s*[:=]\s*['\"][^'\"]{10,}['\"]" --include="*.py" --include="*.js" --include="*.php" --include="*.json" . 2>/dev/null | grep -v "example\|test\|\.git")
if [ -n "$APIKEYS" ]; then
  echo "❌ API keys:"
  echo "$APIKEYS" | head -10
  ISSUES=$((ISSUES + 1))
fi

# Database connection strings
DBCONN=$(grep -rnE "(mysql|postgres|mongodb)://[^:]+:[^@]+@" --include="*.py" --include="*.js" --include="*.php" . 2>/dev/null | grep -v "example\|test\|\.git")
if [ -n "$DBCONN" ]; then
  echo "❌ Database connection strings:"
  echo "$DBCONN"
  ISSUES=$((ISSUES + 1))
fi

# 3. Sensitive files that shouldn't be committed
echo ""
echo "### Sensitive Files Check"

SENSITIVE_PATTERNS=(
  "*.pem"
  "*.key"
  "*.p12"
  "*.pfx"
  "id_rsa*"
  "id_dsa*"
  "id_ecdsa*"
  "id_ed25519*"
  ".env"
  ".env.*"
  "*.sql"
  "credentials.json"
  "service-account*.json"
)

for pattern in "${SENSITIVE_PATTERNS[@]}"; do
  FOUND=$(find . -name "$pattern" -not -path "./.git/*" 2>/dev/null)
  if [ -n "$FOUND" ]; then
    echo "⚠️ Found: $pattern"
    echo "$FOUND"
    ISSUES=$((ISSUES + 1))
  fi
done

# 4. Check .gitignore
echo ""
echo "### .gitignore Verification"

SHOULD_IGNORE=(
  ".env"
  "*.pem"
  "*.key"
  "*.sql"
  "credentials.json"
  "node_modules"
  "__pycache__"
  ".pytest_cache"
)

if [ -f ".gitignore" ]; then
  for pattern in "${SHOULD_IGNORE[@]}"; do
    if grep -q "^${pattern}$\|^${pattern}/" .gitignore 2>/dev/null; then
      echo "✅ $pattern is ignored"
    else
      echo "⚠️ $pattern NOT in .gitignore"
    fi
  done
else
  echo "❌ No .gitignore file found!"
  ISSUES=$((ISSUES + 1))
fi

echo ""
echo "---"
echo "**Total Issues Found:** $ISSUES"

if [ "$ISSUES" -eq 0 ]; then
  echo "✅ No secrets detected"
else
  echo "❌ Action required before commit!"
fi
```

### Git History Scan
```bash
# Check git history for accidentally committed secrets
echo "## Git History Scan"

# Recent commits with potential secrets
git log --all --oneline -20 --format="%h %s" | while read hash msg; do
  if git show "$hash" 2>/dev/null | grep -qE "(password|secret|api_key|private_key)"; then
    echo "⚠️ $hash: $msg - may contain secrets"
  fi
done

# Large file additions (potential data dumps)
git log --all --oneline -20 --diff-filter=A --format="%h %s" | while read hash msg; do
  LARGE=$(git show --stat "$hash" 2>/dev/null | grep -E "\+[0-9]{4,}")
  if [ -n "$LARGE" ]; then
    echo "⚠️ $hash: Large file added - $msg"
  fi
done
```

### Pre-Commit Integration
```bash
# Install as git pre-commit hook
cat > .git/hooks/pre-commit << 'HOOK'
#!/bin/bash
# Secrets pre-commit hook

# Quick scan staged files
ISSUES=0

for file in $(git diff --cached --name-only); do
  # Skip binary files
  file -b "$file" 2>/dev/null | grep -q "text" || continue
  
  # Check for secrets
  if grep -qE "(password|secret|api_key|private_key)\s*=\s*['\"][^'\"]+['\"]" "$file" 2>/dev/null; then
    echo "❌ Potential secret in: $file"
    ISSUES=$((ISSUES + 1))
  fi
  
  # Check for AWS keys
  if grep -qE "AKIA[0-9A-Z]{16}" "$file" 2>/dev/null; then
    echo "❌ AWS key pattern in: $file"
    ISSUES=$((ISSUES + 1))
  fi
done

if [ "$ISSUES" -gt 0 ]; then
  echo ""
  echo "Commit blocked: $ISSUES potential secrets found"
  echo "Review files and use git commit --no-verify to bypass (not recommended)"
  exit 1
fi

exit 0
HOOK

chmod +x .git/hooks/pre-commit
echo "Pre-commit secrets hook installed"
```

## Remediation Steps

When secrets are found:

1. **Remove from code:**
   ```bash
   # Replace with environment variable
   sed -i 's/api_key = "ACTUAL_KEY"/api_key = os.getenv("API_KEY")/' file.py
   ```

2. **Add to .gitignore:**
   ```bash
   echo ".env" >> .gitignore
   echo "*.pem" >> .gitignore
   ```

3. **Rotate compromised credentials:**
   - AWS: Generate new access keys in IAM console
   - API keys: Revoke and regenerate in service dashboard
   - Passwords: Change immediately

4. **Clean git history (if committed):**
   ```bash
   # Use BFG Repo-Cleaner or git filter-branch
   # WARNING: Rewrites history
   bfg --replace-text secrets.txt repo.git
   ```

## Integration

Works with:
- **security-operations** - For comprehensive security reviews
- **git-workflow** - Pre-commit validation
- **pre-commit command** - Automated checking
```

---

### 3.2 Enhance pre_tool_use.sh with Additional Protections

**Add these checks to existing pre_tool_use.sh:**

```bash
# Add after existing dangerous patterns check

# =========================================
# Enhanced Security Checks
# =========================================

# 1. Prevent credential file access
CREDENTIAL_PATTERNS=(
  ".aws/credentials"
  ".ssh/id_"
  ".gnupg/"
  ".netrc"
  ".npmrc"
  ".pypirc"
  "credentials.json"
  "service-account"
  ".google/credentials"
)

for pattern in "${CREDENTIAL_PATTERNS[@]}"; do
  if [[ "$COMMAND" == *"$pattern"* ]] && [[ "$COMMAND" != *"cat"*">"* ]]; then
    # Allow reading but not writing to credential files
    if [[ "$COMMAND" == *">"* ]] || [[ "$COMMAND" == *"rm"* ]] || [[ "$COMMAND" == *"mv"* ]]; then
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] BLOCKED CREDENTIAL MODIFICATION: $COMMAND" >> "$LOG_DIR/blocked_commands.log"
      echo '{"decision": "block", "reason": "Modification of credential files is not allowed: '"$pattern"'"}'
      exit 0
    fi
  fi
done

# 2. Block curl/wget to suspicious destinations
if [[ "$COMMAND" == *"curl "* ]] || [[ "$COMMAND" == *"wget "* ]]; then
  # Block posting to unknown endpoints
  if [[ "$COMMAND" == *"-X POST"* ]] || [[ "$COMMAND" == *"--data"* ]] || [[ "$COMMAND" == *"-d "* ]]; then
    # Allow known safe endpoints
    SAFE_ENDPOINTS=(
      "api.github.com"
      "api.anthropic.com"
      "rundaverun.org"
      "localhost"
      "127.0.0.1"
    )
    
    IS_SAFE=false
    for endpoint in "${SAFE_ENDPOINTS[@]}"; do
      if [[ "$COMMAND" == *"$endpoint"* ]]; then
        IS_SAFE=true
        break
      fi
    done
    
    if [ "$IS_SAFE" = false ]; then
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] BLOCKED OUTBOUND POST: $COMMAND" >> "$LOG_DIR/blocked_commands.log"
      echo '{"decision": "block", "reason": "POST requests to unknown endpoints require approval"}'
      exit 0
    fi
  fi
fi

# 3. Prevent accidental database destruction
if [[ "$COMMAND" == *"DROP DATABASE"* ]] || [[ "$COMMAND" == *"DROP TABLE"* ]]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] BLOCKED DB DROP: $COMMAND" >> "$LOG_DIR/blocked_commands.log"
  echo '{"decision": "block", "reason": "DROP DATABASE/TABLE requires explicit approval"}'
  exit 0
fi

# 4. Block mass file operations outside work directories
if [[ "$COMMAND" == *"rm -rf"* ]] || [[ "$COMMAND" == *"rm -r"* ]]; then
  SAFE_DIRS=(
    "/home/dave/skippy/work"
    "/tmp"
    "$HOME/.cache"
    "node_modules"
    "__pycache__"
    ".pytest_cache"
  )
  
  IS_SAFE=false
  for dir in "${SAFE_DIRS[@]}"; do
    if [[ "$COMMAND" == *"$dir"* ]]; then
      IS_SAFE=true
      break
    fi
  done
  
  if [ "$IS_SAFE" = false ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] BLOCKED MASS DELETE: $COMMAND" >> "$LOG_DIR/blocked_commands.log"
    echo '{"decision": "block", "reason": "Mass deletion outside work directories requires approval"}'
    exit 0
  fi
fi

# 5. Rate limit API calls
RATE_LIMIT_FILE="$LOG_DIR/api_rate_limit.txt"
if [[ "$COMMAND" == *"curl"* ]] || [[ "$COMMAND" == *"wget"* ]] || [[ "$COMMAND" == *"requests."* ]]; then
  MINUTE=$(date +%Y%m%d%H%M)
  COUNT=$(grep -c "^$MINUTE" "$RATE_LIMIT_FILE" 2>/dev/null || echo "0")
  
  if [ "$COUNT" -gt 30 ]; then
    echo '{"decision": "block", "reason": "API rate limit exceeded (30/minute). Wait and retry."}'
    exit 0
  fi
  
  echo "$MINUTE" >> "$RATE_LIMIT_FILE"
  
  # Cleanup old entries
  tail -100 "$RATE_LIMIT_FILE" > "$RATE_LIMIT_FILE.tmp" && mv "$RATE_LIMIT_FILE.tmp" "$RATE_LIMIT_FILE"
fi
```

---

## Phase 4: Skill Consolidation

### 4.1 Merge Debugging Skills

**Current:** `advanced-debugging`, `diagnostic-debugging`
**New:** `~/.claude/skills/debugging/SKILL.md`

```markdown
---
name: debugging
description: Comprehensive debugging skill combining advanced and diagnostic techniques. Auto-invoke for error investigation, log analysis, performance issues, and troubleshooting.
---

# Debugging Skill

**Version:** 2.0.0
**Last Updated:** 2025-12-01
**Merged From:** advanced-debugging, diagnostic-debugging
**Auto-Invoke:** Yes - for any debugging, error investigation, or troubleshooting

## When to Use This Skill

Auto-invoke when:
- User reports an error or bug
- Log analysis is needed
- Performance issues mentioned
- Stack traces need interpretation
- System troubleshooting required

## Quick Diagnostics

### Error Investigation Workflow
```bash
# 1. Capture error context
ERROR_LOG="$HOME/skippy/work/debug/$(date +%Y%m%d_%H%M%S)_investigation"
mkdir -p "$ERROR_LOG"

# 2. Gather system state
{
  echo "## System State at $(date)"
  echo ""
  echo "### Process Info"
  ps aux | head -20
  echo ""
  echo "### Memory"
  free -h
  echo ""
  echo "### Disk"
  df -h
  echo ""
  echo "### Recent Errors"
  journalctl --since "1 hour ago" -p err 2>/dev/null | tail -20 || dmesg | tail -20
} > "$ERROR_LOG/system_state.md"

# 3. Application logs
{
  echo "## Application Logs"
  
  # Claude logs
  echo "### Claude Logs"
  tail -50 ~/.claude/logs/*.log 2>/dev/null
  
  # WordPress logs
  echo ""
  echo "### WordPress Debug"
  WP_LOG="/home/dave/skippy/rundaverun_local_site/app/public/wp-content/debug.log"
  [ -f "$WP_LOG" ] && tail -50 "$WP_LOG"
  
  # PHP logs
  echo ""
  echo "### PHP Errors"
  tail -50 /var/log/php*.log 2>/dev/null
} > "$ERROR_LOG/app_logs.md"
```

### Stack Trace Analysis
```bash
analyze_traceback() {
  local traceback="$1"
  
  echo "## Stack Trace Analysis"
  echo ""
  
  # Python traceback
  if echo "$traceback" | grep -q "Traceback\|File.*line"; then
    echo "### Python Traceback"
    echo "$traceback" | grep -oP 'File "[^"]+", line \d+' | while read match; do
      FILE=$(echo "$match" | grep -oP '(?<=File ")[^"]+')
      LINE=$(echo "$match" | grep -oP '(?<=line )\d+')
      echo ""
      echo "**$FILE:$LINE**"
      [ -f "$FILE" ] && sed -n "$((LINE-2)),$((LINE+2))p" "$FILE" | nl -ba -v $((LINE-2))
    done
  fi
  
  # JavaScript stack
  if echo "$traceback" | grep -q "at .*("; then
    echo "### JavaScript Stack"
    echo "$traceback" | grep -oP 'at [^\(]+\([^\)]+\)' | head -10
  fi
  
  # PHP stack
  if echo "$traceback" | grep -q "Stack trace:\|#[0-9]"; then
    echo "### PHP Stack"
    echo "$traceback" | grep -E "^#[0-9]|in .*\.php"
  fi
}
```

### Log Analysis
```bash
# Find errors in logs
find_errors() {
  local log_path="${1:-.}"
  local hours="${2:-24}"
  
  echo "## Errors in Last $hours Hours"
  echo ""
  
  find "$log_path" -name "*.log" -mmin -$((hours * 60)) -exec grep -l -i "error\|exception\|fatal\|critical" {} \; 2>/dev/null | while read log; do
    echo "### $log"
    grep -i "error\|exception\|fatal\|critical" "$log" | tail -10
    echo ""
  done
}

# Analyze error frequency
error_frequency() {
  local log_file="$1"
  
  echo "## Error Frequency Analysis"
  grep -i "error" "$log_file" | \
    sed 's/\[.*\]/[TIME]/' | \
    sort | uniq -c | sort -rn | head -10
}
```

### Performance Debugging
```bash
# Profile Python code
profile_python() {
  local script="$1"
  python3 -m cProfile -s cumtime "$script" 2>&1 | head -30
}

# Memory profiling
memory_profile() {
  local pid="${1:-$$}"
  
  echo "## Memory Profile for PID $pid"
  ps -o pid,ppid,rss,vsz,pmem,comm -p "$pid"
  
  # If available, use more detailed tools
  if command -v smem &>/dev/null; then
    smem -P "$pid"
  fi
}

# Database query analysis
analyze_slow_queries() {
  echo "## Slow Query Analysis"
  
  # MySQL slow query log
  if [ -f "/var/log/mysql/slow.log" ]; then
    tail -100 /var/log/mysql/slow.log
  fi
  
  # WordPress query monitor
  wp eval "global \$wpdb; print_r(\$wpdb->queries);" --path=/home/dave/skippy/rundaverun_local_site/app/public 2>/dev/null | head -50
}
```

### Network Debugging
```bash
# Connection issues
debug_network() {
  local host="$1"
  
  echo "## Network Debug: $host"
  
  # DNS
  echo "### DNS Resolution"
  nslookup "$host" 2>/dev/null || host "$host"
  
  # Connectivity
  echo ""
  echo "### Connectivity"
  ping -c 3 "$host" 2>/dev/null
  
  # Port check
  echo ""
  echo "### Common Ports"
  for port in 80 443 22 3306; do
    timeout 2 bash -c "echo >/dev/tcp/$host/$port" 2>/dev/null && echo "Port $port: OPEN" || echo "Port $port: CLOSED"
  done
  
  # SSL certificate
  echo ""
  echo "### SSL Certificate"
  echo | openssl s_client -connect "$host:443" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null
}
```

### Common Error Patterns

| Error | Likely Cause | Quick Fix |
|-------|--------------|-----------|
| `ModuleNotFoundError` | Missing dependency | `pip install <module>` |
| `ImportError` | Wrong path or missing __init__.py | Check PYTHONPATH, create __init__.py |
| `ConnectionRefused` | Service not running | Start service, check port |
| `Permission denied` | File permissions | `chmod +x` or check ownership |
| `ENOENT` | File not found | Verify path exists |
| `MemoryError` | Insufficient RAM | Increase memory, optimize code |
| `TimeoutError` | Slow response | Check network, increase timeout |
| `JSONDecodeError` | Invalid JSON | Validate JSON structure |
| `SyntaxError` | Code syntax issue | Check for typos, brackets |
| `TypeError` | Wrong argument type | Verify function signature |

## Session Documentation

After debugging, always document:

```bash
cat > "$ERROR_LOG/README.md" << EOF
# Debug Session: $(date +%Y-%m-%d)

## Problem
[Description of the issue]

## Investigation
1. [Step taken]
2. [Step taken]

## Root Cause
[What caused the issue]

## Solution
[How it was fixed]

## Prevention
[How to prevent recurrence]
EOF
```

## Integration

Works with:
- **error-tracking-monitoring** - For systematic error tracking
- **performance-monitoring** - For performance issues
- **session-management** - For documentation
```

---

### 4.2 Merge MCP Skills

**Current:** `mcp-monitoring`, `mcp-server-deployment`, `mcp-server-tools`
**New:** `~/.claude/skills/mcp-operations/SKILL.md`

```markdown
---
name: mcp-operations
description: Comprehensive MCP server management - deployment, monitoring, tools, and troubleshooting. Auto-invoke for any MCP-related tasks.
---

# MCP Operations Skill

**Version:** 2.0.0
**Last Updated:** 2025-12-01
**Merged From:** mcp-monitoring, mcp-server-deployment, mcp-server-tools
**Auto-Invoke:** For MCP server management, tool development, or connectivity issues

## When to Use This Skill

Auto-invoke when:
- MCP server status or health checks needed
- Deploying or updating MCP servers
- Creating new MCP tools
- Troubleshooting MCP connectivity
- Managing MCP configurations

## Quick Reference

### Server Locations
```
/home/dave/skippy/mcp-servers/
├── general-server/           # Main server (52+ tools)
│   ├── server.py             # 9,140 lines
│   ├── requirements.txt
│   └── README.md
└── wordpress-validator/      # WordPress-specific
```

### Status Check
```bash
# Quick MCP health check
mcp_status() {
  echo "## MCP Server Status"
  echo ""
  
  # Check if server process is running
  if pgrep -f "mcp.*server" > /dev/null; then
    echo "✅ MCP server process running"
    pgrep -af "mcp.*server"
  else
    echo "⚠️ No MCP server process found"
  fi
  
  # Check Claude Code connection
  echo ""
  echo "### Claude Code MCP Status"
  claude mcp list 2>/dev/null || echo "Run 'claude mcp list' to check connections"
  
  # Check server files
  echo ""
  echo "### Server Files"
  for server in /home/dave/skippy/mcp-servers/*/server.py; do
    if [ -f "$server" ]; then
      DIR=$(dirname "$server")
      NAME=$(basename "$DIR")
      TOOLS=$(grep -c "@mcp.tool" "$server" 2>/dev/null || echo "0")
      echo "- $NAME: $TOOLS tools"
    fi
  done
}

mcp_status
```

### Tool Inventory
```bash
# List all available MCP tools
list_mcp_tools() {
  SERVER="/home/dave/skippy/mcp-servers/general-server/server.py"
  
  echo "## MCP Tools Inventory"
  echo ""
  
  grep -E "^@mcp\.tool|^async def " "$SERVER" | while read line; do
    if [[ "$line" == "@mcp.tool"* ]]; then
      echo -n "- "
    else
      FUNC=$(echo "$line" | grep -oP "(?<=def )[^(]+")
      echo "$FUNC"
    fi
  done
}
```

### Server Deployment
```bash
# Deploy/update MCP server
deploy_mcp_server() {
  local server_dir="${1:-/home/dave/skippy/mcp-servers/general-server}"
  
  echo "## Deploying MCP Server"
  echo "Directory: $server_dir"
  echo ""
  
  # 1. Validate server
  echo "### Validation"
  if python3 -m py_compile "$server_dir/server.py" 2>/dev/null; then
    echo "✅ Python syntax valid"
  else
    echo "❌ Syntax errors - aborting"
    return 1
  fi
  
  # 2. Install dependencies
  echo ""
  echo "### Dependencies"
  if [ -f "$server_dir/requirements.txt" ]; then
    pip install -r "$server_dir/requirements.txt" --quiet
    echo "✅ Dependencies installed"
  fi
  
  # 3. Test import
  echo ""
  echo "### Import Test"
  cd "$server_dir"
  if python3 -c "import server" 2>/dev/null; then
    echo "✅ Import successful"
  else
    echo "❌ Import failed"
    return 1
  fi
  
  # 4. Restart (if applicable)
  echo ""
  echo "### Restart"
  echo "Restart Claude Code to pick up changes"
  
  return 0
}
```

### Creating New Tools
```bash
# Generate MCP tool template
create_mcp_tool() {
  local name="$1"
  local description="$2"
  
  cat << TOOL

@mcp.tool()
async def $name(
    param1: str,
    param2: int = 10,
    verbose: bool = False
) -> str:
    """
    $description
    
    Args:
        param1: Description of param1
        param2: Description of param2 (default: 10)
        verbose: Enable verbose output
        
    Returns:
        Result description
    """
    try:
        logger.info(f"$name: Processing {param1}")
        
        # Validate input
        if not param1:
            return "Error: param1 is required"
        
        # TODO: Implement logic
        result = f"Processed: {param1}"
        
        if verbose:
            result += f"\\n[DEBUG] param2={param2}"
        
        return result
        
    except Exception as e:
        logger.error(f"$name failed: {e}")
        return f"Error: {str(e)}"

TOOL
}
```

### Troubleshooting
```bash
# Debug MCP connection issues
debug_mcp() {
  echo "## MCP Diagnostics"
  echo ""
  
  # 1. Check Python environment
  echo "### Python Environment"
  echo "Python: $(python3 --version)"
  echo "FastMCP: $(pip show fastmcp 2>/dev/null | grep Version || echo 'Not installed')"
  
  # 2. Check server syntax
  echo ""
  echo "### Server Syntax"
  SERVER="/home/dave/skippy/mcp-servers/general-server/server.py"
  python3 -m py_compile "$SERVER" 2>&1 || echo "Syntax errors found"
  
  # 3. Check imports
  echo ""
  echo "### Import Dependencies"
  cd "$(dirname "$SERVER")"
  python3 -c "
import sys
try:
    from mcp.server.fastmcp import FastMCP
    print('✅ FastMCP')
except ImportError as e:
    print(f'❌ FastMCP: {e}')

try:
    import psutil
    print('✅ psutil')
except ImportError:
    print('❌ psutil')

try:
    import httpx
    print('✅ httpx')
except ImportError:
    print('❌ httpx')
"
  
  # 4. Check for common issues
  echo ""
  echo "### Common Issues Check"
  
  # Duplicate tool names
  DUPS=$(grep "@mcp.tool" "$SERVER" -A1 | grep "async def" | awk '{print $3}' | cut -d'(' -f1 | sort | uniq -d)
  if [ -n "$DUPS" ]; then
    echo "❌ Duplicate tool names: $DUPS"
  else
    echo "✅ No duplicate tools"
  fi
  
  # Missing type hints
  MISSING=$(grep "async def" "$SERVER" | grep -v ":" | head -5)
  if [ -n "$MISSING" ]; then
    echo "⚠️ Functions missing type hints"
  fi
}
```

### Server Configuration
```json
// Claude Code MCP configuration (~/.claude/mcp.json)
{
  "servers": {
    "general": {
      "command": "python3",
      "args": ["/home/dave/skippy/mcp-servers/general-server/server.py"],
      "env": {
        "PYTHONPATH": "/home/dave/skippy/lib/python"
      }
    },
    "wordpress": {
      "command": "python3",
      "args": ["/home/dave/skippy/mcp-servers/wordpress-validator/server.py"]
    }
  }
}
```

## Integration

Works with:
- **api-development** - For API-related tools
- **security-operations** - For secure tool development
- **testing-and-qa** - For tool testing
```

---

### 4.3 Merge Backup Skills

**Current:** `backup-infrastructure`, `gdrive-backup`, `emergency-recovery`
**New:** `~/.claude/skills/backup-recovery/SKILL.md`

Create similar comprehensive merged skill for backup and recovery operations.

---

## Phase 5: Convenience Features

### 5.1 Create Skills Index Generator

**Location:** `~/.claude/scripts/generate_skills_index.sh`

```bash
#!/bin/bash
# generate_skills_index.sh - Generate searchable skills index
# Version: 1.0.0
# Run periodically or after skill changes

SKILLS_DIR="$HOME/.claude/skills"
INDEX_FILE="$SKILLS_DIR/INDEX.md"

{
  echo "# Skills Index"
  echo ""
  echo "**Generated:** $(date)"
  echo "**Total Skills:** $(find "$SKILLS_DIR" -name "SKILL.md" | wc -l)"
  echo ""
  echo "## Quick Reference"
  echo ""
  echo "| Skill | Description | Lines | Auto-Invoke |"
  echo "|-------|-------------|-------|-------------|"
  
  for skill_file in "$SKILLS_DIR"/*/SKILL.md; do
    [ -f "$skill_file" ] || continue
    
    SKILL_DIR=$(dirname "$skill_file")
    SKILL_NAME=$(basename "$SKILL_DIR")
    
    # Extract description from YAML frontmatter
    DESCRIPTION=$(grep -A1 "^description:" "$skill_file" | head -1 | sed 's/description: //' | head -c 50)
    
    # Line count
    LINES=$(wc -l < "$skill_file")
    
    # Check for auto-invoke
    if grep -qi "auto-invoke.*yes" "$skill_file"; then
      AUTO="✅"
    else
      AUTO=""
    fi
    
    echo "| \`$SKILL_NAME\` | $DESCRIPTION... | $LINES | $AUTO |"
  done
  
  echo ""
  echo "## By Category"
  echo ""
  
  # Group by keywords
  echo "### Development"
  ls "$SKILLS_DIR" | grep -E "code|git|test|debug|refactor|script|api" | sed 's/^/- /'
  
  echo ""
  echo "### WordPress"
  ls "$SKILLS_DIR" | grep -E "wordpress|wp|content|plugin" | sed 's/^/- /'
  
  echo ""
  echo "### Security"
  ls "$SKILLS_DIR" | grep -E "security|credential|secret|auth" | sed 's/^/- /'
  
  echo ""
  echo "### Infrastructure"
  ls "$SKILLS_DIR" | grep -E "backup|deploy|monitor|mcp|system" | sed 's/^/- /'
  
  echo ""
  echo "### Campaign"
  ls "$SKILLS_DIR" | grep -E "campaign|voter|volunteer|donor|event" | sed 's/^/- /'
  
} > "$INDEX_FILE"

echo "Index generated: $INDEX_FILE"
```

---

### 5.2 Create Session Template Generator

**Location:** `~/.claude/commands/new-session.md`

```markdown
---
description: Start a new work session with proper directory structure and documentation
argument-hint: "<category> <description> (e.g., 'wordpress homepage-update')"
allowed-tools: ["Bash", "Write"]
---

# New Session Creator

Create properly structured work sessions.

## Instructions

```bash
CATEGORY="${1:-general}"
DESCRIPTION="${2:-work}"

# Sanitize description
SAFE_DESC=$(echo "$DESCRIPTION" | tr ' ' '_' | tr '[:upper:]' '[:lower:]')
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create session directory
SESSION_DIR="/home/dave/skippy/work/$CATEGORY/${TIMESTAMP}_${SAFE_DESC}"
mkdir -p "$SESSION_DIR"/{before,during,after,notes}

# Create session README
cat > "$SESSION_DIR/README.md" << EOF
# Session: $DESCRIPTION

**Started:** $(date)
**Category:** $CATEGORY
**Status:** 🟡 In Progress

## Objective
[Describe what you're trying to accomplish]

## Context
- **Branch:** $(git branch --show-current 2>/dev/null || echo "N/A")
- **Related Issues:** [Link any related issues]

## Files Modified
| File | Change | Status |
|------|--------|--------|
| | | |

## Steps Taken
1. [Step]

## Results
- [ ] Objective completed
- [ ] Tests pass
- [ ] Documentation updated

## Rollback
If needed, rollback with:
\`\`\`bash
# Commands to rollback changes
\`\`\`

## Notes
[Additional notes]

---
**Completed:** [timestamp when done]
**Duration:** [how long it took]
EOF

# Create .gitkeep files
touch "$SESSION_DIR/before/.gitkeep"
touch "$SESSION_DIR/during/.gitkeep"
touch "$SESSION_DIR/after/.gitkeep"
touch "$SESSION_DIR/notes/.gitkeep"

# Log session start
echo "[$(date '+%Y-%m-%d %H:%M:%S')] SESSION_START: $SESSION_DIR" >> ~/.claude/logs/sessions.log

echo "## Session Created"
echo ""
echo "**Directory:** $SESSION_DIR"
echo ""
echo "### Structure"
echo "\`\`\`"
echo "$SESSION_DIR/"
echo "├── before/     # Original state files"
echo "├── during/     # Work in progress"
echo "├── after/      # Final state files"
echo "├── notes/      # Investigation notes"
echo "└── README.md   # Session documentation"
echo "\`\`\`"
echo ""
echo "### Next Steps"
echo "1. Save original state to \`before/\`"
echo "2. Make changes, save iterations to \`during/\`"
echo "3. Save final state to \`after/\`"
echo "4. Update README.md with results"

# Export for use in session
echo ""
echo "### Quick Access"
echo "\`\`\`bash"
echo "export SESSION_DIR=\"$SESSION_DIR\""
echo "cd \"\$SESSION_DIR\""
echo "\`\`\`"
```

## Usage
- `/new-session wordpress homepage-update`
- `/new-session security audit-2024`
- `/new-session development new-feature`
```

---

### 5.3 Create Quick Commands Cheatsheet

**Location:** `~/.claude/commands/cheat.md`

```markdown
---
description: Quick reference for common commands and operations
argument-hint: "[topic: git, wp, test, docker, etc.]"
allowed-tools: ["Read"]
---

# Command Cheatsheet

Quick reference for common operations.

## Git
```bash
# Status & branches
git status -sb
git branch -vv
git log --oneline -10

# Commit
git add -p                    # Interactive staging
git commit -m "type: message"
git commit --amend            # Fix last commit

# Branches
git checkout -b feature/name
git merge --no-ff feature/name
git branch -d feature/name    # Delete merged
git branch -D feature/name    # Force delete

# Stash
git stash push -m "description"
git stash list
git stash pop
```

## WordPress (WP-CLI)
```bash
WP_PATH="/home/dave/skippy/rundaverun_local_site/app/public"

# Content
wp post list --path="$WP_PATH"
wp post get 123 --path="$WP_PATH"
wp post update 123 --post_content="$(cat file.html)" --path="$WP_PATH"

# Database
wp db query "SELECT * FROM wp_posts LIMIT 5" --path="$WP_PATH"
wp db export backup.sql --path="$WP_PATH"

# Cache & maintenance
wp cache flush --path="$WP_PATH"
wp transient delete --all --path="$WP_PATH"
wp rewrite flush --path="$WP_PATH"

# Plugins
wp plugin list --path="$WP_PATH"
wp plugin activate plugin-name --path="$WP_PATH"
```

## Python
```bash
# Virtual environments
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Testing
pytest tests/ -v
pytest --cov=src --cov-report=html
pytest -k "test_name"         # Run specific test
pytest --lf                   # Last failed

# Code quality
black .
isort .
flake8 .
mypy .
```

## Docker
```bash
# Containers
docker ps -a
docker logs container_name
docker exec -it container_name bash
docker stop $(docker ps -q)   # Stop all

# Images
docker images
docker build -t name:tag .
docker rmi image_id

# Cleanup
docker system prune -a
docker volume prune
```

## System
```bash
# Disk
df -h
du -sh *
ncdu .                        # Interactive

# Process
ps aux | grep name
top -o %MEM
htop

# Network
ss -tlnp                      # Listening ports
curl -I https://example.com   # Headers only
```

## Quick Search
```bash
# Find files
find . -name "*.py" -mmin -60    # Modified in last hour
find . -size +10M                # Large files

# Search content
grep -rn "pattern" --include="*.py" .
grep -rE "regex" .
ag "pattern"                     # Silver searcher
rg "pattern"                     # Ripgrep

# Replace
sed -i 's/old/new/g' file
find . -name "*.py" -exec sed -i 's/old/new/g' {} \;
```
```

---

## Phase 6: Infrastructure Cleanup

### 6.1 Cleanup Script

**Location:** `~/.claude/scripts/cleanup_config.sh`

```bash
#!/bin/bash
# cleanup_config.sh - Clean up Claude Code configuration
# Version: 1.0.0

set -euo pipefail

SKILLS_DIR="$HOME/.claude/skills"
DRY_RUN="${1:-false}"

echo "# Claude Code Configuration Cleanup"
echo "Dry run: $DRY_RUN"
echo ""

# 1. Remove empty resource directories
echo "## Empty Resource Directories"
EMPTY_DIRS=$(find "$SKILLS_DIR" -type d -name "resources" -empty)
COUNT=$(echo "$EMPTY_DIRS" | grep -c . || echo "0")
echo "Found: $COUNT empty resource directories"

if [ "$DRY_RUN" = "false" ] && [ -n "$EMPTY_DIRS" ]; then
  echo "$EMPTY_DIRS" | xargs rmdir
  echo "Removed $COUNT empty directories"
else
  echo "$EMPTY_DIRS"
fi

# 2. Find duplicate/similar skills
echo ""
echo "## Potential Duplicate Skills"
ls "$SKILLS_DIR" | while read skill; do
  # Check for skills with similar names
  SIMILAR=$(ls "$SKILLS_DIR" | grep -v "^$skill$" | grep -E "$(echo $skill | cut -d- -f1)")
  if [ -n "$SIMILAR" ]; then
    echo "- $skill may overlap with: $SIMILAR"
  fi
done

# 3. Update last modified dates in skills
echo ""
echo "## Outdated Skills (>30 days)"
find "$SKILLS_DIR" -name "SKILL.md" -mtime +30 | while read skill; do
  echo "- $skill"
done

# 4. Check for deprecated patterns
echo ""
echo "## Deprecated Patterns"
grep -rl "/tmp/" "$SKILLS_DIR" 2>/dev/null | while read file; do
  echo "- $file contains /tmp/ reference"
done

# 5. Validate hook syntax
echo ""
echo "## Hook Validation"
for hook in "$HOME/.claude/hooks"/*.sh; do
  if ! bash -n "$hook" 2>/dev/null; then
    echo "- SYNTAX ERROR: $hook"
  fi
done

echo ""
echo "Cleanup complete."
```

---

### 6.2 Hook Error Handler Template

**Add to all hooks:**

```bash
# Add at the top of every hook script

#!/bin/bash
set -uo pipefail  # Note: removed -e to allow custom error handling

# Error handler - ensure hook never blocks Claude
trap 'echo "{\"decision\": \"allow\"}" 2>/dev/null; exit 0' ERR TERM

# Timeout protection
TIMEOUT_PID=""
start_timeout() {
  local seconds="$1"
  (sleep "$seconds" && kill -TERM $$ 2>/dev/null) &
  TIMEOUT_PID=$!
}

cleanup_timeout() {
  [ -n "$TIMEOUT_PID" ] && kill "$TIMEOUT_PID" 2>/dev/null || true
}

trap cleanup_timeout EXIT

# Start 4-second timeout (leave buffer for hook timeout)
start_timeout 4
```

---

## Implementation Checklist

### Priority 1: High-Impact, Low-Effort (Do First)

- [ ] Create `/debug` command (`~/.claude/commands/debug.md`)
- [ ] Create `/test` command (`~/.claude/commands/test.md`)
- [ ] Create `/health-check` command (`~/.claude/commands/health-check.md`)
- [ ] Add error handlers to all hooks
- [ ] Remove 32 empty `resources/` directories

### Priority 2: Development Productivity

- [ ] Create `/scaffold` command
- [ ] Create `/review-pr` command
- [ ] Create `/explain` command
- [ ] Create `post_edit_lint.sh` hook
- [ ] Create `dev_context_tracker.sh` hook

### Priority 3: Security Hardening

- [ ] Create `secrets-scanner` skill
- [ ] Enhance `pre_tool_use.sh` with new protections
- [ ] Create `security_scan.sh` hook
- [ ] Add rate limiting to API calls

### Priority 4: Skill Consolidation

- [ ] Merge `advanced-debugging` + `diagnostic-debugging` → `debugging`
- [ ] Merge `mcp-*` skills → `mcp-operations`
- [ ] Merge `backup-*` + `emergency-recovery` → `backup-recovery`
- [ ] Generate skills INDEX.md

### Priority 5: Convenience & Cleanup

- [ ] Create `/new-session` command
- [ ] Create `/cheat` command
- [ ] Run cleanup script
- [ ] Update settings.json with new hooks
- [ ] Update main CLAUDE.md with new commands

---

## Verification Steps

After implementation, verify:

```bash
# 1. All hooks are executable and valid
for hook in ~/.claude/hooks/*.sh; do
  bash -n "$hook" && echo "✅ $hook" || echo "❌ $hook"
done

# 2. All commands exist
for cmd in debug test scaffold review-pr explain health-check new-session cheat; do
  [ -f ~/.claude/commands/$cmd.md ] && echo "✅ $cmd" || echo "❌ $cmd"
done

# 3. Skills merged
for skill in debugging mcp-operations backup-recovery; do
  [ -d ~/.claude/skills/$skill ] && echo "✅ $skill" || echo "❌ $skill"
done

# 4. Run health check
~/.claude/commands/health-check.md full
```

---

## Notes for Claude Code

1. **Test hooks after creation** - Run `bash -n script.sh` to verify syntax
2. **Make hooks executable** - Run `chmod +x` on all new hooks
3. **Back up before merging skills** - Keep old skills until new ones are verified
4. **Update settings.json incrementally** - Test each hook addition
5. **Create session directories** - Use `/new-session` for this work
6. **Commit changes in stages** - Don't do everything in one commit

---

**End of Implementation Report**
