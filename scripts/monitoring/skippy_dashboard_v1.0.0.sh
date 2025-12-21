#!/bin/bash
# Skippy System Dashboard v1.0.0
# Real-time monitoring dashboard for Skippy infrastructure
#
# Usage:
#   bash skippy_dashboard_v1.0.0.sh [--json|--html]
#
# Features:
#   - System health overview
#   - Service status
#   - Recent backup status
#   - MCP server connectivity
#   - WordPress site health
#   - Resource usage
#
# Created: 2025-12-21

VERSION="1.0.0"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# Configuration
SKIPPY_PATH="${SKIPPY_PATH:-/home/dave/skippy}"
WP_PATH="${WORDPRESS_PATH:-/home/dave/skippy/websites/rundaverun/local_site/rundaverun_local_site/app/public}"
BACKUP_DIR="$SKIPPY_PATH/backups"

# Output format
OUTPUT_FORMAT="terminal"
case "$1" in
    --json) OUTPUT_FORMAT="json" ;;
    --html) OUTPUT_FORMAT="html" ;;
esac

# Helper functions
check_pass() { echo -e "${GREEN}✓${NC}"; }
check_fail() { echo -e "${RED}✗${NC}"; }
check_warn() { echo -e "${YELLOW}⚠${NC}"; }

# Collect data
collect_data() {
    local data="{}"

    # System info
    HOSTNAME=$(hostname)
    UPTIME=$(uptime -p 2>/dev/null || uptime | awk -F'up' '{print $2}' | awk -F',' '{print $1}')
    LOAD=$(cat /proc/loadavg | awk '{print $1, $2, $3}')

    # Disk usage
    DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | tr -d '%')
    DISK_TOTAL=$(df -h / | tail -1 | awk '{print $2}')
    DISK_USED=$(df -h / | tail -1 | awk '{print $3}')

    # Memory
    MEM_TOTAL=$(free -h | awk '/^Mem:/ {print $2}')
    MEM_USED=$(free -h | awk '/^Mem:/ {print $3}')
    MEM_PERCENT=$(free | awk '/^Mem:/ {printf("%.0f", $3/$2 * 100)}')

    # CPU
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print 100 - $8}' | cut -d. -f1)

    # Backup status
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/wordpress/*/db_backup_*.sql.gz 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        BACKUP_DATE=$(stat -c %Y "$LATEST_BACKUP" 2>/dev/null)
        BACKUP_AGE_HOURS=$(( ($(date +%s) - BACKUP_DATE) / 3600 ))
        BACKUP_STATUS="OK"
        [ $BACKUP_AGE_HOURS -gt 48 ] && BACKUP_STATUS="STALE"
    else
        BACKUP_STATUS="MISSING"
        BACKUP_AGE_HOURS="-"
    fi

    # WordPress health
    WP_STATUS="UNKNOWN"
    if [ -d "$WP_PATH" ]; then
        if wp --path="$WP_PATH" --allow-root core is-installed 2>/dev/null; then
            WP_STATUS="OK"
            WP_VERSION=$(wp --path="$WP_PATH" --allow-root core version 2>/dev/null)
        else
            WP_STATUS="ERROR"
        fi
    fi

    # MCP status (check if processes running)
    MCP_GENERAL=$(pgrep -f "general-server" > /dev/null && echo "OK" || echo "DOWN")

    # Git status
    GIT_BRANCH=$(cd "$SKIPPY_PATH" && git branch --show-current 2>/dev/null || echo "unknown")
    GIT_CLEAN=$(cd "$SKIPPY_PATH" && git status --porcelain 2>/dev/null | wc -l)
    [ "$GIT_CLEAN" = "0" ] && GIT_STATUS="clean" || GIT_STATUS="$GIT_CLEAN changes"

    # Services check (basic)
    CRON_RUNNING=$(pgrep cron > /dev/null && echo "OK" || echo "DOWN")

    # Recent errors in logs
    ERROR_COUNT=$(grep -c "ERROR\|FAIL" "$SKIPPY_PATH/logs/"*.log 2>/dev/null | awk -F: '{sum+=$2} END {print sum+0}')
}

# Terminal output
print_terminal() {
    clear
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}              SKIPPY SYSTEM DASHBOARD v$VERSION${NC}"
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BOLD}📊 System Status${NC}  ($(date '+%Y-%m-%d %H:%M:%S'))"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # System Overview
    echo -e "${BOLD}🖥️  System Overview${NC}"
    echo -e "   Host:     $HOSTNAME"
    echo -e "   Uptime:   $UPTIME"
    echo -e "   Load:     $LOAD"
    echo ""

    # Resources
    echo -e "${BOLD}📈 Resources${NC}"
    if [ "$CPU_USAGE" -lt 70 ]; then
        echo -e "   CPU:      $(check_pass) ${CPU_USAGE}%"
    elif [ "$CPU_USAGE" -lt 90 ]; then
        echo -e "   CPU:      $(check_warn) ${CPU_USAGE}%"
    else
        echo -e "   CPU:      $(check_fail) ${CPU_USAGE}% (High!)"
    fi

    if [ "$MEM_PERCENT" -lt 80 ]; then
        echo -e "   Memory:   $(check_pass) ${MEM_USED}/${MEM_TOTAL} (${MEM_PERCENT}%)"
    else
        echo -e "   Memory:   $(check_warn) ${MEM_USED}/${MEM_TOTAL} (${MEM_PERCENT}%)"
    fi

    if [ "$DISK_USAGE" -lt 80 ]; then
        echo -e "   Disk:     $(check_pass) ${DISK_USED}/${DISK_TOTAL} (${DISK_USAGE}%)"
    elif [ "$DISK_USAGE" -lt 90 ]; then
        echo -e "   Disk:     $(check_warn) ${DISK_USED}/${DISK_TOTAL} (${DISK_USAGE}%)"
    else
        echo -e "   Disk:     $(check_fail) ${DISK_USED}/${DISK_TOTAL} (${DISK_USAGE}% Critical!)"
    fi
    echo ""

    # Services
    echo -e "${BOLD}🔧 Services${NC}"
    [ "$CRON_RUNNING" = "OK" ] && echo -e "   Cron:     $(check_pass) Running" || echo -e "   Cron:     $(check_fail) Not Running"
    [ "$MCP_GENERAL" = "OK" ] && echo -e "   MCP:      $(check_pass) Connected" || echo -e "   MCP:      $(check_warn) Not detected (may be normal)"
    echo ""

    # WordPress
    echo -e "${BOLD}🌐 WordPress${NC}"
    case "$WP_STATUS" in
        OK)    echo -e "   Status:   $(check_pass) Running (v$WP_VERSION)" ;;
        ERROR) echo -e "   Status:   $(check_fail) Error detected" ;;
        *)     echo -e "   Status:   $(check_warn) Unknown" ;;
    esac
    echo ""

    # Backups
    echo -e "${BOLD}💾 Backups${NC}"
    case "$BACKUP_STATUS" in
        OK)      echo -e "   Latest:   $(check_pass) ${BACKUP_AGE_HOURS} hours ago" ;;
        STALE)   echo -e "   Latest:   $(check_warn) ${BACKUP_AGE_HOURS} hours ago (Stale!)" ;;
        MISSING) echo -e "   Latest:   $(check_fail) No backups found" ;;
    esac
    echo ""

    # Git
    echo -e "${BOLD}📝 Repository${NC}"
    echo -e "   Branch:   $GIT_BRANCH"
    [ "$GIT_STATUS" = "clean" ] && echo -e "   Status:   $(check_pass) Clean" || echo -e "   Status:   $(check_warn) $GIT_STATUS"
    echo ""

    # Errors
    echo -e "${BOLD}⚠️  Recent Issues${NC}"
    if [ "$ERROR_COUNT" -eq 0 ]; then
        echo -e "   Errors:   $(check_pass) None in logs"
    else
        echo -e "   Errors:   $(check_warn) $ERROR_COUNT error(s) in logs"
    fi
    echo ""

    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "Run '/status' slash command for quick check"
    echo ""
}

# JSON output
print_json() {
    cat <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "version": "$VERSION",
  "system": {
    "hostname": "$HOSTNAME",
    "uptime": "$UPTIME",
    "load": "$LOAD"
  },
  "resources": {
    "cpu_percent": $CPU_USAGE,
    "memory": {
      "used": "$MEM_USED",
      "total": "$MEM_TOTAL",
      "percent": $MEM_PERCENT
    },
    "disk": {
      "used": "$DISK_USED",
      "total": "$DISK_TOTAL",
      "percent": $DISK_USAGE
    }
  },
  "services": {
    "cron": "$CRON_RUNNING",
    "mcp": "$MCP_GENERAL"
  },
  "wordpress": {
    "status": "$WP_STATUS",
    "version": "${WP_VERSION:-unknown}"
  },
  "backup": {
    "status": "$BACKUP_STATUS",
    "age_hours": ${BACKUP_AGE_HOURS:-null}
  },
  "git": {
    "branch": "$GIT_BRANCH",
    "status": "$GIT_STATUS"
  },
  "errors_in_logs": $ERROR_COUNT
}
EOF
}

# Main
collect_data

case "$OUTPUT_FORMAT" in
    json) print_json ;;
    html) echo "HTML output not yet implemented" ;;
    *)    print_terminal ;;
esac

exit 0
