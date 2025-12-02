#!/bin/bash
# Claude Code Crash Monitor v1.0.0
# Monitors for Claude Code crashes and logs diagnostic info
#
# Usage:
#   ./claude_crash_monitor_v1.0.0.sh [--daemon]
#
# Features:
#   - Monitors Claude Code process
#   - Logs MCP server status on crash detection
#   - Captures system state (memory, CPU, network)
#   - Writes crash reports to ~/skippy/logs/claude_crashes/
#
# Dependencies:
#   - pgrep, ps, free, netstat/ss
#
# Created: 2025-12-01

set -euo pipefail

LOG_DIR="/home/dave/skippy/logs/claude_crashes"
MONITOR_LOG="$LOG_DIR/monitor.log"
CHECK_INTERVAL=10  # seconds

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$MONITOR_LOG"
}

check_claude_process() {
    pgrep -f "claude" >/dev/null 2>&1
}

check_mcp_servers() {
    local mcp_status=""

    # Check each MCP server type
    for server in "general-server" "mcp-server-memory" "mcp-server-sequential" "mcp-server-puppeteer" "mcp-server-github" "mcp-server-brave" "chrome-devtools-mcp" "mcp-server-filesystem" "mcp-server-postgres"; do
        if pgrep -f "$server" >/dev/null 2>&1; then
            mcp_status+="  ✅ $server\n"
        else
            mcp_status+="  ❌ $server (DOWN)\n"
        fi
    done

    echo -e "$mcp_status"
}

capture_crash_report() {
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local report_file="$LOG_DIR/crash_${timestamp}.md"

    cat > "$report_file" <<EOF
# Claude Code Crash Report
**Timestamp:** $(date)
**Report ID:** $timestamp

## System State

### Memory
\`\`\`
$(free -h)
\`\`\`

### CPU Load
\`\`\`
$(uptime)
\`\`\`

### MCP Server Status
\`\`\`
$(check_mcp_servers)
\`\`\`

### Recent Processes (claude/mcp related)
\`\`\`
$(ps aux | grep -E "claude|mcp|node.*server" | grep -v grep | head -20)
\`\`\`

### Network Connections (node/python)
\`\`\`
$(ss -tunp 2>/dev/null | grep -E "node|python" | head -20 || echo "No connections found")
\`\`\`

### Recent System Errors (last 5 min)
\`\`\`
$(journalctl --since "5 minutes ago" 2>/dev/null | grep -iE "error|fail|kill|oom" | tail -20 || echo "No recent errors")
\`\`\`

### Disk Space
\`\`\`
$(df -h / /home 2>/dev/null)
\`\`\`

## Notes
- Check if MCP servers show ❌ - may indicate cascade failure
- Review memory usage for potential OOM
- Network issues may indicate API timeout

EOF

    log "Crash report saved: $report_file"
    echo "$report_file"
}

# Daemon mode - continuous monitoring
daemon_mode() {
    log "Starting Claude Code crash monitor (daemon mode)"
    log "Check interval: ${CHECK_INTERVAL}s"
    log "Log directory: $LOG_DIR"

    local was_running=false

    while true; do
        if check_claude_process; then
            if [ "$was_running" = false ]; then
                log "Claude Code process detected - monitoring active"
                was_running=true
            fi
        else
            if [ "$was_running" = true ]; then
                log "⚠️  Claude Code process STOPPED - possible crash!"
                capture_crash_report
                was_running=false
            fi
        fi

        sleep "$CHECK_INTERVAL"
    done
}

# One-shot status check
status_check() {
    echo "=== Claude Code Status Check ==="
    echo "Timestamp: $(date)"
    echo ""

    echo "Claude Process:"
    if check_claude_process; then
        echo "  ✅ Running"
        ps aux | grep -E "[c]laude" | head -5
    else
        echo "  ❌ Not running"
    fi
    echo ""

    echo "MCP Servers:"
    check_mcp_servers
    echo ""

    echo "Memory:"
    free -h | head -2
    echo ""

    echo "Recent crash reports:"
    ls -lt "$LOG_DIR"/crash_*.md 2>/dev/null | head -5 || echo "  No crash reports found"
}

# Main
case "${1:-status}" in
    --daemon|-d)
        daemon_mode
        ;;
    --status|-s|status)
        status_check
        ;;
    --report|-r)
        capture_crash_report
        ;;
    --help|-h)
        echo "Usage: $0 [--daemon|--status|--report|--help]"
        echo ""
        echo "Options:"
        echo "  --daemon, -d   Run in daemon mode (continuous monitoring)"
        echo "  --status, -s   One-shot status check (default)"
        echo "  --report, -r   Generate crash report now"
        echo "  --help, -h     Show this help"
        ;;
    *)
        status_check
        ;;
esac
