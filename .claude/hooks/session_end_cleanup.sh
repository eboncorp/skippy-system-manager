#!/bin/bash
# SessionEnd Hook - Cleanup operations when Claude Code session ends
# Created: 2025-11-19
# Version: 1.0.0

# Exit on any error
set -e

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> /home/dave/skippy/.claude/logs/sessions.log
}

# Create logs directory if needed
mkdir -p /home/dave/skippy/.claude/logs

# Log session completion
log "Session ended"

# Archive old work files (older than 30 days)
ARCHIVE_DIR="/home/dave/skippy/.claude/archives"
mkdir -p "$ARCHIVE_DIR"

if [ -d "/home/dave/skippy/work" ]; then
    # Find and archive files older than 30 days
    find /home/dave/skippy/work -type f -mtime +30 -print0 2>/dev/null | \
        xargs -0 tar -czf "$ARCHIVE_DIR/work_$(date +%Y%m%d_%H%M%S).tar.gz" 2>/dev/null || true

    # Remove archived files
    find /home/dave/skippy/work -type f -mtime +30 -delete 2>/dev/null || true

    log "Archived work files older than 30 days"
fi

# Clean up temporary files
if [ -d "/tmp" ]; then
    rm -f /tmp/claude_* 2>/dev/null || true
    log "Cleaned temporary files"
fi

# Success
exit 0
