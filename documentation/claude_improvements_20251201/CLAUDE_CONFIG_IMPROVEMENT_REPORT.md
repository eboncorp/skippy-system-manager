# Claude Code Configuration Improvement Report

**Generated:** 2025-12-01
**Target System:** Skippy System Manager + Claude Code Config
**Prepared For:** Claude Code Implementation
**Priority:** Execute in order listed

---

## Executive Summary

This report contains actionable improvements for the Claude Code configuration exported from `claude_config_export_20251201.zip`. The improvements are organized into these categories:

1. **Structural Improvements** - Consolidation, cleanup, organization
2. **New Slash Commands** - Development, debugging, testing commands
3. **Hook Enhancements** - Security, automation, error handling
4. **New Skills** - Development-focused skills
5. **Security Hardening** - Additional protection layers
6. **Automation Enhancements** - Workflow automation
7. **MCP Server Improvements** - Modularization and resilience

**Total Estimated Implementation Time:** 4-6 hours

---

## Table of Contents

1. [Structural Improvements](#1-structural-improvements)
2. [New Slash Commands](#2-new-slash-commands)
3. [Hook Enhancements](#3-hook-enhancements)
4. [New Skills](#4-new-skills)
5. [Security Hardening](#5-security-hardening)
6. [Automation Enhancements](#6-automation-enhancements)
7. [MCP Server Improvements](#7-mcp-server-improvements)
8. [Configuration Updates](#8-configuration-updates)
9. [Implementation Checklist](#9-implementation-checklist)

---

## 1. Structural Improvements

### 1.1 Remove Empty Resource Directories

**Problem:** 32 empty `resources/` directories exist in skills.

**Action:** Execute this cleanup:

```bash
#!/bin/bash
# cleanup_empty_resources.sh

SKILLS_DIR="$HOME/.claude/skills"
LOG_FILE="$HOME/.claude/logs/cleanup_$(date +%Y%m%d_%H%M%S).log"

echo "Cleaning empty resource directories..." | tee "$LOG_FILE"

find "$SKILLS_DIR" -type d -name "resources" -empty | while read dir; do
  echo "Removing: $dir" | tee -a "$LOG_FILE"
  rmdir "$dir"
done

echo "Cleanup complete. Removed $(grep -c "Removing" "$LOG_FILE") directories."
```

### 1.2 Consolidate Overlapping Skills

**Problem:** Multiple skills cover similar domains, increasing context usage.

**Action:** Merge these skill groups:

#### Group 1: Debugging Skills → `debugging`

Merge: `advanced-debugging` + `diagnostic-debugging`

Create: `$HOME/.claude/skills/debugging/SKILL.md`

```markdown
---
name: debugging
description: Comprehensive debugging toolkit. Auto-invoke for error investigation, log analysis, stack traces, performance issues, and troubleshooting any system or code problems.
---

# Debugging Skill

**Version:** 2.0.0
**Last Updated:** 2025-12-01
**Auto-Invoke:** Yes - errors, debugging, troubleshooting, stack traces, logs

## When to Use This Skill

Auto-invoke when:
- Investigating errors or exceptions
- Analyzing log files
- Tracing code execution
- Debugging performance issues
- Troubleshooting system problems

## Quick Diagnostics

### Error Analysis
```bash
# Parse Python traceback
parse_traceback() {
  grep -E "File \"|line [0-9]+|Error:|Exception:" | head -20
}

# Parse JavaScript stack
parse_js_stack() {
  grep -oP 'at .+ \([^)]+:\d+:\d+\)' | head -10
}

# Find error in logs
find_errors() {
  grep -rni "error\|exception\|failed\|fatal" "$1" | tail -50
}
```

### Log Analysis
```bash
# Recent errors across all logs
tail_all_logs() {
  find /var/log ~/.claude/logs -name "*.log" -mmin -60 2>/dev/null | \
    xargs -I {} sh -c 'echo "=== {} ===" && tail -20 {}'
}

# Error frequency analysis
error_frequency() {
  grep -h "error\|Error\|ERROR" "$@" | \
    sed 's/[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}//g' | \
    sort | uniq -c | sort -rn | head -20
}

# Timeline of errors
error_timeline() {
  grep -h "error\|Error" "$@" | \
    grep -oP '\d{4}-\d{2}-\d{2} \d{2}:\d{2}' | \
    uniq -c
}
```

### Performance Debugging
```bash
# Python profiling
profile_python() {
  python3 -m cProfile -s cumtime "$1" 2>&1 | head -30
}

# Memory usage
memory_profile() {
  python3 -c "
import tracemalloc
tracemalloc.start()
exec(open('$1').read())
snapshot = tracemalloc.take_snapshot()
for stat in snapshot.statistics('lineno')[:10]:
    print(stat)
"
}

# Slow query detection (if DB available)
slow_queries() {
  grep -E "Query took [0-9]+\.[0-9]+ seconds" "$@" | \
    awk '{print $NF, $0}' | sort -rn | head -10
}
```

### System Debugging
```bash
# Process investigation
investigate_process() {
  PID="$1"
  echo "=== Process Info ==="
  ps -p "$PID" -o pid,ppid,user,%cpu,%mem,stat,start,time,command
  echo "=== Open Files ==="
  lsof -p "$PID" 2>/dev/null | head -20
  echo "=== Network Connections ==="
  lsof -i -p "$PID" 2>/dev/null
}

# Disk space issues
disk_investigation() {
  echo "=== Disk Usage ==="
  df -h
  echo "=== Large Files ==="
  find / -xdev -type f -size +100M 2>/dev/null | head -20
  echo "=== Recent Large Files ==="
  find / -xdev -type f -size +50M -mtime -1 2>/dev/null
}

# Network debugging
network_debug() {
  echo "=== Listening Ports ==="
  ss -tlnp
  echo "=== Established Connections ==="
  ss -tnp state established
  echo "=== DNS Resolution ==="
  cat /etc/resolv.conf
}
```

## Common Error Patterns

| Error Pattern | Likely Cause | Quick Fix |
|---------------|--------------|-----------|
| `ModuleNotFoundError` | Missing Python package | `pip install {module}` |
| `ENOENT` | File/path not found | Verify path exists |
| `Permission denied` | Insufficient permissions | `chmod`/`chown` |
| `Connection refused` | Service not running | Check service status |
| `ECONNRESET` | Connection dropped | Retry with backoff |
| `OOM killed` | Out of memory | Increase memory/optimize |
| `Segmentation fault` | Memory corruption | Check for buffer overflows |
| `Timeout` | Slow response/deadlock | Increase timeout/check locks |

## Debug Session Workflow

1. **Capture State**
```bash
SESSION_DIR="$HOME/skippy/work/debug/$(date +%Y%m%d_%H%M%S)_investigation"
mkdir -p "$SESSION_DIR"

# Capture system state
{
  echo "=== System Info ==="
  uname -a
  echo "=== Memory ==="
  free -h
  echo "=== Disk ==="
  df -h
  echo "=== Processes ==="
  ps aux --sort=-%mem | head -20
} > "$SESSION_DIR/system_state.txt"
```

2. **Reproduce Issue**
```bash
# Run with verbose logging
DEBUG=1 VERBOSE=1 command 2>&1 | tee "$SESSION_DIR/debug_output.log"
```

3. **Analyze**
```bash
# Search for patterns
grep -E "error|warn|fail" "$SESSION_DIR/debug_output.log" > "$SESSION_DIR/errors.txt"
```

4. **Document**
```bash
cat > "$SESSION_DIR/README.md" << EOF
# Debug Session: $(date)

## Issue
{description}

## Steps to Reproduce
1. {step}

## Root Cause
{cause}

## Solution
{solution}

## Prevention
{how to prevent}
EOF
```

## Integration

Works with:
- **error-tracking-monitoring** - Error aggregation
- **session-management** - Session preservation
- **git-workflow** - Bisect for regressions
```

After creating, remove old skills:
```bash
rm -rf "$HOME/.claude/skills/advanced-debugging"
rm -rf "$HOME/.claude/skills/diagnostic-debugging"
```

#### Group 2: MCP Skills → `mcp-operations`

Merge: `mcp-monitoring` + `mcp-server-deployment` + `mcp-server-tools`

Create: `$HOME/.claude/skills/mcp-operations/SKILL.md`

```markdown
---
name: mcp-operations
description: Complete MCP server management - deployment, monitoring, tools, and troubleshooting. Auto-invoke for any MCP-related operations.
---

# MCP Operations Skill

**Version:** 2.0.0
**Last Updated:** 2025-12-01
**Auto-Invoke:** Yes - MCP, server, tools, deployment

## Quick Reference

### Server Status
```bash
# Check all MCP servers
claude mcp list

# Server health check
curl -s http://localhost:3000/health 2>/dev/null || echo "Server not responding"

# Process check
pgrep -f "mcp.*server" && echo "MCP process running" || echo "No MCP process"
```

### Common Operations
```bash
# Restart server
pkill -f "mcp.*server"
sleep 2
cd ~/skippy/mcp-servers/general-server && python server.py &

# View logs
tail -f ~/.claude/logs/mcp_*.log

# Test tool
echo '{"tool": "test", "args": {}}' | nc localhost 3000
```

### Deployment Checklist
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Environment variables set
- [ ] Port available
- [ ] Permissions correct
- [ ] Health endpoint responding

### Troubleshooting

| Symptom | Check | Fix |
|---------|-------|-----|
| Connection refused | Port in use | `lsof -i :3000` then kill |
| Timeout | Server overloaded | Restart, check resources |
| Tool not found | Registration | Check tool definitions |
| Auth failure | Credentials | Verify tokens/keys |

## Tool Categories (52+ tools)

- **Google Drive (13):** File management, uploads, sharing
- **Pexels (4):** Stock photo search/download
- **System (8):** CPU, disk, memory, processes
- **Remote/SSH (5):** Ebon server management
- **WordPress (10):** WP-CLI, backups, database
- **File Operations (6):** Advanced file management
- **Web (4):** HTTP GET/POST
- **Git (2):** Status, diff
```

After creating, remove old skills:
```bash
rm -rf "$HOME/.claude/skills/mcp-monitoring"
rm -rf "$HOME/.claude/skills/mcp-server-deployment"
rm -rf "$HOME/.claude/skills/mcp-server-tools"
```

#### Group 3: Backup Skills → `backup-recovery`

Merge: `backup-infrastructure` + `gdrive-backup` + `emergency-recovery`

Create: `$HOME/.claude/skills/backup-recovery/SKILL.md`

```markdown
---
name: backup-recovery
description: Unified backup and recovery operations - local backups, cloud sync, disaster recovery, and rollback procedures. Auto-invoke for backup, restore, or recovery tasks.
---

# Backup & Recovery Skill

**Version:** 2.0.0
**Last Updated:** 2025-12-01
**Auto-Invoke:** Yes - backup, restore, recovery, rollback, disaster

## Backup Systems Overview

| System | Schedule | Location | Retention |
|--------|----------|----------|-----------|
| WordPress DB | Daily 2 AM | ~/skippy/backups/wordpress/ | 30 days |
| Config Files | Daily 3 AM | ~/skippy/backups/config/ | 90 days |
| Google Drive | Daily 4 AM | Cloud | Unlimited |
| Session State | On compact | ~/.claude/compactions/ | 7 days |
| Git Repos | On commit | Remote + local | Unlimited |

## Quick Backup Commands

```bash
# WordPress full backup
wp db export --path=/path/to/wordpress backup_$(date +%Y%m%d).sql
tar -czf wp_files_$(date +%Y%m%d).tar.gz /path/to/wordpress/wp-content

# Config backup
tar -czf config_$(date +%Y%m%d).tar.gz ~/.claude ~/.ssh/config

# Google Drive sync
rclone sync ~/skippy/important gdrive:skippy-backup --progress

# Session state backup
cp -r ~/.claude/compactions ~/.claude/backups/compactions_$(date +%Y%m%d)
```

## Recovery Procedures

### WordPress Recovery
```bash
# 1. Find latest backup
ls -lt ~/skippy/backups/wordpress/*.sql | head -5

# 2. Restore database
wp db import backup_YYYYMMDD.sql --path=/path/to/wordpress

# 3. Restore files if needed
tar -xzf wp_files_YYYYMMDD.tar.gz -C /

# 4. Verify
wp core verify-checksums --path=/path/to/wordpress
```

### Session Recovery
```bash
# 1. Find recent compaction
ls -lt ~/.claude/compactions/ | head -5

# 2. Read resume instructions
cat ~/.claude/compactions/LATEST/RESUME_INSTRUCTIONS.md

# 3. Restore context
cat ~/.claude/compactions/LATEST/session_summary.md
```

### Emergency Rollback
```bash
# Git rollback (safe)
git log --oneline -10
git revert HEAD

# Git rollback (destructive - requires explicit permission)
# git reset --hard HEAD~1  # DO NOT RUN WITHOUT USER APPROVAL

# File rollback from backup
cp ~/skippy/backups/file.bak file
```

## Verification Commands

```bash
# Verify backup integrity
gzip -t backup.tar.gz && echo "OK" || echo "CORRUPTED"

# Verify WordPress backup
mysql -e "SELECT COUNT(*) FROM wp_posts;" database_name

# Verify file counts
find /path/to/backup -type f | wc -l
```
```

### 1.3 Create Skills Index

**Action:** Generate auto-updated skills index:

Create: `$HOME/.claude/skills/INDEX.md`

```bash
#!/bin/bash
# generate_skills_index.sh

SKILLS_DIR="$HOME/.claude/skills"
INDEX_FILE="$SKILLS_DIR/INDEX.md"

cat > "$INDEX_FILE" << 'HEADER'
# Skills Index

**Auto-Generated:** $(date)
**Total Skills:** $(ls -d "$SKILLS_DIR"/*/ 2>/dev/null | wc -l)

## Quick Reference

| Skill | Description | Auto-Invoke Keywords |
|-------|-------------|---------------------|
HEADER

for skill_dir in "$SKILLS_DIR"/*/; do
  [ -d "$skill_dir" ] || continue
  skill_name=$(basename "$skill_dir")
  skill_file="$skill_dir/SKILL.md"
  
  if [ -f "$skill_file" ]; then
    # Extract description from YAML frontmatter
    desc=$(grep -A1 "^description:" "$skill_file" | tail -1 | sed 's/^[- ]*//' | cut -c1-60)
    # Extract auto-invoke keywords
    keywords=$(grep -i "auto-invoke\|when.*mention" "$skill_file" | head -1 | cut -c1-40)
    
    echo "| $skill_name | $desc... | $keywords |" >> "$INDEX_FILE"
  fi
done

echo "" >> "$INDEX_FILE"
echo "## Skills by Category" >> "$INDEX_FILE"
echo "" >> "$INDEX_FILE"

# Group by category
for category in "campaign" "wordpress" "security" "development" "infrastructure" "operations"; do
  echo "### ${category^}" >> "$INDEX_FILE"
  ls "$SKILLS_DIR" | grep -i "$category" | while read skill; do
    echo "- $skill" >> "$INDEX_FILE"
  done
  echo "" >> "$INDEX_FILE"
done

echo "Index generated: $INDEX_FILE"
```

---

## 2. New Slash Commands

### 2.1 `/debug` - Quick Debug Helper

Create: `$HOME/.claude/commands/debug.md`

```markdown
---
description: Quick debug helper - analyze errors, suggest fixes, trace issues
argument-hint: "[error message, file:line, or 'logs' to scan recent logs]"
allowed-tools: ["Bash", "Read", "Grep", "Write"]
---

# Debug Assistant

Quickly analyze errors, trace issues, and suggest fixes.

## Instructions

### 1. Determine Debug Mode

```bash
ARG="$1"

if [ -z "$ARG" ]; then
  MODE="interactive"
elif [ "$ARG" = "logs" ]; then
  MODE="logs"
elif echo "$ARG" | grep -q ":"; then
  MODE="file_line"
else
  MODE="error_search"
fi
```

### 2. Log Scanning Mode
```bash
if [ "$MODE" = "logs" ]; then
  echo "## Recent Errors (last hour)"
  
  # Claude logs
  echo "### Claude Logs"
  find ~/.claude/logs -name "*.log" -mmin -60 -exec grep -l -i "error\|exception\|failed" {} \; | \
    while read log; do
      echo "#### $log"
      grep -i "error\|exception\|failed" "$log" | tail -10
    done
  
  # System logs
  echo "### System Logs"
  journalctl --since "1 hour ago" -p err --no-pager 2>/dev/null | tail -20
  
  # Application logs
  echo "### Application Logs"
  for log in /var/log/apache2/error.log /var/log/nginx/error.log /var/log/php*.log; do
    [ -f "$log" ] && echo "#### $log" && tail -10 "$log"
  done
fi
```

### 3. File:Line Mode
```bash
if [ "$MODE" = "file_line" ]; then
  FILE=$(echo "$ARG" | cut -d: -f1)
  LINE=$(echo "$ARG" | cut -d: -f2)
  
  echo "## Context for $FILE:$LINE"
  
  # Show context around the line
  START=$((LINE - 10))
  [ $START -lt 1 ] && START=1
  END=$((LINE + 10))
  
  echo "### Code Context"
  sed -n "${START},${END}p" "$FILE" | nl -ba -v $START
  
  # Find related tests
  echo "### Related Tests"
  BASENAME=$(basename "$FILE" | sed 's/\.[^.]*$//')
  find . -name "*${BASENAME}*test*" -o -name "test_*${BASENAME}*" 2>/dev/null | head -5
  
  # Find recent changes to this file
  echo "### Recent Changes"
  git log --oneline -5 -- "$FILE" 2>/dev/null || echo "Not in git"
fi
```

### 4. Error Search Mode
```bash
if [ "$MODE" = "error_search" ]; then
  ERROR="$ARG"
  
  echo "## Searching for: $ERROR"
  
  # Search codebase
  echo "### In Codebase"
  grep -rn "$ERROR" --include="*.py" --include="*.js" --include="*.php" --include="*.sh" . 2>/dev/null | head -20
  
  # Search logs
  echo "### In Logs"
  grep -rh "$ERROR" ~/.claude/logs/*.log 2>/dev/null | tail -10
  
  # Common fixes database
  echo "### Suggested Fixes"
  case "$ERROR" in
    *"ModuleNotFoundError"*|*"No module named"*)
      MODULE=$(echo "$ERROR" | grep -oP "No module named '\K[^']+")
      echo "pip install $MODULE"
      ;;
    *"Permission denied"*)
      echo "Check file permissions: ls -la <file>"
      echo "Fix: chmod +x <file> or sudo chown \$USER <file>"
      ;;
    *"Connection refused"*)
      echo "Service not running. Check: systemctl status <service>"
      ;;
    *"ENOENT"*|*"No such file"*)
      echo "File/path doesn't exist. Verify path is correct."
      ;;
    *"Timeout"*)
      echo "Consider: increase timeout, check network, check service health"
      ;;
    *)
      echo "Search online: https://www.google.com/search?q=$(echo "$ERROR" | head -c 100 | sed 's/ /+/g')"
      ;;
  esac
fi
```

### 5. Interactive Mode
```bash
if [ "$MODE" = "interactive" ]; then
  echo "## Debug Helper"
  echo ""
  echo "Usage:"
  echo "  /debug <error message>  - Search for error and suggest fixes"
  echo "  /debug <file:line>      - Show context around specific line"
  echo "  /debug logs             - Scan recent logs for errors"
  echo ""
  echo "## Quick Diagnostics"
  echo ""
  echo "### System Health"
  echo "- CPU: $(top -bn1 | grep 'Cpu(s)' | awk '{print $2}')% used"
  echo "- Memory: $(free -h | awk '/Mem:/ {print $3 "/" $2}')"
  echo "- Disk: $(df -h / | awk 'NR==2 {print $5}') used"
  echo ""
  echo "### Recent Errors"
  find ~/.claude/logs -name "*.log" -mmin -30 -exec grep -l "error\|Error" {} \; 2>/dev/null | wc -l
  echo " log files with errors in last 30 minutes"
fi
```

### 6. Create Debug Session Record
```bash
DEBUG_DIR="$HOME/.claude/debug_sessions"
mkdir -p "$DEBUG_DIR"

cat > "$DEBUG_DIR/$(date +%Y%m%d_%H%M%S).json" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "mode": "$MODE",
  "query": "$ARG",
  "working_dir": "$(pwd)",
  "git_branch": "$(git branch --show-current 2>/dev/null || echo 'N/A')"
}
EOF
```
```

### 2.2 `/test` - Smart Test Runner

Create: `$HOME/.claude/commands/test.md`

```markdown
---
description: Smart test runner - auto-detects framework, runs relevant tests
argument-hint: "[file, function, 'all', 'changed', or 'failed']"
allowed-tools: ["Bash", "Read"]
---

# Smart Test Runner

Auto-detect test framework and run tests intelligently.

## Instructions

### 1. Detect Test Framework
```bash
detect_framework() {
  if [ -f "pytest.ini" ] || [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
    if grep -q "pytest" pyproject.toml setup.py 2>/dev/null; then
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
  
  if [ -f "Cargo.toml" ]; then
    echo "cargo"
    return
  fi
  
  echo "unknown"
}

FRAMEWORK=$(detect_framework)
TARGET="${1:-all}"
```

### 2. Run Tests Based on Framework
```bash
run_tests() {
  case "$FRAMEWORK" in
    pytest)
      case "$TARGET" in
        all)
          pytest tests/ -v --tb=short -x
          ;;
        changed)
          # Tests for files changed vs main
          CHANGED=$(git diff --name-only main 2>/dev/null | grep "\.py$" | grep -v test)
          if [ -n "$CHANGED" ]; then
            for f in $CHANGED; do
              TEST_FILE=$(echo "$f" | sed 's|src/|tests/test_|' | sed 's|\.py$|_test.py|')
              [ -f "$TEST_FILE" ] && pytest "$TEST_FILE" -v
            done
          else
            echo "No Python files changed vs main"
          fi
          ;;
        failed)
          pytest --lf -v --tb=short
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
        *)
          npx jest "$TARGET" --coverage
          ;;
      esac
      ;;
      
    phpunit)
      case "$TARGET" in
        all)
          ./vendor/bin/phpunit
          ;;
        *)
          ./vendor/bin/phpunit --filter "$TARGET"
          ;;
      esac
      ;;
      
    cargo)
      case "$TARGET" in
        all)
          cargo test
          ;;
        *)
          cargo test "$TARGET"
          ;;
      esac
      ;;
      
    *)
      echo "Unknown test framework. Searching for test files..."
      find . -name "*test*.py" -o -name "*.test.js" -o -name "*Test.php" | head -10
      ;;
  esac
}

run_tests
```

### 3. Coverage Report
```bash
echo ""
echo "## Coverage Summary"

case "$FRAMEWORK" in
  pytest)
    pytest --cov=src --cov-report=term-missing --cov-fail-under=0 -q 2>/dev/null | tail -20
    ;;
  jest)
    npx jest --coverage --coverageReporters=text-summary 2>/dev/null | tail -10
    ;;
esac
```

### 4. Test Health Summary
```bash
echo ""
echo "## Test Health"

# Count test files
TEST_COUNT=$(find . -name "*test*.py" -o -name "*.test.js" -o -name "*Test.php" 2>/dev/null | wc -l)
echo "- Test files found: $TEST_COUNT"

# Check for missing tests
echo "- Source files without tests:"
find . -name "*.py" -path "*/src/*" ! -name "__init__.py" ! -name "*test*" | while read src; do
  TEST=$(echo "$src" | sed 's|src/|tests/test_|' | sed 's|\.py$|_test.py|')
  [ ! -f "$TEST" ] && echo "  - $src"
done | head -5
```
```

### 2.3 `/scaffold` - Code Generator

Create: `$HOME/.claude/commands/scaffold.md`

```markdown
---
description: Generate boilerplate code - classes, tests, scripts, components
argument-hint: "<type> <name> (e.g., 'class UserService', 'test payment', 'script backup')"
allowed-tools: ["Bash", "Write", "Read"]
---

# Code Scaffolding

Generate boilerplate for common code patterns.

## Instructions

### 1. Parse Arguments
```bash
TYPE="$1"
NAME="$2"

if [ -z "$TYPE" ] || [ -z "$NAME" ]; then
  echo "Usage: /scaffold <type> <name>"
  echo ""
  echo "Types:"
  echo "  class <ClassName>     - Python class with tests"
  echo "  test <module_name>    - Test file for existing module"
  echo "  script <name>         - Bash script with template"
  echo "  api <endpoint>        - REST API endpoint"
  echo "  component <Name>      - React component"
  echo "  hook <name>           - Claude Code hook"
  echo "  skill <name>          - Claude Code skill"
  echo "  command <name>        - Slash command"
  exit 0
fi
```

### 2. Generate Based on Type

#### Python Class
```bash
if [ "$TYPE" = "class" ]; then
  FILENAME=$(echo "$NAME" | sed 's/\([A-Z]\)/_\L\1/g' | sed 's/^_//')
  
  # Main class file
  cat > "src/${FILENAME}.py" << EOF
"""
${NAME} - Brief description

Created: $(date +%Y-%m-%d)
Author: Claude Code
"""

from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ${NAME}:
    """
    Brief description of ${NAME}.
    
    Attributes:
        attr1: Description of attr1
        attr2: Description of attr2
    
    Example:
        >>> obj = ${NAME}()
        >>> obj.method()
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize ${NAME}.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._initialized = False
        logger.debug(f"Initialized ${NAME}")
    
    def __repr__(self) -> str:
        return f"${NAME}(initialized={self._initialized})"
    
    def __enter__(self):
        """Context manager entry."""
        self._initialized = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
        return False
    
    def process(self, data: Any) -> Any:
        """Process data.
        
        Args:
            data: Input data to process
            
        Returns:
            Processed data
            
        Raises:
            ValueError: If data is invalid
        """
        if not data:
            raise ValueError("Data cannot be empty")
        
        logger.info(f"Processing data: {type(data)}")
        # TODO: Implement processing logic
        return data
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False
        logger.debug(f"Cleaned up ${NAME}")
EOF

  # Test file
  cat > "tests/test_${FILENAME}.py" << EOF
"""Tests for ${FILENAME} module."""

import pytest
from src.${FILENAME} import ${NAME}


class Test${NAME}:
    """Test suite for ${NAME}."""
    
    @pytest.fixture
    def instance(self):
        """Create test instance."""
        return ${NAME}()
    
    @pytest.fixture
    def configured_instance(self):
        """Create configured test instance."""
        return ${NAME}(config={"debug": True})
    
    def test_init_default(self, instance):
        """Test default initialization."""
        assert instance is not None
        assert instance.config == {}
        assert not instance._initialized
    
    def test_init_with_config(self, configured_instance):
        """Test initialization with config."""
        assert configured_instance.config == {"debug": True}
    
    def test_repr(self, instance):
        """Test string representation."""
        assert "${NAME}" in repr(instance)
        assert "initialized=False" in repr(instance)
    
    def test_context_manager(self):
        """Test context manager protocol."""
        with ${NAME}() as obj:
            assert obj._initialized
        assert not obj._initialized
    
    def test_process_valid_data(self, instance):
        """Test processing valid data."""
        result = instance.process({"key": "value"})
        assert result == {"key": "value"}
    
    def test_process_empty_data_raises(self, instance):
        """Test that empty data raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            instance.process(None)
    
    def test_cleanup(self, instance):
        """Test cleanup method."""
        instance._initialized = True
        instance.cleanup()
        assert not instance._initialized
EOF

  echo "Created:"
  echo "  - src/${FILENAME}.py"
  echo "  - tests/test_${FILENAME}.py"
fi
```

#### Bash Script
```bash
if [ "$TYPE" = "script" ]; then
  FILENAME="${NAME}_v1.0.0.sh"
  
  cat > "$FILENAME" << 'EOF'
#!/bin/bash
# ${NAME}_v1.0.0.sh - Brief description
#
# Usage:
#   ${NAME}.sh [options] <arguments>
#
# Options:
#   -h, --help     Show this help message
#   -v, --verbose  Enable verbose output
#   -d, --dry-run  Show what would be done
#
# Examples:
#   ${NAME}.sh input.txt
#   ${NAME}.sh -v --dry-run input.txt
#
# Dependencies:
#   - bash 4.0+
#   - jq (optional)
#
# Created: $(date +%Y-%m-%d)
# Author: Claude Code

set -euo pipefail

# ==============================================================================
# Configuration
# ==============================================================================

readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly VERSION="1.0.0"

# Defaults
VERBOSE=false
DRY_RUN=false
LOG_FILE="${SCRIPT_DIR}/${SCRIPT_NAME%.sh}.log"

# ==============================================================================
# Logging Functions
# ==============================================================================

log() {
  local level="$1"
  shift
  local message="$*"
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  
  echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

info()  { log "INFO" "$@"; }
warn()  { log "WARN" "$@" >&2; }
error() { log "ERROR" "$@" >&2; }
debug() { $VERBOSE && log "DEBUG" "$@" || true; }

die() {
  error "$@"
  exit 1
}

# ==============================================================================
# Helper Functions
# ==============================================================================

usage() {
  grep '^#' "$0" | grep -v '#!/' | cut -c3-
  exit 0
}

version() {
  echo "$SCRIPT_NAME version $VERSION"
  exit 0
}

cleanup() {
  # Cleanup code here
  debug "Cleanup complete"
}

trap cleanup EXIT

# ==============================================================================
# Main Functions
# ==============================================================================

validate_inputs() {
  # Add validation logic
  debug "Validating inputs..."
}

process() {
  local input="$1"
  
  info "Processing: $input"
  
  if $DRY_RUN; then
    info "[DRY RUN] Would process: $input"
    return 0
  fi
  
  # TODO: Add main processing logic here
  
  info "Processing complete"
}

# ==============================================================================
# Argument Parsing
# ==============================================================================

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help)
        usage
        ;;
      -v|--verbose)
        VERBOSE=true
        shift
        ;;
      -d|--dry-run)
        DRY_RUN=true
        shift
        ;;
      --version)
        version
        ;;
      -*)
        die "Unknown option: $1"
        ;;
      *)
        ARGS+=("$1")
        shift
        ;;
    esac
  done
}

# ==============================================================================
# Main
# ==============================================================================

main() {
  parse_args "$@"
  
  info "Starting $SCRIPT_NAME v$VERSION"
  debug "Arguments: ${ARGS[*]:-none}"
  
  validate_inputs
  
  for arg in "${ARGS[@]:-}"; do
    process "$arg"
  done
  
  info "Complete"
}

# Run if not sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
EOF

  chmod +x "$FILENAME"
  echo "Created: $FILENAME"
fi
```

#### Claude Code Skill
```bash
if [ "$TYPE" = "skill" ]; then
  SKILL_DIR="$HOME/.claude/skills/${NAME}"
  mkdir -p "$SKILL_DIR"
  
  cat > "$SKILL_DIR/SKILL.md" << EOF
---
name: ${NAME}
description: Brief description of what this skill does. Auto-invoke when: keyword1, keyword2, keyword3
---

# ${NAME^} Skill

**Version:** 1.0.0
**Last Updated:** $(date +%Y-%m-%d)
**Auto-Invoke:** Yes - when {keywords} mentioned

## When to Use This Skill

Auto-invoke when:
- Condition 1
- Condition 2
- Condition 3

## Quick Reference

\`\`\`bash
# Common command 1
command_here

# Common command 2
another_command
\`\`\`

## Workflows

### Workflow 1: Name
1. Step 1
2. Step 2
3. Step 3

### Workflow 2: Name
1. Step 1
2. Step 2

## Common Patterns

| Pattern | Description | Example |
|---------|-------------|---------|
| Pattern 1 | Description | \`example\` |
| Pattern 2 | Description | \`example\` |

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Issue 1 | Cause | Solution |
| Issue 2 | Cause | Solution |

## Integration

Works with:
- **skill-1** - How they integrate
- **skill-2** - How they integrate
EOF

  echo "Created: $SKILL_DIR/SKILL.md"
fi
```

#### Slash Command
```bash
if [ "$TYPE" = "command" ]; then
  cat > "$HOME/.claude/commands/${NAME}.md" << EOF
---
description: Brief description of what this command does
argument-hint: "[optional: argument description]"
allowed-tools: ["Bash", "Read", "Write", "Grep"]
---

# ${NAME^} Command

Brief description of purpose.

## Instructions

### 1. Parse Arguments
\`\`\`bash
ARG="\$1"

if [ -z "\$ARG" ]; then
  echo "Usage: /${NAME} <argument>"
  exit 0
fi
\`\`\`

### 2. Main Logic
\`\`\`bash
echo "Processing: \$ARG"

# TODO: Implement main logic

echo "Complete"
\`\`\`

### 3. Output
\`\`\`bash
# Format output nicely
echo "## Results"
echo ""
echo "- Result 1"
echo "- Result 2"
\`\`\`

## Examples

- \`/${NAME} example1\` - Does something
- \`/${NAME} example2\` - Does something else
EOF

  echo "Created: $HOME/.claude/commands/${NAME}.md"
fi
```
```

### 2.4 `/review` - Code Review Assistant

Create: `$HOME/.claude/commands/review.md`

```markdown
---
description: Comprehensive code review - diff analysis, security scan, quality metrics
argument-hint: "[file, PR number, branch, or 'staged' for staged changes]"
allowed-tools: ["Bash", "Read", "Grep"]
---

# Code Review Assistant

Perform comprehensive code review with automated checks.

## Instructions

### 1. Determine Review Scope
```bash
TARGET="${1:-staged}"

case "$TARGET" in
  staged)
    FILES=$(git diff --cached --name-only)
    DIFF_CMD="git diff --cached"
    ;;
  HEAD~*)
    FILES=$(git diff --name-only "$TARGET")
    DIFF_CMD="git diff $TARGET"
    ;;
  */*)
    # Branch comparison
    FILES=$(git diff --name-only main..."$TARGET")
    DIFF_CMD="git diff main...$TARGET"
    ;;
  *)
    # Single file
    FILES="$TARGET"
    DIFF_CMD="git diff HEAD -- $TARGET"
    ;;
esac

echo "# Code Review: $TARGET"
echo "Files to review: $(echo "$FILES" | wc -w)"
echo ""
```

### 2. Summary Statistics
```bash
echo "## Change Summary"
echo ""
$DIFF_CMD --stat
echo ""
```

### 3. Security Scan
```bash
echo "## Security Check"
echo ""

SECURITY_ISSUES=0

# Check for secrets
echo "### Secrets Scan"
if $DIFF_CMD | grep -E "(password|secret|api_key|token|private_key)\s*[=:]" | grep "^+"; then
  echo "⚠️  POTENTIAL SECRETS DETECTED"
  SECURITY_ISSUES=$((SECURITY_ISSUES + 1))
else
  echo "✅ No obvious secrets"
fi

# Check for SQL injection
echo "### SQL Injection"
if $DIFF_CMD | grep -E "execute\s*\(.*%|execute\s*\(.*\+|query\s*\(.*\\\$" | grep "^+"; then
  echo "⚠️  POTENTIAL SQL INJECTION"
  SECURITY_ISSUES=$((SECURITY_ISSUES + 1))
else
  echo "✅ No obvious SQL injection"
fi

# Check for eval
echo "### Dangerous Functions"
if $DIFF_CMD | grep -E "\beval\s*\(|\bexec\s*\(" | grep "^+"; then
  echo "⚠️  DANGEROUS FUNCTION USAGE"
  SECURITY_ISSUES=$((SECURITY_ISSUES + 1))
else
  echo "✅ No dangerous functions"
fi

echo ""
echo "Security issues found: $SECURITY_ISSUES"
echo ""
```

### 4. Code Quality Analysis
```bash
echo "## Code Quality"
echo ""

for file in $FILES; do
  [ -f "$file" ] || continue
  
  echo "### $file"
  
  LINES=$(wc -l < "$file")
  echo "- Lines: $LINES"
  
  case "$file" in
    *.py)
      # Python analysis
      FUNCTIONS=$(grep -c "^def \|^    def " "$file" 2>/dev/null || echo 0)
      CLASSES=$(grep -c "^class " "$file" 2>/dev/null || echo 0)
      TODOS=$(grep -c "TODO\|FIXME\|HACK" "$file" 2>/dev/null || echo 0)
      
      echo "- Functions: $FUNCTIONS"
      echo "- Classes: $CLASSES"
      echo "- TODOs: $TODOS"
      
      # Complexity (if radon available)
      if command -v radon &>/dev/null; then
        COMPLEXITY=$(radon cc "$file" -a 2>/dev/null | tail -1 || echo "N/A")
        echo "- Complexity: $COMPLEXITY"
      fi
      
      # Type hints coverage
      TYPED=$(grep -c ": \|-> " "$file" 2>/dev/null || echo 0)
      echo "- Type annotations: $TYPED"
      ;;
      
    *.js|*.ts)
      # JavaScript analysis
      FUNCTIONS=$(grep -cE "function |=> |async " "$file" 2>/dev/null || echo 0)
      CONSOLE=$(grep -c "console\." "$file" 2>/dev/null || echo 0)
      
      echo "- Functions: $FUNCTIONS"
      echo "- Console statements: $CONSOLE"
      [ "$CONSOLE" -gt 0 ] && echo "  ⚠️  Remove console statements before production"
      ;;
      
    *.php)
      # PHP analysis
      FUNCTIONS=$(grep -c "function " "$file" 2>/dev/null || echo 0)
      echo "- Functions: $FUNCTIONS"
      
      # WordPress checks
      if grep -q "wp_" "$file"; then
        SANITIZED=$(grep -c "sanitize_\|esc_" "$file" 2>/dev/null || echo 0)
        echo "- Sanitization calls: $SANITIZED"
      fi
      ;;
  esac
  
  echo ""
done
```

### 5. Test Coverage Check
```bash
echo "## Test Coverage"
echo ""

for file in $FILES; do
  case "$file" in
    *.py)
      if [[ "$file" != *test* ]]; then
        BASENAME=$(basename "$file" .py)
        TEST_FILE=$(find . -name "test_${BASENAME}.py" -o -name "${BASENAME}_test.py" 2>/dev/null | head -1)
        
        if [ -n "$TEST_FILE" ]; then
          echo "✅ $file → $TEST_FILE"
        else
          echo "❌ $file → NO TESTS FOUND"
        fi
      fi
      ;;
  esac
done
echo ""
```

### 6. Complexity Hotspots
```bash
echo "## Complexity Hotspots"
echo ""

for file in $FILES; do
  [ -f "$file" ] || continue
  
  case "$file" in
    *.py|*.js|*.php)
      # Find long functions
      echo "### Long functions in $file (>30 lines)"
      awk '/^(def |function |async function )/{name=$2; start=NR} 
           /^(def |function |class |async function )/ && NR>start{
             if(NR-start>30) print "  ⚠️  " name ": " NR-start " lines"
           }' "$file" 2>/dev/null
      
      # Find deeply nested code
      DEEP_NESTING=$(awk '{n=gsub(/\{/,"{"); if(n>4) print NR": depth "n}' "$file" | head -3)
      if [ -n "$DEEP_NESTING" ]; then
        echo "### Deep nesting in $file"
        echo "$DEEP_NESTING"
      fi
      ;;
  esac
done
echo ""
```

### 7. Review Checklist
```bash
echo "## Review Checklist"
echo ""
echo "- [ ] Code does what it's supposed to do"
echo "- [ ] Error handling is appropriate"
echo "- [ ] No hardcoded values that should be config"
echo "- [ ] Logging is adequate"
echo "- [ ] Tests cover new functionality"
echo "- [ ] Documentation updated if needed"
echo "- [ ] No dead code or debug statements"
echo "- [ ] Security issues addressed"
echo ""
```

### 8. Generate Report File
```bash
REVIEW_DIR="$HOME/skippy/work/reviews"
mkdir -p "$REVIEW_DIR"
REPORT_FILE="$REVIEW_DIR/review_$(date +%Y%m%d_%H%M%S).md"

# Capture all output to file
# (This would be the full output above)

echo "Review saved to: $REPORT_FILE"
```
```

### 2.5 `/health` - System Health Check

Create: `$HOME/.claude/commands/health.md`

```markdown
---
description: Comprehensive system health check - hooks, MCP, paths, services
argument-hint: "[optional: 'full' for complete check, 'quick' for fast check]"
allowed-tools: ["Bash", "Read"]
---

# System Health Check

Validate entire Claude Code stack and development environment.

## Instructions

```bash
MODE="${1:-quick}"

echo "# System Health Check"
echo "**Time:** $(date)"
echo "**Mode:** $MODE"
echo ""

ISSUES=0
WARNINGS=0

check_pass() { echo "✅ $1"; }
check_fail() { echo "❌ $1"; ISSUES=$((ISSUES + 1)); }
check_warn() { echo "⚠️  $1"; WARNINGS=$((WARNINGS + 1)); }

# ==============================================================================
# Core Checks (Always Run)
# ==============================================================================

echo "## Core Systems"
echo ""

# Hooks
echo "### Hooks"
for hook in pre_compact session_start_check context_budget_monitor pre_tool_use; do
  HOOK_FILE="$HOME/.claude/hooks/${hook}.sh"
  if [ -x "$HOOK_FILE" ]; then
    check_pass "$hook is executable"
  elif [ -f "$HOOK_FILE" ]; then
    check_warn "$hook exists but not executable"
  else
    check_fail "$hook not found"
  fi
done
echo ""

# Settings
echo "### Configuration"
if [ -f "$HOME/.claude/settings.json" ]; then
  if python3 -m json.tool "$HOME/.claude/settings.json" > /dev/null 2>&1; then
    check_pass "settings.json is valid JSON"
  else
    check_fail "settings.json is invalid JSON"
  fi
else
  check_fail "settings.json not found"
fi
echo ""

# Skills
echo "### Skills"
SKILL_COUNT=$(find "$HOME/.claude/skills" -name "SKILL.md" 2>/dev/null | wc -l)
check_pass "Found $SKILL_COUNT skills"

# Check for required skills
for skill in session-management git-workflow debugging; do
  if [ -f "$HOME/.claude/skills/$skill/SKILL.md" ]; then
    check_pass "Required skill: $skill"
  else
    check_warn "Missing recommended skill: $skill"
  fi
done
echo ""

# Commands
echo "### Slash Commands"
CMD_COUNT=$(find "$HOME/.claude/commands" -name "*.md" 2>/dev/null | wc -l)
check_pass "Found $CMD_COUNT commands"
echo ""

# ==============================================================================
# Full Checks (If Requested)
# ==============================================================================

if [ "$MODE" = "full" ]; then
  
  echo "## Development Environment"
  echo ""
  
  # Git
  echo "### Git"
  if command -v git &>/dev/null; then
    check_pass "git installed: $(git --version | cut -d' ' -f3)"
    
    if git config user.name &>/dev/null; then
      check_pass "git user configured: $(git config user.name)"
    else
      check_warn "git user not configured"
    fi
  else
    check_fail "git not installed"
  fi
  echo ""
  
  # Python
  echo "### Python"
  if command -v python3 &>/dev/null; then
    check_pass "python3: $(python3 --version | cut -d' ' -f2)"
    
    for pkg in pytest black flake8 mypy radon; do
      if python3 -c "import $pkg" 2>/dev/null; then
        check_pass "$pkg installed"
      else
        check_warn "$pkg not installed"
      fi
    done
  else
    check_fail "python3 not installed"
  fi
  echo ""
  
  # Node.js
  echo "### Node.js"
  if command -v node &>/dev/null; then
    check_pass "node: $(node --version)"
    check_pass "npm: $(npm --version)"
  else
    check_warn "node not installed"
  fi
  echo ""
  
  # MCP Servers
  echo "## MCP Servers"
  echo ""
  
  if command -v claude &>/dev/null; then
    MCP_STATUS=$(claude mcp list 2>&1 || echo "Error")
    if echo "$MCP_STATUS" | grep -q "connected\|running"; then
      check_pass "MCP servers connected"
    else
      check_warn "MCP servers may not be connected"
    fi
  fi
  echo ""
  
  # WordPress (if applicable)
  echo "## WordPress"
  echo ""
  
  if command -v wp &>/dev/null; then
    check_pass "WP-CLI installed: $(wp --version | head -1)"
    
    WP_PATH="/home/dave/skippy/rundaverun_local_site/app/public"
    if [ -f "$WP_PATH/wp-config.php" ]; then
      check_pass "WordPress installation found"
      
      if wp --path="$WP_PATH" core is-installed 2>/dev/null; then
        check_pass "WordPress is functional"
      else
        check_warn "WordPress may have issues"
      fi
    else
      check_warn "WordPress installation not at expected path"
    fi
  else
    check_warn "WP-CLI not installed"
  fi
  echo ""
  
  # Disk Space
  echo "## System Resources"
  echo ""
  
  DISK_USED=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
  if [ "$DISK_USED" -lt 80 ]; then
    check_pass "Disk usage: ${DISK_USED}%"
  elif [ "$DISK_USED" -lt 90 ]; then
    check_warn "Disk usage: ${DISK_USED}% (getting full)"
  else
    check_fail "Disk usage: ${DISK_USED}% (critical)"
  fi
  
  MEM_AVAIL=$(free -m | awk '/Mem:/ {print $7}')
  if [ "$MEM_AVAIL" -gt 1000 ]; then
    check_pass "Available memory: ${MEM_AVAIL}MB"
  elif [ "$MEM_AVAIL" -gt 500 ]; then
    check_warn "Available memory: ${MEM_AVAIL}MB (low)"
  else
    check_fail "Available memory: ${MEM_AVAIL}MB (critical)"
  fi
  echo ""
  
  # Backups
  echo "## Backups"
  echo ""
  
  RECENT_BACKUP=$(find "$HOME/skippy/backups" -type f -mtime -1 2>/dev/null | head -1)
  if [ -n "$RECENT_BACKUP" ]; then
    check_pass "Recent backup found: $(basename "$RECENT_BACKUP")"
  else
    check_warn "No backups in last 24 hours"
  fi
  
  COMPACTION_COUNT=$(find "$HOME/.claude/compactions" -type d -mtime -7 2>/dev/null | wc -l)
  check_pass "Compaction saves (7 days): $COMPACTION_COUNT"
  echo ""
  
fi

# ==============================================================================
# Summary
# ==============================================================================

echo "## Summary"
echo ""
echo "| Status | Count |"
echo "|--------|-------|"
echo "| ✅ Passed | $(($(grep -c "✅" /dev/stdin || echo 0))) |"
echo "| ⚠️  Warnings | $WARNINGS |"
echo "| ❌ Failed | $ISSUES |"
echo ""

if [ "$ISSUES" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
  echo "**Status: All systems healthy** 🎉"
elif [ "$ISSUES" -eq 0 ]; then
  echo "**Status: Healthy with warnings** ⚠️"
else
  echo "**Status: Issues detected** ❌"
  echo ""
  echo "Run individual checks to diagnose issues."
fi
```
```

### 2.6 `/explain` - Code Explainer

Create: `$HOME/.claude/commands/explain.md`

```markdown
---
description: Explain code structure, trace execution, document complex logic
argument-hint: "<file> or <file:function> or <file:line>"
allowed-tools: ["Bash", "Read", "Grep"]
---

# Code Explainer

Analyze and explain code structure, dependencies, and execution flow.

## Instructions

```bash
TARGET="$1"

if [ -z "$TARGET" ]; then
  echo "Usage: /explain <file> or <file:function> or <file:line>"
  exit 0
fi

# Parse target
if echo "$TARGET" | grep -q ":"; then
  FILE=$(echo "$TARGET" | cut -d: -f1)
  FOCUS=$(echo "$TARGET" | cut -d: -f2)
else
  FILE="$TARGET"
  FOCUS=""
fi

if [ ! -f "$FILE" ]; then
  echo "File not found: $FILE"
  exit 1
fi

echo "# Code Analysis: $FILE"
echo ""

# ==============================================================================
# File Overview
# ==============================================================================

echo "## Overview"
echo ""
echo "- **Path:** $FILE"
echo "- **Size:** $(wc -l < "$FILE") lines"
echo "- **Type:** $(file -b "$FILE")"
echo "- **Last Modified:** $(stat -c %y "$FILE" | cut -d'.' -f1)"
echo ""

# ==============================================================================
# Structure Analysis
# ==============================================================================

echo "## Structure"
echo ""

case "$FILE" in
  *.py)
    echo "### Imports"
    grep -n "^import \|^from " "$FILE" | head -20
    echo ""
    
    echo "### Classes"
    grep -n "^class " "$FILE"
    echo ""
    
    echo "### Functions"
    grep -n "^def \|^async def " "$FILE"
    echo ""
    
    echo "### Constants"
    grep -n "^[A-Z_]\+ = " "$FILE" | head -10
    echo ""
    ;;
    
  *.js|*.ts)
    echo "### Imports"
    grep -n "^import \|^const .* = require" "$FILE" | head -20
    echo ""
    
    echo "### Exports"
    grep -n "^export " "$FILE"
    echo ""
    
    echo "### Functions"
    grep -n "function \|const .* = (" "$FILE" | head -20
    echo ""
    ;;
    
  *.sh)
    echo "### Functions"
    grep -n "^[a-z_]*() {" "$FILE"
    echo ""
    
    echo "### Variables"
    grep -n "^[A-Z_]*=" "$FILE" | head -10
    echo ""
    ;;
    
  *.php)
    echo "### Classes"
    grep -n "^class " "$FILE"
    echo ""
    
    echo "### Functions"
    grep -n "function " "$FILE"
    echo ""
    ;;
esac

# ==============================================================================
# Focus Analysis (if specified)
# ==============================================================================

if [ -n "$FOCUS" ]; then
  echo "## Focus: $FOCUS"
  echo ""
  
  if echo "$FOCUS" | grep -qE "^[0-9]+$"; then
    # Line number
    LINE="$FOCUS"
    START=$((LINE - 10))
    [ $START -lt 1 ] && START=1
    END=$((LINE + 20))
    
    echo "### Context (lines $START-$END)"
    echo '```'
    sed -n "${START},${END}p" "$FILE" | nl -ba -v $START
    echo '```'
  else
    # Function name
    FUNC="$FOCUS"
    
    echo "### Function: $FUNC"
    echo ""
    
    # Find function definition
    case "$FILE" in
      *.py)
        FUNC_LINE=$(grep -n "^def $FUNC\|^async def $FUNC" "$FILE" | cut -d: -f1 | head -1)
        ;;
      *.js|*.ts)
        FUNC_LINE=$(grep -n "function $FUNC\|const $FUNC = " "$FILE" | cut -d: -f1 | head -1)
        ;;
      *.sh)
        FUNC_LINE=$(grep -n "^$FUNC() {" "$FILE" | cut -d: -f1 | head -1)
        ;;
    esac
    
    if [ -n "$FUNC_LINE" ]; then
      # Extract function body (simplified)
      echo "#### Definition (starting line $FUNC_LINE)"
      echo '```'
      sed -n "${FUNC_LINE},$((FUNC_LINE + 30))p" "$FILE"
      echo '```'
      
      echo ""
      echo "#### Callers"
      grep -rn "$FUNC(" --include="*.py" --include="*.js" --include="*.sh" . 2>/dev/null | grep -v "^$FILE:$FUNC_LINE" | head -10
    fi
  fi
fi

# ==============================================================================
# Dependencies
# ==============================================================================

echo "## Dependencies"
echo ""

case "$FILE" in
  *.py)
    echo "### External Packages"
    grep "^import \|^from " "$FILE" | grep -v "^\." | sort -u
    
    echo ""
    echo "### Internal Modules"
    grep "^from \." "$FILE" | sort -u
    ;;
esac
echo ""

# ==============================================================================
# Related Files
# ==============================================================================

echo "## Related Files"
echo ""

BASENAME=$(basename "$FILE" | sed 's/\.[^.]*$//')

echo "### Tests"
find . -name "*test*$BASENAME*" -o -name "*${BASENAME}*test*" 2>/dev/null | head -5

echo ""
echo "### Similar Files"
find . -name "*$BASENAME*" ! -name "$(basename "$FILE")" 2>/dev/null | head -5

echo ""
echo "### Files That Import This"
grep -rl "import.*$BASENAME\|from.*$BASENAME" --include="*.py" --include="*.js" . 2>/dev/null | head -10
```
```

---

## 3. Hook Enhancements

### 3.1 Enhanced Error Handling for All Hooks

Update all hooks with robust error handling. Add this pattern to the top of each hook:

```bash
#!/bin/bash
# Add to top of all hooks

set -euo pipefail

# Trap errors - ensure hook never blocks Claude
trap 'echo "{\"decision\": \"allow\"}" 2>/dev/null; exit 0' ERR SIGTERM SIGINT

# Timeout protection
TIMEOUT=5  # seconds
timeout_handler() {
  echo "{\"decision\": \"allow\"}"
  exit 0
}
trap timeout_handler ALRM
( sleep $TIMEOUT; kill -ALRM $$ 2>/dev/null ) &
TIMEOUT_PID=$!

# Cleanup timeout on exit
cleanup_timeout() {
  kill $TIMEOUT_PID 2>/dev/null || true
}
trap cleanup_timeout EXIT
```

### 3.2 New Hook: `post_edit_lint.sh`

Create: `$HOME/.claude/hooks/post_edit_lint.sh`

```bash
#!/bin/bash
# post_edit_lint.sh - Auto-lint and format after file edits
# Hook: PostToolUse (matcher: Edit|Write)
# Version: 1.0.0

set -euo pipefail

# Safety: never block Claude
trap 'exit 0' ERR SIGTERM SIGINT

# Read input
INPUT=$(cat)

# Extract file path
FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('file_path', d.get('filePath', '')))
except:
    print('')
" 2>/dev/null || echo "")

[ -z "$FILE_PATH" ] && exit 0
[ ! -f "$FILE_PATH" ] && exit 0

# Log
LOG_DIR="$HOME/.claude/logs"
mkdir -p "$LOG_DIR"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Linting: $FILE_PATH" >> "$LOG_DIR/lint.log"

# Auto-format based on file type
case "$FILE_PATH" in
  *.py)
    # Python: black + isort
    if command -v black &>/dev/null; then
      black "$FILE_PATH" --quiet 2>/dev/null || true
    fi
    if command -v isort &>/dev/null; then
      isort "$FILE_PATH" --quiet 2>/dev/null || true
    fi
    # Quick lint check (don't block, just log)
    if command -v flake8 &>/dev/null; then
      ISSUES=$(flake8 "$FILE_PATH" --max-line-length=100 2>/dev/null | wc -l || echo 0)
      [ "$ISSUES" -gt 0 ] && echo "  Lint issues: $ISSUES" >> "$LOG_DIR/lint.log"
    fi
    ;;
    
  *.js|*.ts|*.jsx|*.tsx)
    # JavaScript/TypeScript: prettier
    if command -v npx &>/dev/null; then
      npx prettier --write "$FILE_PATH" 2>/dev/null || true
    fi
    ;;
    
  *.sh)
    # Shell: check syntax, log issues
    if command -v shellcheck &>/dev/null; then
      ISSUES=$(shellcheck "$FILE_PATH" 2>/dev/null | grep -c "^In\|SC[0-9]" || echo 0)
      [ "$ISSUES" -gt 0 ] && echo "  ShellCheck issues: $ISSUES" >> "$LOG_DIR/lint.log"
    fi
    ;;
    
  *.php)
    # PHP: syntax check
    php -l "$FILE_PATH" 2>/dev/null | grep -v "No syntax errors" >> "$LOG_DIR/lint.log" || true
    ;;
    
  *.json)
    # JSON: validate
    python3 -m json.tool "$FILE_PATH" > /dev/null 2>&1 || echo "  Invalid JSON: $FILE_PATH" >> "$LOG_DIR/lint.log"
    ;;
    
  *.yaml|*.yml)
    # YAML: validate
    python3 -c "import yaml; yaml.safe_load(open('$FILE_PATH'))" 2>/dev/null || echo "  Invalid YAML: $FILE_PATH" >> "$LOG_DIR/lint.log"
    ;;
esac

exit 0
```

### 3.3 New Hook: `dev_context_tracker.sh`

Create: `$HOME/.claude/hooks/dev_context_tracker.sh`

```bash
#!/bin/bash
# dev_context_tracker.sh - Track development context for smarter assistance
# Hook: SessionStart
# Version: 1.0.0

set -euo pipefail
trap 'exit 0' ERR

CONTEXT_FILE="$HOME/.claude/dev_context.json"
CONTEXT_DIR="$HOME/.claude"
mkdir -p "$CONTEXT_DIR"

# Get current development context
BRANCH=$(git branch --show-current 2>/dev/null || echo "none")
RECENT_FILES=$(git diff --name-only HEAD~5 2>/dev/null | head -10 | jq -R . | jq -s . 2>/dev/null || echo '[]')
UNCOMMITTED=$(git status --porcelain 2>/dev/null | wc -l || echo 0)
LAST_COMMIT=$(git log -1 --format='%s' 2>/dev/null || echo "none")
VENV="${VIRTUAL_ENV:-none}"

# Detect project type
PROJECT_TYPE="unknown"
[ -f "package.json" ] && PROJECT_TYPE="node"
[ -f "pyproject.toml" ] || [ -f "setup.py" ] && PROJECT_TYPE="python"
[ -f "composer.json" ] && PROJECT_TYPE="php"
[ -f "Cargo.toml" ] && PROJECT_TYPE="rust"
[ -f "wp-config.php" ] && PROJECT_TYPE="wordpress"

# Get test status (quick check)
TEST_STATUS="unknown"
if [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then
  pytest --collect-only -q 2>/dev/null | tail -1 | grep -q "error" && TEST_STATUS="failing" || TEST_STATUS="passing"
fi

# Write context
cat > "$CONTEXT_FILE" << EOF
{
  "last_updated": "$(date -Iseconds)",
  "working_directory": "$(pwd)",
  "git": {
    "branch": "$BRANCH",
    "uncommitted_changes": $UNCOMMITTED,
    "last_commit": "$LAST_COMMIT"
  },
  "recent_files": $RECENT_FILES,
  "project_type": "$PROJECT_TYPE",
  "virtual_env": "$VENV",
  "test_status": "$TEST_STATUS"
}
EOF

exit 0
```

### 3.4 Enhanced `pre_tool_use.sh`

Add these additional checks to your existing `pre_tool_use.sh`:

```bash
# Add after existing checks in pre_tool_use.sh

# ==============================================================================
# Git Safety Checks
# ==============================================================================

if [ "$TOOL_NAME" = "Bash" ]; then
  
  # Block dangerous git operations without explicit approval
  DANGEROUS_GIT=(
    "git push --force"
    "git push -f"
    "git reset --hard"
    "git clean -fd"
    "git checkout -- ."
    "git stash drop"
    "git branch -D"
  )
  
  for pattern in "${DANGEROUS_GIT[@]}"; do
    if [[ "$COMMAND" == *"$pattern"* ]]; then
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] BLOCKED GIT: $COMMAND" >> "$LOG_DIR/blocked_git.log"
      echo "{\"decision\": \"block\", \"reason\": \"Dangerous git operation requires explicit user approval: $pattern\"}"
      exit 0
    fi
  done
  
  # Warn on git push to main/master
  if [[ "$COMMAND" == *"git push"* ]] && [[ "$COMMAND" == *"main"* || "$COMMAND" == *"master"* ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: Push to main/master: $COMMAND" >> "$LOG_DIR/git_warnings.log"
  fi
  
  # Warn on git commit --amend
  if [[ "$COMMAND" == *"git commit"* ]] && [[ "$COMMAND" == *"--amend"* ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: Amending commit: $COMMAND" >> "$LOG_DIR/git_warnings.log"
  fi
  
fi

# ==============================================================================
# Database Safety
# ==============================================================================

if [ "$TOOL_NAME" = "Bash" ]; then
  
  # Block destructive database operations
  if echo "$COMMAND" | grep -qiE "DROP TABLE|DROP DATABASE|TRUNCATE|DELETE FROM.*WHERE 1|DELETE FROM [^W]"; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] BLOCKED DB: $COMMAND" >> "$LOG_DIR/blocked_db.log"
    echo "{\"decision\": \"block\", \"reason\": \"Destructive database operation requires explicit approval\"}"
    exit 0
  fi
  
fi

# ==============================================================================
# Network Safety
# ==============================================================================

if [ "$TOOL_NAME" = "Bash" ]; then
  
  # Warn on curl/wget to unknown domains
  if echo "$COMMAND" | grep -qE "curl|wget"; then
    URL=$(echo "$COMMAND" | grep -oE 'https?://[^[:space:]]+' | head -1)
    if [ -n "$URL" ]; then
      DOMAIN=$(echo "$URL" | awk -F/ '{print $3}')
      
      # Known safe domains
      SAFE_DOMAINS="github.com api.github.com pypi.org npmjs.com localhost 127.0.0.1"
      
      if ! echo "$SAFE_DOMAINS" | grep -q "$DOMAIN"; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] NETWORK: $DOMAIN - $COMMAND" >> "$LOG_DIR/network_access.log"
      fi
    fi
  fi
  
fi
```

### 3.5 Update `settings.json` for New Hooks

Update: `$HOME/.claude/settings.json`

Add to the hooks section:

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
    ]
  }
}
```

---

## 4. New Skills

### 4.1 `dev-workflow` Skill

Create: `$HOME/.claude/skills/dev-workflow/SKILL.md`

```markdown
---
name: dev-workflow
description: Development session management and best practices. Auto-invoke when starting coding sessions, working on features, or managing development workflow.
---

# Development Workflow Skill

**Version:** 1.0.0
**Last Updated:** 2025-12-01
**Auto-Invoke:** Yes - development, coding, feature, workflow, session

## When to Use This Skill

Auto-invoke when:
- Starting a new development session
- Working on features or bug fixes
- Managing branches and commits
- Preparing code for review

## Session Initialization

### Start Development Session
```bash
# Create development session directory
init_dev_session() {
  local description="${1:-coding}"
  local category="${2:-general}"
  
  SESSION_DIR="$HOME/skippy/work/dev/$(date +%Y%m%d_%H%M%S)_${description}"
  mkdir -p "$SESSION_DIR"/{scratch,tests,notes}
  
  # Capture starting state
  {
    echo "# Development Session: $description"
    echo "Started: $(date)"
    echo "Directory: $SESSION_DIR"
    echo ""
    echo "## Git Status"
    git status --short
    echo ""
    echo "## Current Branch"
    git branch --show-current
    echo ""
    echo "## Recent Commits"
    git log --oneline -5
  } > "$SESSION_DIR/SESSION_START.md"
  
  # Save uncommitted changes as patch
  git diff > "$SESSION_DIR/uncommitted_start.patch" 2>/dev/null
  
  echo "Session initialized: $SESSION_DIR"
  export DEV_SESSION_DIR="$SESSION_DIR"
}
```

### Session Checkpoint
```bash
# Save progress checkpoint
checkpoint() {
  local message="${1:-checkpoint}"
  local checkpoint_dir="$DEV_SESSION_DIR/checkpoints/$(date +%H%M%S)_$message"
  mkdir -p "$checkpoint_dir"
  
  # Save current diff
  git diff > "$checkpoint_dir/changes.patch"
  git diff --staged > "$checkpoint_dir/staged.patch"
  
  # List modified files
  git status --short > "$checkpoint_dir/status.txt"
  
  echo "Checkpoint saved: $checkpoint_dir"
}
```

### Session Summary
```bash
# Generate session summary
session_summary() {
  cat > "$DEV_SESSION_DIR/SESSION_END.md" << EOF
# Session Summary

**Started:** $(head -2 "$DEV_SESSION_DIR/SESSION_START.md" | tail -1)
**Ended:** $(date)

## Changes Made
$(git diff --stat HEAD~1 2>/dev/null || echo "No commits yet")

## Files Modified
$(git status --short)

## Commits
$(git log --oneline --since="$(stat -c %Y "$DEV_SESSION_DIR/SESSION_START.md" | xargs -I {} date -d @{})" 2>/dev/null || echo "No new commits")

## Notes
- 

## Next Steps
- 
EOF

  echo "Session summary: $DEV_SESSION_DIR/SESSION_END.md"
}
```

## Feature Development Workflow

### 1. Start Feature
```bash
start_feature() {
  local name="$1"
  
  # Create branch
  git checkout -b "feature/$name" main
  
  # Initialize session
  init_dev_session "$name" "feature"
  
  # Create feature spec
  cat > "$DEV_SESSION_DIR/FEATURE_SPEC.md" << EOF
# Feature: $name

## Description


## Acceptance Criteria
- [ ] 

## Technical Notes


## Testing Plan

EOF
  
  echo "Feature branch created: feature/$name"
}
```

### 2. Development Cycle
```bash
# Regular development cycle
dev_cycle() {
  echo "## Development Cycle"
  echo ""
  echo "1. Write failing test"
  echo "2. Implement feature"
  echo "3. Run tests: pytest -v"
  echo "4. Lint: flake8 && black ."
  echo "5. Checkpoint: checkpoint 'description'"
  echo "6. Commit when ready"
}
```

### 3. Prepare for Review
```bash
prepare_review() {
  echo "## Pre-Review Checklist"
  echo ""
  
  # Run tests
  echo "### Tests"
  pytest -v --tb=short && echo "✅ Tests pass" || echo "❌ Tests fail"
  
  # Lint
  echo "### Lint"
  flake8 && echo "✅ No lint errors" || echo "❌ Lint errors"
  
  # Coverage
  echo "### Coverage"
  pytest --cov=src --cov-fail-under=80 -q
  
  # Security
  echo "### Security"
  bandit -r src/ -q && echo "✅ No security issues" || echo "⚠️ Security warnings"
  
  # Diff summary
  echo "### Changes"
  git diff --stat main
}
```

## Quick Commands

| Command | Description |
|---------|-------------|
| `init_dev_session "name"` | Start session |
| `checkpoint "msg"` | Save checkpoint |
| `session_summary` | End session |
| `start_feature "name"` | Start feature branch |
| `prepare_review` | Pre-review checks |

## Best Practices

### DO
- Always work in session directories
- Checkpoint frequently
- Write tests first
- Run lint before commits
- Document decisions

### DON'T
- Work in /tmp/
- Skip tests
- Force push without review
- Commit without checking diff
- Leave sessions undocumented

## Integration

Works with:
- **git-workflow** - Branch management
- **testing-and-qa** - Test execution
- **code-review** - Review preparation
- **session-management** - Session preservation
```

### 4.2 `quick-fixes` Skill

Create: `$HOME/.claude/skills/quick-fixes/SKILL.md`

```markdown
---
name: quick-fixes
description: Common error solutions and quick fixes. Auto-invoke when encountering errors, exceptions, or common development issues.
---

# Quick Fixes Skill

**Version:** 1.0.0
**Last Updated:** 2025-12-01
**Auto-Invoke:** Yes - error, exception, fix, problem, issue, broken

## When to Use This Skill

Auto-invoke when:
- Encountering error messages
- Debugging common issues
- Looking for quick solutions

## Error Quick Reference

### Python Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'X'` | Package not installed | `pip install X` |
| `ImportError: cannot import name 'X'` | Circular import or wrong version | Check import order, `pip install --upgrade` |
| `AttributeError: 'NoneType' has no attribute` | Variable is None | Add null check before access |
| `KeyError: 'X'` | Key not in dictionary | Use `.get('X', default)` |
| `IndexError: list index out of range` | List shorter than expected | Check length first |
| `TypeError: 'X' object is not callable` | Calling non-function | Check parentheses, variable shadowing |
| `RecursionError` | Infinite recursion | Check base case, use iteration |
| `MemoryError` | Out of memory | Process in chunks, use generators |

### JavaScript Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `TypeError: Cannot read property 'X' of undefined` | Accessing property on undefined | Add optional chaining `?.` |
| `ReferenceError: X is not defined` | Variable not declared | Check spelling, scope, imports |
| `SyntaxError: Unexpected token` | Syntax mistake | Check for missing brackets, commas |
| `TypeError: X is not a function` | Calling non-function | Check variable type |

### Shell Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `command not found` | Not installed or not in PATH | Install or add to PATH |
| `Permission denied` | No execute permission | `chmod +x file` |
| `No such file or directory` | Path doesn't exist | Check path, create directory |
| `syntax error near unexpected token` | Bash syntax error | Check quotes, parentheses |

### Git Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `fatal: not a git repository` | Not in git repo | `cd` to repo or `git init` |
| `error: failed to push some refs` | Remote has changes | `git pull --rebase` first |
| `CONFLICT` | Merge conflict | Resolve in files, then `git add` |
| `detached HEAD` | Not on branch | `git checkout branch-name` |

### Network Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Connection refused` | Service not running | Start service, check port |
| `Connection timed out` | Network/firewall issue | Check connectivity, firewall |
| `Name or service not known` | DNS failure | Check hostname, /etc/hosts |
| `SSL: CERTIFICATE_VERIFY_FAILED` | SSL issue | Update certs, check date |

## Quick Fix Commands

### Python
```bash
# Reinstall package
pip uninstall X && pip install X

# Clear cache
pip cache purge

# Virtual environment issues
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Node.js
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Fix permissions
sudo chown -R $(whoami) ~/.npm
```

### Git
```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Discard all local changes
git checkout -- .
git clean -fd

# Fix detached HEAD
git checkout -b temp-branch
git checkout main
git merge temp-branch
```

### Permissions
```bash
# Fix file permissions
chmod 644 file.txt      # Regular file
chmod 755 script.sh     # Executable
chmod 600 private.key   # Private file

# Fix ownership
sudo chown $USER:$USER file
sudo chown -R $USER:$USER directory/
```

### Disk Space
```bash
# Find large files
find / -xdev -type f -size +100M 2>/dev/null | head -20

# Clear caches
pip cache purge
npm cache clean --force
docker system prune -a

# Clear logs
sudo journalctl --vacuum-time=7d
```

## Diagnostic Commands

```bash
# System info
uname -a
cat /etc/os-release

# Memory
free -h
top -bn1 | head -20

# Disk
df -h
du -sh * | sort -h

# Network
ss -tlnp
curl -I https://example.com

# Processes
ps aux --sort=-%mem | head -10
lsof -i :8000
```

## Integration

Reference when:
- **debugging** skill encounters an error
- **pre_tool_use** hook blocks a command
- User reports an issue
```

---

## 5. Security Hardening

### 5.1 Create Security Audit Command

Create: `$HOME/.claude/commands/security-scan.md`

```markdown
---
description: Security scan - check for secrets, vulnerabilities, and security issues
argument-hint: "[optional: 'full' for comprehensive scan, 'quick' for fast check]"
allowed-tools: ["Bash", "Read", "Grep"]
---

# Security Scan

Comprehensive security scanning for secrets, vulnerabilities, and misconfigurations.

## Instructions

```bash
MODE="${1:-quick}"

echo "# Security Scan"
echo "**Mode:** $MODE"
echo "**Time:** $(date)"
echo ""

CRITICAL=0
HIGH=0
MEDIUM=0
LOW=0

report_issue() {
  local severity="$1"
  local message="$2"
  
  case "$severity" in
    CRITICAL) echo "🔴 CRITICAL: $message"; CRITICAL=$((CRITICAL + 1)) ;;
    HIGH)     echo "🟠 HIGH: $message"; HIGH=$((HIGH + 1)) ;;
    MEDIUM)   echo "🟡 MEDIUM: $message"; MEDIUM=$((MEDIUM + 1)) ;;
    LOW)      echo "🔵 LOW: $message"; LOW=$((LOW + 1)) ;;
  esac
}

# ==============================================================================
# Secrets Detection
# ==============================================================================

echo "## Secrets Detection"
echo ""

# Hardcoded passwords
echo "### Hardcoded Credentials"
PASSWORDS=$(grep -rn --include="*.py" --include="*.js" --include="*.php" --include="*.sh" \
  -E "(password|passwd|pwd)\s*[=:]\s*['\"][^'\"]+['\"]" . 2>/dev/null | grep -v "test\|example\|sample" | head -10)
  
if [ -n "$PASSWORDS" ]; then
  report_issue "CRITICAL" "Hardcoded passwords found"
  echo "$PASSWORDS" | head -5
else
  echo "✅ No hardcoded passwords"
fi

# API Keys
echo ""
echo "### API Keys"
APIKEYS=$(grep -rn --include="*.py" --include="*.js" --include="*.php" --include="*.env*" \
  -E "(api_key|apikey|api-key|access_key)\s*[=:]\s*['\"][A-Za-z0-9_-]{20,}['\"]" . 2>/dev/null | head -10)
  
if [ -n "$APIKEYS" ]; then
  report_issue "CRITICAL" "API keys found in code"
  echo "$APIKEYS" | head -3
else
  echo "✅ No exposed API keys"
fi

# Private keys
echo ""
echo "### Private Keys"
PRIVATEKEYS=$(find . -name "*.pem" -o -name "*.key" -o -name "id_rsa" -o -name "id_ed25519" 2>/dev/null | grep -v ".git")

if [ -n "$PRIVATEKEYS" ]; then
  report_issue "HIGH" "Private key files found"
  echo "$PRIVATEKEYS"
else
  echo "✅ No private key files in repo"
fi

# .env files in git
echo ""
echo "### Environment Files"
if git ls-files --error-unmatch .env .env.local .env.production 2>/dev/null; then
  report_issue "CRITICAL" ".env files tracked in git"
else
  echo "✅ .env files not tracked"
fi

# ==============================================================================
# File Permissions
# ==============================================================================

echo ""
echo "## File Permissions"
echo ""

# World-writable files
WORLDWRITE=$(find . -type f -perm -002 2>/dev/null | grep -v ".git" | head -10)
if [ -n "$WORLDWRITE" ]; then
  report_issue "MEDIUM" "World-writable files found"
  echo "$WORLDWRITE"
else
  echo "✅ No world-writable files"
fi

# Executable scripts without proper permissions
BADEXEC=$(find . -name "*.sh" ! -perm -100 2>/dev/null | head -10)
if [ -n "$BADEXEC" ]; then
  report_issue "LOW" "Shell scripts not executable"
  echo "$BADEXEC" | head -3
else
  echo "✅ Script permissions OK"
fi

# ==============================================================================
# Code Vulnerabilities
# ==============================================================================

if [ "$MODE" = "full" ]; then
  
  echo ""
  echo "## Code Vulnerabilities"
  echo ""
  
  # SQL Injection
  echo "### SQL Injection"
  SQLI=$(grep -rn --include="*.py" --include="*.php" \
    -E "execute\s*\([^)]*%|execute\s*\([^)]*\+|query\s*\([^)]*\\\$" . 2>/dev/null | head -10)
    
  if [ -n "$SQLI" ]; then
    report_issue "HIGH" "Potential SQL injection"
    echo "$SQLI" | head -3
  else
    echo "✅ No obvious SQL injection"
  fi
  
  # Command Injection
  echo ""
  echo "### Command Injection"
  CMDI=$(grep -rn --include="*.py" --include="*.php" \
    -E "os\.system\s*\(|subprocess\.(call|run|Popen)\s*\([^)]*shell\s*=\s*True|exec\s*\(" . 2>/dev/null | head -10)
    
  if [ -n "$CMDI" ]; then
    report_issue "HIGH" "Potential command injection"
    echo "$CMDI" | head -3
  else
    echo "✅ No obvious command injection"
  fi
  
  # XSS
  echo ""
  echo "### Cross-Site Scripting (XSS)"
  XSS=$(grep -rn --include="*.php" --include="*.js" \
    -E "innerHTML\s*=|document\.write\s*\(|\.html\s*\(" . 2>/dev/null | grep -v "sanitize\|escape" | head -10)
    
  if [ -n "$XSS" ]; then
    report_issue "MEDIUM" "Potential XSS vulnerabilities"
    echo "$XSS" | head -3
  else
    echo "✅ No obvious XSS"
  fi
  
  # Eval
  echo ""
  echo "### Dangerous Functions"
  EVAL=$(grep -rn --include="*.py" --include="*.js" --include="*.php" \
    -E "\beval\s*\(|\bexec\s*\(" . 2>/dev/null | grep -v "test\|spec" | head -10)
    
  if [ -n "$EVAL" ]; then
    report_issue "HIGH" "eval/exec usage found"
    echo "$EVAL" | head -3
  else
    echo "✅ No dangerous function usage"
  fi
  
  # Python security scan
  if command -v bandit &>/dev/null; then
    echo ""
    echo "### Bandit Security Scan"
    bandit -r . -q --format txt 2>/dev/null | head -30 || echo "Bandit scan complete"
  fi
  
fi

# ==============================================================================
# Dependency Vulnerabilities
# ==============================================================================

if [ "$MODE" = "full" ]; then
  
  echo ""
  echo "## Dependency Vulnerabilities"
  echo ""
  
  # Python dependencies
  if [ -f "requirements.txt" ] && command -v safety &>/dev/null; then
    echo "### Python Dependencies"
    safety check -r requirements.txt 2>/dev/null | head -20 || echo "Safety check complete"
  fi
  
  # Node dependencies
  if [ -f "package.json" ] && command -v npm &>/dev/null; then
    echo ""
    echo "### Node.js Dependencies"
    npm audit --json 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    vulns = data.get('vulnerabilities', {})
    for name, info in list(vulns.items())[:5]:
        severity = info.get('severity', 'unknown')
        print(f'{severity.upper()}: {name}')
except:
    pass
" 2>/dev/null || echo "npm audit complete"
  fi
  
fi

# ==============================================================================
# Summary
# ==============================================================================

echo ""
echo "## Summary"
echo ""
echo "| Severity | Count |"
echo "|----------|-------|"
echo "| 🔴 Critical | $CRITICAL |"
echo "| 🟠 High | $HIGH |"
echo "| 🟡 Medium | $MEDIUM |"
echo "| 🔵 Low | $LOW |"
echo ""

TOTAL=$((CRITICAL + HIGH + MEDIUM + LOW))
if [ "$TOTAL" -eq 0 ]; then
  echo "**Status: No security issues found** ✅"
elif [ "$CRITICAL" -gt 0 ]; then
  echo "**Status: CRITICAL issues require immediate attention** 🔴"
elif [ "$HIGH" -gt 0 ]; then
  echo "**Status: HIGH severity issues found** 🟠"
else
  echo "**Status: Minor issues found** 🟡"
fi
```
```

### 5.2 Enhanced Sensitive Path Protection

Update `.gitignore` and add to skill:

Create: `$HOME/.claude/skills/security-config/SKILL.md`

```markdown
---
name: security-config
description: Security configuration and sensitive file protection. Auto-invoke when handling credentials, secrets, or security-sensitive operations.
---

# Security Configuration Skill

## Protected Paths

### Never Access
```
.ssh/id_*
.aws/credentials
.config/gcloud/
*.pem
*.key
.env
.env.*
*credentials*
*secrets*
```

### Never Commit
```
.env
.env.*
*.pem
*.key
*.p12
*.pfx
credentials.json
secrets.yaml
id_rsa*
*.sql
*.dump
```

### Required .gitignore Entries
```gitignore
# Secrets
.env
.env.*
*.pem
*.key
*.p12
credentials.json
secrets/

# Databases
*.sql
*.dump
*.sqlite

# IDE
.idea/
.vscode/settings.json
*.swp

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Build
dist/
build/
__pycache__/
node_modules/
```

## Credential Handling

### DO
- Use environment variables
- Use secret managers (AWS Secrets, Vault)
- Rotate credentials regularly
- Use least privilege

### DON'T
- Hardcode credentials
- Commit secrets to git
- Log sensitive data
- Share credentials in plain text

## Quick Security Checks
```bash
# Check for secrets in git history
git log -p | grep -E "(password|secret|key|token)\s*=" | head -10

# Check file permissions
find . -perm -002 -type f

# Check for .env in git
git ls-files | grep -E "\.env"
```
```

---

## 6. Automation Enhancements

### 6.1 Daily Maintenance Script

Create: `$HOME/.claude/scripts/daily_maintenance.sh`

```bash
#!/bin/bash
# daily_maintenance.sh - Automated daily maintenance tasks
# Version: 1.0.0
# Schedule: Add to cron for daily execution

set -euo pipefail

LOG_FILE="$HOME/.claude/logs/maintenance_$(date +%Y%m%d).log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "=== Daily Maintenance Started ==="

# ==============================================================================
# 1. Cleanup Old Files
# ==============================================================================

log "Cleaning old files..."

# Old compaction saves (keep 7 days)
find "$HOME/.claude/compactions" -type d -mtime +7 -exec rm -rf {} \; 2>/dev/null || true
log "  Cleaned old compaction saves"

# Old debug sessions (keep 7 days)
find "$HOME/.claude/debug_sessions" -type f -mtime +7 -delete 2>/dev/null || true
log "  Cleaned old debug sessions"

# Old logs (keep 30 days)
find "$HOME/.claude/logs" -name "*.log" -mtime +30 -delete 2>/dev/null || true
log "  Cleaned old logs"

# Rotate large logs
for logfile in "$HOME/.claude/logs"/*.log; do
  if [ -f "$logfile" ] && [ $(stat -c%s "$logfile" 2>/dev/null || echo 0) -gt 10485760 ]; then
    mv "$logfile" "${logfile}.$(date +%Y%m%d)"
    gzip "${logfile}.$(date +%Y%m%d)"
    log "  Rotated: $logfile"
  fi
done

# ==============================================================================
# 2. Validate Configuration
# ==============================================================================

log "Validating configuration..."

# Check settings.json
if python3 -m json.tool "$HOME/.claude/settings.json" > /dev/null 2>&1; then
  log "  settings.json: OK"
else
  log "  ERROR: settings.json is invalid!"
fi

# Check hook permissions
for hook in "$HOME/.claude/hooks"/*.sh; do
  if [ -x "$hook" ]; then
    log "  $(basename "$hook"): executable"
  else
    chmod +x "$hook"
    log "  $(basename "$hook"): fixed permissions"
  fi
done

# ==============================================================================
# 3. Update Skills Index
# ==============================================================================

log "Updating skills index..."

SKILLS_DIR="$HOME/.claude/skills"
INDEX_FILE="$SKILLS_DIR/INDEX.md"

{
  echo "# Skills Index"
  echo ""
  echo "**Last Updated:** $(date)"
  echo "**Total Skills:** $(find "$SKILLS_DIR" -name "SKILL.md" | wc -l)"
  echo ""
  echo "| Skill | Description |"
  echo "|-------|-------------|"
  
  for skill_dir in "$SKILLS_DIR"/*/; do
    [ -d "$skill_dir" ] || continue
    skill_name=$(basename "$skill_dir")
    skill_file="$skill_dir/SKILL.md"
    
    if [ -f "$skill_file" ]; then
      desc=$(grep -m1 "^description:" "$skill_file" | cut -d: -f2- | cut -c1-50 | tr -d '"')
      echo "| $skill_name | $desc... |"
    fi
  done
} > "$INDEX_FILE"

log "  Index updated: $INDEX_FILE"

# ==============================================================================
# 4. Health Check
# ==============================================================================

log "Running health check..."

ISSUES=0

# Check disk space
DISK_USED=$(df -h "$HOME" | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$DISK_USED" -gt 90 ]; then
  log "  WARNING: Disk usage at ${DISK_USED}%"
  ISSUES=$((ISSUES + 1))
else
  log "  Disk usage: ${DISK_USED}%"
fi

# Check for failed hooks in logs
FAILED_HOOKS=$(grep -c "ERROR\|FAILED" "$HOME/.claude/logs"/hook*.log 2>/dev/null || echo 0)
if [ "$FAILED_HOOKS" -gt 0 ]; then
  log "  WARNING: $FAILED_HOOKS hook errors in logs"
  ISSUES=$((ISSUES + 1))
fi

# ==============================================================================
# 5. Summary
# ==============================================================================

log "=== Maintenance Complete ==="
log "Issues found: $ISSUES"

if [ "$ISSUES" -gt 0 ]; then
  log "Review log for details: $LOG_FILE"
fi

exit 0
```

### 6.2 Auto-Backup Hook

Create: `$HOME/.claude/hooks/auto_backup.sh`

```bash
#!/bin/bash
# auto_backup.sh - Automatic backup on significant changes
# Hook: PostToolUse (matcher: Edit|Write)
# Version: 1.0.0

set -euo pipefail
trap 'exit 0' ERR

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('file_path', d.get('filePath', '')))
except:
    print('')
" 2>/dev/null || echo "")

[ -z "$FILE_PATH" ] && exit 0
[ ! -f "$FILE_PATH" ] && exit 0

BACKUP_DIR="$HOME/.claude/backups/files"
mkdir -p "$BACKUP_DIR"

# Determine if backup needed (important files only)
SHOULD_BACKUP=false

case "$FILE_PATH" in
  *.py|*.js|*.ts|*.php|*.sh)
    SHOULD_BACKUP=true
    ;;
  */.claude/*)
    SHOULD_BACKUP=true
    ;;
  */wp-content/*)
    SHOULD_BACKUP=true
    ;;
esac

if $SHOULD_BACKUP; then
  # Create backup with timestamp
  BASENAME=$(basename "$FILE_PATH")
  BACKUP_FILE="$BACKUP_DIR/${BASENAME%.}.$(date +%Y%m%d_%H%M%S).bak"
  
  cp "$FILE_PATH" "$BACKUP_FILE"
  
  # Keep only last 10 backups per file
  ls -t "$BACKUP_DIR/${BASENAME%.*}."*.bak 2>/dev/null | tail -n +11 | xargs -r rm
  
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backed up: $FILE_PATH" >> "$HOME/.claude/logs/backups.log"
fi

exit 0
```

### 6.3 Git Auto-Stash Before Risky Operations

Add to `pre_tool_use.sh`:

```bash
# Add to pre_tool_use.sh

# Auto-stash before risky git operations
if [ "$TOOL_NAME" = "Bash" ]; then
  
  if [[ "$COMMAND" == *"git checkout"* ]] || [[ "$COMMAND" == *"git switch"* ]] || [[ "$COMMAND" == *"git rebase"* ]]; then
    # Check for uncommitted changes
    if git diff --quiet 2>/dev/null && git diff --cached --quiet 2>/dev/null; then
      : # No changes, proceed
    else
      # Auto-stash
      STASH_MSG="auto-stash-$(date +%Y%m%d_%H%M%S)"
      git stash push -m "$STASH_MSG" 2>/dev/null || true
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] Auto-stashed: $STASH_MSG" >> "$LOG_DIR/auto_stash.log"
    fi
  fi
  
fi
```

---

## 7. MCP Server Improvements

### 7.1 Modularization Plan

The 9,140-line `server.py` should be split into modules. Here's the recommended structure:

```
mcp_server/
├── server.py                    # Entry point (~200 lines)
├── config.py                    # Configuration loading
├── tools/
│   ├── __init__.py
│   ├── base.py                  # Base tool class
│   ├── gdrive.py                # Google Drive tools (13 tools)
│   ├── pexels.py                # Pexels tools (4 tools)
│   ├── system.py                # System monitoring tools
│   ├── wordpress.py             # WordPress tools
│   ├── ssh.py                   # Remote server tools
│   ├── git.py                   # Git operations
│   └── files.py                 # File operations
├── lib/
│   ├── __init__.py
│   ├── validation.py            # Input validation
│   ├── resilience.py            # Retry, circuit breaker
│   └── security.py              # Security helpers
└── tests/
    ├── __init__.py
    ├── test_gdrive.py
    ├── test_wordpress.py
    └── conftest.py
```

### 7.2 Server Entry Point Template

Create: `mcp_server/server_modular.py` (template for future refactor)

```python
#!/usr/bin/env python3
"""
MCP Server - Modular Entry Point
Version: 3.0.0
"""

import logging
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Import tool modules
from tools import gdrive, pexels, system, wordpress, ssh, git, files
from lib.validation import validate_all_tools
from lib.resilience import setup_circuit_breakers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize server
mcp = FastMCP("skippy-server")

# Register tool modules
TOOL_MODULES = [
    gdrive,
    pexels,
    system,
    wordpress,
    ssh,
    git,
    files,
]

def register_tools():
    """Register all tools from modules."""
    for module in TOOL_MODULES:
        if hasattr(module, 'register'):
            tools = module.register(mcp)
            logger.info(f"Registered {len(tools)} tools from {module.__name__}")

def main():
    """Main entry point."""
    logger.info("Starting MCP Server v3.0.0")
    
    # Setup
    setup_circuit_breakers()
    register_tools()
    validate_all_tools()
    
    # Run
    mcp.run()

if __name__ == "__main__":
    main()
```

### 7.3 Health Endpoint

Add to MCP server:

```python
@mcp.tool()
def health_check() -> dict:
    """
    Check MCP server health status.
    
    Returns:
        Health status dictionary
    """
    import psutil
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": time.time() - START_TIME,
        "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024,
        "tools_registered": len(mcp.tools),
        "circuit_breakers": get_all_circuit_breaker_states(),
    }
```

---

## 8. Configuration Updates

### 8.1 Updated settings.json

Replace: `$HOME/.claude/settings.json`

```json
{
  "sandbox": {
    "enabled": true,
    "filesystem": {
      "writablePaths": [
        "$PWD",
        "$HOME/skippy/work",
        "$HOME/skippy/development",
        "$HOME/skippy/plugins",
        "$HOME/skippy/documentation",
        "$HOME/skippy/conversations",
        "$HOME/.claude"
      ],
      "readablePaths": [
        "$PWD",
        "$HOME/skippy",
        "$HOME/.claude",
        "$HOME/.config"
      ],
      "deniedPaths": [
        "$HOME/.ssh/id_*",
        "$HOME/.aws/credentials",
        "$HOME/.credentials",
        "$HOME/.gnupg/private*",
        "/etc/shadow",
        "/etc/sudoers",
        "/root"
      ]
    },
    "network": {
      "allowedDomains": [
        "github.com",
        "api.github.com",
        "raw.githubusercontent.com",
        "npmjs.com",
        "registry.npmjs.org",
        "pypi.org",
        "files.pythonhosted.org",
        "rundaverun.org",
        "rundaverun-local-complete-022655.local",
        "pexels.com",
        "api.pexels.com",
        "bp6.0cf.myftpupload.com",
        "localhost",
        "127.0.0.1"
      ],
      "deniedDomains": [],
      "allowUnixSockets": true,
      "allowLocalBinding": true
    },
    "excludedCommands": [
      "docker",
      "sudo",
      "su"
    ],
    "allowUnsandboxedCommands": true,
    "autoAllowBashIfSandboxed": true
  },
  "permissions": {
    "defaultMode": "acceptEdits"
  },
  "hooks": {
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
    ],
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/pre_tool_use.sh",
            "timeout": 5000
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
          },
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/auto_backup.sh",
            "timeout": 3000
          }
        ]
      }
    ],
    "PermissionRequest": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/permission_request.sh",
            "timeout": 2000
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/stop_hook.sh",
            "timeout": 5000
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/subagent_stop.sh",
            "timeout": 5000
          }
        ]
      }
    ]
  },
  "preferences": {
    "autoCompactWarnings": true,
    "preserveSessionState": true,
    "autoLint": true,
    "autoBackup": true
  }
}
```

---

## 9. Implementation Checklist

### Phase 1: Quick Wins (1-2 hours)

- [ ] Run cleanup script to remove 32 empty `resources/` directories
- [ ] Add error handling to all existing hooks (trap pattern)
- [ ] Create `/debug` command
- [ ] Create `/test` command
- [ ] Create `/health` command
- [ ] Update `settings.json` with new configuration

### Phase 2: Skill Consolidation (1-2 hours)

- [ ] Create consolidated `debugging` skill
- [ ] Create consolidated `mcp-operations` skill
- [ ] Create consolidated `backup-recovery` skill
- [ ] Remove old redundant skills
- [ ] Generate skills INDEX.md

### Phase 3: New Capabilities (1-2 hours)

- [ ] Create `/scaffold` command
- [ ] Create `/review` command
- [ ] Create `/explain` command
- [ ] Create `/security-scan` command
- [ ] Create `dev-workflow` skill
- [ ] Create `quick-fixes` skill

### Phase 4: Hook Enhancements (30 min)

- [ ] Create `post_edit_lint.sh` hook
- [ ] Create `dev_context_tracker.sh` hook
- [ ] Create `auto_backup.sh` hook
- [ ] Update `pre_tool_use.sh` with additional security checks
- [ ] Update `settings.json` to register new hooks

### Phase 5: Automation (30 min)

- [ ] Create `daily_maintenance.sh` script
- [ ] Add to crontab: `0 3 * * * $HOME/.claude/scripts/daily_maintenance.sh`
- [ ] Test all automation scripts

### Phase 6: Documentation

- [ ] Update main CLAUDE.md with new features
- [ ] Update README.md
- [ ] Create CHANGELOG.md entry

---

## Verification Commands

After implementation, run these to verify:

```bash
# Check all hooks are executable
ls -la ~/.claude/hooks/*.sh

# Validate settings.json
python3 -m json.tool ~/.claude/settings.json

# Count skills
find ~/.claude/skills -name "SKILL.md" | wc -l

# Count commands
find ~/.claude/commands -name "*.md" | wc -l

# Run health check
~/.claude/commands/health.md full

# Run security scan
~/.claude/commands/security-scan.md quick
```

---

## Notes for Claude Code

1. **Execute in order** - Dependencies exist between phases
2. **Test after each phase** - Verify functionality before proceeding
3. **Backup before changes** - Especially for settings.json and existing hooks
4. **Use session directories** - All work should be in proper session dirs
5. **Document changes** - Update relevant documentation as you go

**Total estimated implementation time: 4-6 hours**

---

*Report generated: 2025-12-01*
*Configuration analyzed: claude_config_export_20251201.zip*
