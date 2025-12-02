#!/bin/bash
# mcp_watchdog_v1.1.0.sh
# Monitor MCP servers and auto-restart on failure
#
# Usage:
#   mcp_watchdog_v1.0.0.sh           # Run once (for cron)
#   mcp_watchdog_v1.0.0.sh --daemon  # Run continuously
#
# Features:
#   - Checks MCP server health
#   - SKIPS recovery if Claude is actively running (interactive session)
#   - Auto-restarts on failure only when Claude is idle
#   - Exponential backoff on repeated failures
#   - Desktop notifications
#   - Incident logging
#
# Cron: */10 * * * * /home/dave/skippy/scripts/monitoring/mcp_watchdog_v1.0.0.sh
#
# Dependencies:
#   - claude (Claude Code CLI)
#   - notify-send (optional, for desktop notifications)
#
# Created: 2025-12-01
# Updated: 2025-12-02 - v1.1.0: Don't kill active Claude sessions

set -euo pipefail

# Configuration
LOG_DIR="/home/dave/skippy/logs/mcp"
LOG_FILE="$LOG_DIR/watchdog.log"
STATE_FILE="$LOG_DIR/watchdog_state.json"
MAX_RETRIES=3
RETRY_DELAY=30
CHECK_TIMEOUT=10

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Logging function
log() {
    local level="$1"
    local message="$2"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $message" >> "$LOG_FILE"
    if [ "$level" = "ERROR" ] || [ "$level" = "WARN" ]; then
        echo "[$level] $message" >&2
    fi
}

# Check if Claude is actively running an interactive session
# Returns 0 if Claude is active (should NOT be killed), 1 if idle/not running
is_claude_active() {
    # Check if claude process exists and is attached to a terminal (pts)
    if pgrep -x "claude" >/dev/null 2>&1; then
        # Get the TTY of the claude process
        local claude_tty
        claude_tty=$(ps -o tty= -p "$(pgrep -x claude | head -1)" 2>/dev/null | tr -d ' ')

        if [ -n "$claude_tty" ] && [ "$claude_tty" != "?" ]; then
            # Claude is running on a terminal - it's interactive
            log "INFO" "Claude is active on $claude_tty - will not interrupt"
            return 0
        fi
    fi

    # No active Claude session
    return 1
}

# Send notification
notify() {
    local title="$1"
    local message="$2"
    local urgency="${3:-normal}"

    # Desktop notification
    if command -v notify-send >/dev/null 2>&1; then
        notify-send -u "$urgency" "$title" "$message" 2>/dev/null || true
    fi

    # Log notification
    log "NOTIFY" "$title: $message"

    # Also use Claude hook if available
    if [ -x "$HOME/.claude/hooks/notification_hook.sh" ]; then
        echo "$message" | "$HOME/.claude/hooks/notification_hook.sh" "$title" 2>/dev/null || true
    fi
}

# Check MCP server health
check_mcp_health() {
    log "INFO" "Checking MCP server health..."

    # If Claude is actively running, skip the health check entirely
    # (claude mcp list will fail while Claude is in use)
    if is_claude_active; then
        log "INFO" "Claude is active - assuming MCP healthy (skipping check)"
        return 0
    fi

    # Try to list MCP servers with timeout
    if timeout "$CHECK_TIMEOUT" claude mcp list >/dev/null 2>&1; then
        log "INFO" "MCP servers healthy"
        return 0
    else
        log "WARN" "MCP health check failed"
        return 1
    fi
}

# Get failure count from state file
get_failure_count() {
    if [ -f "$STATE_FILE" ]; then
        grep -o '"failure_count":[0-9]*' "$STATE_FILE" 2>/dev/null | grep -o '[0-9]*' || echo 0
    else
        echo 0
    fi
}

# Update state file
update_state() {
    local failure_count="$1"
    local last_failure="${2:-}"
    local last_recovery="${3:-}"

    cat > "$STATE_FILE" << EOF
{
    "failure_count": $failure_count,
    "last_check": "$(date -Iseconds)",
    "last_failure": "$last_failure",
    "last_recovery": "$last_recovery"
}
EOF
}

# Attempt recovery
attempt_recovery() {
    local attempt="$1"
    log "WARN" "Recovery attempt $attempt of $MAX_RETRIES"

    case $attempt in
        1)
            # Attempt 1: Just wait and recheck (transient issue)
            log "INFO" "Waiting ${RETRY_DELAY}s for transient issue..."
            sleep "$RETRY_DELAY"
            ;;
        2)
            # Attempt 2: Restart Claude Code (if NOT actively in use)
            if is_claude_active; then
                log "INFO" "Claude is active - skipping restart (user is working)"
                # Just wait and hope it recovers
                sleep "$RETRY_DELAY"
            else
                log "INFO" "Attempting to restart Claude Code..."
                pkill -f "claude" 2>/dev/null || true
                sleep 5
                # Claude will auto-start MCP servers on next invocation
            fi
            ;;
        3)
            # Attempt 3: Full restart of MCP server process
            log "INFO" "Attempting full MCP server restart..."

            # Kill any running MCP server processes
            pkill -f "mcp-servers" 2>/dev/null || true
            pkill -f "general-server" 2>/dev/null || true

            sleep 5

            # Try to restart the server directly
            MCP_SERVER_PATH="/home/dave/skippy/mcp-servers/general-server"
            if [ -d "$MCP_SERVER_PATH" ]; then
                cd "$MCP_SERVER_PATH"
                if [ -f ".venv/bin/activate" ]; then
                    source .venv/bin/activate
                    nohup python server.py > "$LOG_DIR/server_restart.log" 2>&1 &
                    log "INFO" "MCP server restarted with PID $!"
                fi
            fi

            sleep 10
            ;;
    esac

    # Check if recovery worked
    if check_mcp_health; then
        return 0
    else
        return 1
    fi
}

# Main watchdog logic
main() {
    log "INFO" "=== MCP Watchdog Check Started ==="

    # Check health
    if check_mcp_health; then
        # All good - reset failure count
        update_state 0 "" ""
        log "INFO" "=== Check Complete: HEALTHY ==="
        exit 0
    fi

    # Health check failed - attempt recovery
    FAILURE_COUNT=$(get_failure_count)
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
    update_state "$FAILURE_COUNT" "$(date -Iseconds)" ""

    log "ERROR" "MCP server unhealthy (failure #$FAILURE_COUNT)"

    # Notify on first failure
    if [ "$FAILURE_COUNT" -eq 1 ]; then
        notify "MCP Server Issue" "MCP servers not responding. Attempting recovery..." "normal"
    fi

    # Attempt recovery with exponential backoff
    for attempt in $(seq 1 $MAX_RETRIES); do
        if attempt_recovery "$attempt"; then
            # Recovery successful
            update_state 0 "" "$(date -Iseconds)"
            notify "MCP Recovered" "MCP servers recovered after $attempt attempt(s)" "normal"
            log "INFO" "=== Check Complete: RECOVERED ==="
            exit 0
        fi

        # Exponential backoff between retries
        if [ "$attempt" -lt "$MAX_RETRIES" ]; then
            BACKOFF=$((RETRY_DELAY * attempt))
            log "INFO" "Waiting ${BACKOFF}s before next attempt..."
            sleep "$BACKOFF"
        fi
    done

    # All recovery attempts failed
    log "ERROR" "All recovery attempts failed"
    notify "MCP Server Down" "MCP servers failed after $MAX_RETRIES recovery attempts. Manual intervention required." "critical"

    # Create incident report
    INCIDENT_FILE="$LOG_DIR/incident_$(date +%Y%m%d_%H%M%S).md"
    cat > "$INCIDENT_FILE" << EOF
# MCP Server Incident Report

**Date:** $(date '+%Y-%m-%d %H:%M:%S')
**Status:** UNRESOLVED
**Consecutive Failures:** $FAILURE_COUNT

## Timeline

- First failure: $(grep -o '"last_failure":"[^"]*"' "$STATE_FILE" 2>/dev/null | cut -d'"' -f4 || echo "unknown")
- Recovery attempts: $MAX_RETRIES
- All attempts failed

## Diagnostics

### Process Status
\`\`\`
$(ps aux | grep -E "claude|mcp" | grep -v grep || echo "No relevant processes found")
\`\`\`

### Recent Logs
\`\`\`
$(tail -20 "$LOG_FILE" 2>/dev/null || echo "No logs available")
\`\`\`

### Claude Logs
\`\`\`
$(tail -20 ~/.claude/logs/*.log 2>/dev/null | head -30 || echo "No Claude logs available")
\`\`\`

## Recommended Actions

1. Check if Claude Code is running
2. Verify MCP server configuration in ~/.claude/settings.json
3. Check network connectivity
4. Restart Claude Code manually
5. Check MCP server logs in $LOG_DIR/

## Manual Recovery

\`\`\`bash
# Restart Claude Code
pkill -f claude
claude

# Or restart MCP server directly
cd /home/dave/skippy/mcp-servers/general-server
source .venv/bin/activate
python server.py
\`\`\`
EOF

    log "ERROR" "Incident report created: $INCIDENT_FILE"
    log "ERROR" "=== Check Complete: FAILED ==="

    exit 1
}

# Daemon mode (continuous monitoring)
daemon_mode() {
    log "INFO" "Starting MCP Watchdog in daemon mode"
    notify "MCP Watchdog" "Watchdog daemon started" "low"

    while true; do
        main || true  # Don't exit on failure
        sleep 600  # Check every 10 minutes
    done
}

# Parse arguments
if [ "${1:-}" = "--daemon" ]; then
    daemon_mode
else
    main
fi
