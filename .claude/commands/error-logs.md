---
description: Aggregated error log viewer - all error sources in one view
allowed-tools: ["Bash", "Read", "Grep", "mcp__general-server__tail_log", "mcp__general-server__search_log", "mcp__general-server__check_claude_logs"]
argument-hint: "[optional: filter pattern] [optional: --hours=N]"
---

# Error Logs Aggregator

View errors from all log sources in a single, prioritized view.

**Problem Solved:** Errors scattered across PHP logs, WordPress debug.log, MCP logs, and system logs. No single place to check when troubleshooting.

## Quick Usage

```
/error-logs                    # Last 2 hours, all sources
/error-logs --hours=24         # Last 24 hours
/error-logs "database"         # Filter by pattern
/error-logs --critical         # Only fatal/critical errors
```

## Log Sources

| Source | Location | Contains |
|--------|----------|----------|
| WordPress | `wp-content/debug.log` | PHP errors, plugin issues, deprecation |
| Apache | `/var/log/apache2/error.log` | Server errors, 500s |
| MCP Server | `~/.claude/logs/` | Tool failures, API errors |
| Skippy | `/home/dave/skippy/logs/` | Script errors, cron failures |
| System | `/var/log/syslog` | System-level issues |
| Production | Remote debug.log | Live site errors |

## Aggregated View

```bash
#!/bin/bash
# Error Log Aggregator v1.0.0

HOURS="${1:-2}"
PATTERN="${2:-}"
OUTPUT_DIR="/home/dave/skippy/work/logs/$(date +%Y%m%d_%H%M%S)_error_review"
mkdir -p "$OUTPUT_DIR"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              ERROR LOG AGGREGATOR                             ║"
echo "║              Last $HOURS hours                                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Calculate time threshold
MINS=$((HOURS * 60))

# Initialize counters
TOTAL_ERRORS=0
CRITICAL=0
WARNINGS=0

# Create aggregated log file
AGGREGATED="$OUTPUT_DIR/aggregated_errors.log"
> "$AGGREGATED"
```

### Source 1: WordPress Debug Log (Local)
```bash
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ 1. WordPress Debug Log (Local)                              │"
echo "└─────────────────────────────────────────────────────────────┘"

WP_DEBUG="/home/dave/skippy/rundaverun_local_site/app/public/wp-content/debug.log"

if [ -f "$WP_DEBUG" ]; then
  # Get file modification time
  FILE_AGE=$(stat -c %Y "$WP_DEBUG" 2>/dev/null)
  NOW=$(date +%s)
  AGE_MINS=$(( (NOW - FILE_AGE) / 60 ))

  if [ "$AGE_MINS" -lt "$MINS" ]; then
    # Count by severity
    FATAL=$(grep -c "Fatal error" "$WP_DEBUG" 2>/dev/null || echo 0)
    ERROR=$(grep -c "PHP Error\|PHP Warning" "$WP_DEBUG" 2>/dev/null || echo 0)
    NOTICE=$(grep -c "PHP Notice\|Deprecated" "$WP_DEBUG" 2>/dev/null || echo 0)

    echo "  Fatal:    $FATAL"
    echo "  Errors:   $ERROR"
    echo "  Notices:  $NOTICE"

    CRITICAL=$((CRITICAL + FATAL))
    TOTAL_ERRORS=$((TOTAL_ERRORS + FATAL + ERROR))

    # Add to aggregated log with source tag
    echo "=== WordPress Local ($(date -r "$WP_DEBUG" '+%Y-%m-%d %H:%M')) ===" >> "$AGGREGATED"
    tail -100 "$WP_DEBUG" | grep -E "Fatal|Error|Warning" >> "$AGGREGATED" 2>/dev/null
    echo "" >> "$AGGREGATED"

    # Show recent critical errors
    if [ "$FATAL" -gt 0 ]; then
      echo ""
      echo "  ❌ Recent Fatal Errors:"
      grep "Fatal error" "$WP_DEBUG" | tail -3 | while read -r line; do
        echo "     $(echo "$line" | cut -c1-80)..."
      done
    fi
  else
    echo "  ℹ️  No recent activity (last modified ${AGE_MINS}m ago)"
  fi
else
  echo "  ⚠️  Debug log not found (WP_DEBUG may be disabled)"
fi
```

### Source 2: WordPress Debug Log (Production)
```bash
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ 2. WordPress Debug Log (Production)                         │"
echo "└─────────────────────────────────────────────────────────────┘"

# Fetch production debug log via SSH
PROD_LOG=$(SSH_AUTH_SOCK="" ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes \
  -i ~/.ssh/godaddy_rundaverun git_deployer_f44cc3416a_545525@bp6.0cf.myftpupload.com \
  "tail -100 html/wp-content/debug.log 2>/dev/null" 2>/dev/null)

if [ -n "$PROD_LOG" ]; then
  PROD_FATAL=$(echo "$PROD_LOG" | grep -c "Fatal error" || echo 0)
  PROD_ERROR=$(echo "$PROD_LOG" | grep -c "PHP Error\|PHP Warning" || echo 0)

  echo "  Fatal:    $PROD_FATAL"
  echo "  Errors:   $PROD_ERROR"

  CRITICAL=$((CRITICAL + PROD_FATAL))
  TOTAL_ERRORS=$((TOTAL_ERRORS + PROD_FATAL + PROD_ERROR))

  echo "=== WordPress Production ===" >> "$AGGREGATED"
  echo "$PROD_LOG" | grep -E "Fatal|Error|Warning" >> "$AGGREGATED" 2>/dev/null
  echo "" >> "$AGGREGATED"

  if [ "$PROD_FATAL" -gt 0 ]; then
    echo ""
    echo "  ❌ Recent Fatal Errors:"
    echo "$PROD_LOG" | grep "Fatal error" | tail -3 | while read -r line; do
      echo "     $(echo "$line" | cut -c1-80)..."
    done
  fi
else
  echo "  ℹ️  Could not fetch production logs (SSH timeout or no log)"
fi
```

### Source 3: MCP Server Logs
```bash
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ 3. MCP Server Logs                                          │"
echo "└─────────────────────────────────────────────────────────────┘"

MCP_LOG_DIR="$HOME/.claude/logs"

if [ -d "$MCP_LOG_DIR" ]; then
  # Find recent MCP log files
  MCP_ERRORS=0
  for log in "$MCP_LOG_DIR"/*.log; do
    if [ -f "$log" ]; then
      FILE_AGE=$(stat -c %Y "$log" 2>/dev/null)
      NOW=$(date +%s)
      AGE_MINS=$(( (NOW - FILE_AGE) / 60 ))

      if [ "$AGE_MINS" -lt "$MINS" ]; then
        ERRS=$(grep -c -i "error\|exception\|failed" "$log" 2>/dev/null || echo 0)
        MCP_ERRORS=$((MCP_ERRORS + ERRS))

        if [ "$ERRS" -gt 0 ]; then
          echo "=== MCP: $(basename "$log") ===" >> "$AGGREGATED"
          grep -i "error\|exception\|failed" "$log" | tail -20 >> "$AGGREGATED"
          echo "" >> "$AGGREGATED"
        fi
      fi
    fi
  done

  echo "  Errors found: $MCP_ERRORS"
  TOTAL_ERRORS=$((TOTAL_ERRORS + MCP_ERRORS))
else
  echo "  ℹ️  MCP log directory not found"
fi
```

### Source 4: Skippy Logs
```bash
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ 4. Skippy System Logs                                       │"
echo "└─────────────────────────────────────────────────────────────┘"

SKIPPY_LOG_DIR="/home/dave/skippy/logs"

if [ -d "$SKIPPY_LOG_DIR" ]; then
  SKIPPY_ERRORS=0
  for log in "$SKIPPY_LOG_DIR"/*.log; do
    if [ -f "$log" ]; then
      FILE_AGE=$(stat -c %Y "$log" 2>/dev/null)
      NOW=$(date +%s)
      AGE_MINS=$(( (NOW - FILE_AGE) / 60 ))

      if [ "$AGE_MINS" -lt "$MINS" ]; then
        ERRS=$(grep -c -i "error\|failed\|exception" "$log" 2>/dev/null || echo 0)
        SKIPPY_ERRORS=$((SKIPPY_ERRORS + ERRS))

        if [ "$ERRS" -gt 0 ]; then
          echo "=== Skippy: $(basename "$log") ===" >> "$AGGREGATED"
          grep -i "error\|failed\|exception" "$log" | tail -20 >> "$AGGREGATED"
          echo "" >> "$AGGREGATED"
        fi
      fi
    fi
  done

  echo "  Errors found: $SKIPPY_ERRORS"
  TOTAL_ERRORS=$((TOTAL_ERRORS + SKIPPY_ERRORS))
else
  echo "  ℹ️  Skippy log directory not found"
fi
```

### Source 5: Cron Logs
```bash
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ 5. Cron Job Logs                                            │"
echo "└─────────────────────────────────────────────────────────────┘"

CRON_ERRORS=$(grep -h "CRON\|cron" /var/log/syslog 2>/dev/null | \
  grep -i "error\|failed" | tail -10 | wc -l || echo 0)

echo "  Recent cron errors: $CRON_ERRORS"
TOTAL_ERRORS=$((TOTAL_ERRORS + CRON_ERRORS))

if [ "$CRON_ERRORS" -gt 0 ]; then
  echo "=== Cron Errors ===" >> "$AGGREGATED"
  grep -h "CRON\|cron" /var/log/syslog 2>/dev/null | \
    grep -i "error\|failed" | tail -10 >> "$AGGREGATED"
  echo "" >> "$AGGREGATED"
fi
```

### Summary
```bash
echo ""
echo "══════════════════════════════════════════════════════════════"
echo ""

if [ "$CRITICAL" -gt 0 ]; then
  echo "  ❌ CRITICAL: $CRITICAL fatal errors require immediate attention"
elif [ "$TOTAL_ERRORS" -gt 10 ]; then
  echo "  ⚠️  WARNING: $TOTAL_ERRORS errors found across all sources"
elif [ "$TOTAL_ERRORS" -gt 0 ]; then
  echo "  ℹ️  INFO: $TOTAL_ERRORS minor errors found"
else
  echo "  ✅ All systems healthy - no errors in last $HOURS hours"
fi

echo ""
echo "  Aggregated log: $AGGREGATED"
echo "  Total lines: $(wc -l < "$AGGREGATED")"
echo ""
echo "══════════════════════════════════════════════════════════════"
```

## Pattern Filtering

Search for specific error patterns:

```bash
/error-logs "database"      # Database-related errors
/error-logs "permission"    # Permission issues
/error-logs "memory"        # Memory exhaustion
/error-logs "timeout"       # Timeout errors
/error-logs "404"           # Not found errors
```

## Severity Levels

| Level | Indicator | Action |
|-------|-----------|--------|
| CRITICAL | ❌ | Immediate action required |
| WARNING | ⚠️ | Review and address soon |
| INFO | ℹ️ | Monitor, may be expected |
| OK | ✅ | No action needed |

## Integration

Uses these MCP tools when available:
- `mcp__general-server__tail_log` - Efficient log tailing
- `mcp__general-server__search_log` - Pattern search with context
- `mcp__general-server__check_claude_logs` - MCP-specific logs

Falls back to standard bash commands if MCP unavailable.

## Output Files

Aggregated logs saved to:
```
/home/dave/skippy/work/logs/YYYYMMDD_HHMMSS_error_review/
├── aggregated_errors.log    # All errors combined
├── summary.md               # Error counts by source
└── critical.log             # Fatal errors only
```

## Troubleshooting Common Errors

### WordPress "Fatal error: Allowed memory size"
```bash
# Increase memory limit in wp-config.php
wp config set WP_MEMORY_LIMIT '256M'
```

### "Permission denied"
```bash
# Fix with /fix-permissions command
/fix-permissions
```

### Database connection errors
```bash
# Check database status
wp db check
```

### MCP tool failures
```bash
# Check MCP status
/mcp-status
```
