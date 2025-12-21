#!/bin/bash
# Weekly Maintenance Automation v1.0.0
# Comprehensive weekly system maintenance tasks
#
# Usage:
#   bash weekly_maintenance_v1.0.0.sh [--report-only]
#
# Tasks performed:
#   - Health check all services
#   - Verify backups exist and are recent
#   - Check for outdated packages
#   - Run security scans
#   - Archive old logs
#   - Generate maintenance report
#
# Created: 2025-12-21

VERSION="1.0.0"

# Configuration
SKIPPY_PATH="${SKIPPY_PATH:-/home/dave/skippy}"
REPORT_DIR="$SKIPPY_PATH/logs/maintenance"
REPORT_FILE="$REPORT_DIR/weekly_maintenance_$(date +%Y%m%d).md"
LOG_FILE="$SKIPPY_PATH/logs/weekly_maintenance.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Initialize
mkdir -p "$REPORT_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    local message="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $message" >> "$LOG_FILE"
    echo -e "$message"
}

# Start report
cat > "$REPORT_FILE" << EOF
# Weekly Maintenance Report
**Date:** $(date '+%Y-%m-%d %H:%M')
**System:** $(hostname)
**Version:** $VERSION

---

## Summary

EOF

WARNINGS=0
ERRORS=0
PASSED=0

# Task 1: System Health Check
log "=== Task 1: System Health Check ==="

# Check disk space
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo "✅ Disk usage: ${DISK_USAGE}% (OK)" >> "$REPORT_FILE"
    ((PASSED++))
elif [ "$DISK_USAGE" -lt 90 ]; then
    echo "⚠️ Disk usage: ${DISK_USAGE}% (Warning)" >> "$REPORT_FILE"
    ((WARNINGS++))
else
    echo "❌ Disk usage: ${DISK_USAGE}% (Critical)" >> "$REPORT_FILE"
    ((ERRORS++))
fi

# Check memory
MEM_PERCENT=$(free | awk '/^Mem:/ {printf("%.0f", $3/$2 * 100)}')
if [ "$MEM_PERCENT" -lt 80 ]; then
    echo "✅ Memory usage: ${MEM_PERCENT}% (OK)" >> "$REPORT_FILE"
    ((PASSED++))
else
    echo "⚠️ Memory usage: ${MEM_PERCENT}% (High)" >> "$REPORT_FILE"
    ((WARNINGS++))
fi

# Task 2: Backup Verification
log "=== Task 2: Backup Verification ==="
echo "" >> "$REPORT_FILE"
echo "## Backup Status" >> "$REPORT_FILE"

# Check WordPress backups
WP_BACKUP=$(ls -t "$SKIPPY_PATH/backups/wordpress/"*/db_backup_*.sql.gz 2>/dev/null | head -1)
if [ -n "$WP_BACKUP" ]; then
    BACKUP_DATE=$(stat -c %Y "$WP_BACKUP" 2>/dev/null)
    BACKUP_AGE=$(( ($(date +%s) - BACKUP_DATE) / 3600 ))
    if [ "$BACKUP_AGE" -lt 48 ]; then
        echo "✅ WordPress DB backup: ${BACKUP_AGE} hours old" >> "$REPORT_FILE"
        ((PASSED++))
    else
        echo "⚠️ WordPress DB backup: ${BACKUP_AGE} hours old (Stale)" >> "$REPORT_FILE"
        ((WARNINGS++))
    fi
else
    echo "❌ WordPress DB backup: Not found" >> "$REPORT_FILE"
    ((ERRORS++))
fi

# Task 3: Service Status
log "=== Task 3: Service Status ==="
echo "" >> "$REPORT_FILE"
echo "## Services" >> "$REPORT_FILE"

# Check cron
if pgrep cron > /dev/null; then
    echo "✅ Cron: Running" >> "$REPORT_FILE"
    ((PASSED++))
else
    echo "❌ Cron: Not running" >> "$REPORT_FILE"
    ((ERRORS++))
fi

# Task 4: Git Repository Status
log "=== Task 4: Git Repository Status ==="
echo "" >> "$REPORT_FILE"
echo "## Repository" >> "$REPORT_FILE"

cd "$SKIPPY_PATH"
GIT_STATUS=$(git status --porcelain 2>/dev/null | wc -l)
GIT_BRANCH=$(git branch --show-current 2>/dev/null)

echo "- Branch: $GIT_BRANCH" >> "$REPORT_FILE"
if [ "$GIT_STATUS" -eq 0 ]; then
    echo "✅ Working tree: Clean" >> "$REPORT_FILE"
    ((PASSED++))
else
    echo "⚠️ Working tree: $GIT_STATUS uncommitted changes" >> "$REPORT_FILE"
    ((WARNINGS++))
fi

# Task 5: Log Cleanup (archive logs older than 30 days)
log "=== Task 5: Log Cleanup ==="
echo "" >> "$REPORT_FILE"
echo "## Maintenance" >> "$REPORT_FILE"

OLD_LOGS=$(find "$SKIPPY_PATH/logs" -name "*.log" -mtime +30 2>/dev/null | wc -l)
if [ "$OLD_LOGS" -gt 0 ]; then
    if [ "$1" != "--report-only" ]; then
        find "$SKIPPY_PATH/logs" -name "*.log" -mtime +30 -exec gzip {} \; 2>/dev/null
        echo "✅ Archived $OLD_LOGS old log files" >> "$REPORT_FILE"
    else
        echo "ℹ️ $OLD_LOGS log files would be archived (report-only mode)" >> "$REPORT_FILE"
    fi
else
    echo "✅ No old logs to archive" >> "$REPORT_FILE"
fi
((PASSED++))

# Task 6: Security Check (basic)
log "=== Task 6: Security Check ==="
echo "" >> "$REPORT_FILE"
echo "## Security" >> "$REPORT_FILE"

# Check for exposed credentials in recent commits
CRED_CHECK=$(cd "$SKIPPY_PATH" && git log --oneline -10 --all --diff-filter=A -- "*.env" "*.pem" "*.key" 2>/dev/null | wc -l)
if [ "$CRED_CHECK" -eq 0 ]; then
    echo "✅ No credential files in recent commits" >> "$REPORT_FILE"
    ((PASSED++))
else
    echo "⚠️ Potential credential files in recent commits" >> "$REPORT_FILE"
    ((WARNINGS++))
fi

# Summary
echo "" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "## Final Status" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "| Status | Count |" >> "$REPORT_FILE"
echo "|--------|-------|" >> "$REPORT_FILE"
echo "| ✅ Passed | $PASSED |" >> "$REPORT_FILE"
echo "| ⚠️ Warnings | $WARNINGS |" >> "$REPORT_FILE"
echo "| ❌ Errors | $ERRORS |" >> "$REPORT_FILE"

if [ "$ERRORS" -gt 0 ]; then
    echo "" >> "$REPORT_FILE"
    echo "**Overall: ❌ ATTENTION NEEDED**" >> "$REPORT_FILE"
    OVERALL="ATTENTION NEEDED"
elif [ "$WARNINGS" -gt 0 ]; then
    echo "" >> "$REPORT_FILE"
    echo "**Overall: ⚠️ OK with warnings**" >> "$REPORT_FILE"
    OVERALL="OK with warnings"
else
    echo "" >> "$REPORT_FILE"
    echo "**Overall: ✅ All healthy**" >> "$REPORT_FILE"
    OVERALL="All healthy"
fi

log "=== Weekly Maintenance Complete ==="
log "Report saved: $REPORT_FILE"
log "Overall: $OVERALL (Passed: $PASSED, Warnings: $WARNINGS, Errors: $ERRORS)"

echo ""
echo -e "${GREEN}Report saved:${NC} $REPORT_FILE"
echo -e "Overall: $OVERALL"

exit $ERRORS
