#!/bin/bash
# session_cleanup_v1.0.0.sh
# Clean up old session directories while preserving recent work
#
# Usage:
#   session_cleanup_v1.0.0.sh                    # Dry run (preview)
#   session_cleanup_v1.0.0.sh --execute          # Actually delete
#   session_cleanup_v1.0.0.sh --days=14          # Custom retention
#
# Features:
#   - Keeps sessions newer than retention period
#   - Archives important sessions before deletion
#   - Generates cleanup report
#   - Safe dry-run by default
#
# Cron: 0 3 * * 0 /home/dave/skippy/scripts/maintenance/session_cleanup_v1.0.0.sh --execute
#
# Dependencies:
#   - tar (for archiving)
#   - find
#
# Created: 2025-12-01

set -euo pipefail

# Configuration
WORK_DIR="/home/dave/skippy/work"
ARCHIVE_DIR="/home/dave/skippy/archives/sessions"
LOG_DIR="/home/dave/skippy/logs/maintenance"
LOG_FILE="$LOG_DIR/session_cleanup.log"
DEFAULT_RETENTION_DAYS=14
DRY_RUN=true
RETENTION_DAYS=$DEFAULT_RETENTION_DAYS

# Parse arguments
for arg in "$@"; do
    case $arg in
        --execute)
            DRY_RUN=false
            ;;
        --days=*)
            RETENTION_DAYS="${arg#*=}"
            ;;
        --help)
            echo "Usage: session_cleanup_v1.0.0.sh [--execute] [--days=N]"
            echo ""
            echo "Options:"
            echo "  --execute    Actually delete (default is dry run)"
            echo "  --days=N     Retention period in days (default: $DEFAULT_RETENTION_DAYS)"
            echo ""
            exit 0
            ;;
    esac
done

# Ensure directories exist
mkdir -p "$ARCHIVE_DIR" "$LOG_DIR"

# Logging function
log() {
    local level="$1"
    local message="$2"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $message" >> "$LOG_FILE"
    echo "[$level] $message"
}

log "INFO" "=== Session Cleanup Started ==="
log "INFO" "Work directory: $WORK_DIR"
log "INFO" "Retention: $RETENTION_DAYS days"
log "INFO" "Mode: $([ "$DRY_RUN" = true ] && echo 'DRY RUN' || echo 'EXECUTE')"

# Initialize counters
SESSIONS_FOUND=0
SESSIONS_ARCHIVED=0
SESSIONS_DELETED=0
SPACE_FREED=0

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              SESSION CLEANUP v1.0.0                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Mode: $([ "$DRY_RUN" = true ] && echo 'DRY RUN (preview only)' || echo 'EXECUTE')"
echo "Retention: $RETENTION_DAYS days"
echo ""

# Find old session directories
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ Scanning for old sessions...                                │"
echo "└─────────────────────────────────────────────────────────────┘"

# Get current disk usage
BEFORE_SIZE=$(du -sh "$WORK_DIR" 2>/dev/null | cut -f1)
echo "Current work directory size: $BEFORE_SIZE"
echo ""

# Find all session directories (format: YYYYMMDD_HHMMSS_*)
while IFS= read -r -d '' session_dir; do
    SESSIONS_FOUND=$((SESSIONS_FOUND + 1))
    DIR_NAME=$(basename "$session_dir")
    DIR_SIZE=$(du -sh "$session_dir" 2>/dev/null | cut -f1)
    DIR_SIZE_BYTES=$(du -sb "$session_dir" 2>/dev/null | cut -f1)

    # Extract date from directory name (YYYYMMDD)
    DIR_DATE="${DIR_NAME:0:8}"

    # Check if directory has README.md with important markers
    HAS_IMPORTANT=false
    if [[ -f "$session_dir/README.md" ]]; then
        if grep -qiE 'KEEP|IMPORTANT|DO NOT DELETE|PRODUCTION' "$session_dir/README.md" 2>/dev/null; then
            HAS_IMPORTANT=true
        fi
    fi

    if [[ "$HAS_IMPORTANT" = true ]]; then
        echo "  KEEP: $DIR_NAME ($DIR_SIZE) - marked important"
        log "INFO" "KEEP: $session_dir (marked important)"
    else
        echo "  DELETE: $DIR_NAME ($DIR_SIZE)"

        if [[ "$DRY_RUN" = false ]]; then
            # Check if we should archive first
            ARCHIVE_NAME="${DIR_NAME}.tar.gz"
            ARCHIVE_PATH="$ARCHIVE_DIR/$ARCHIVE_NAME"

            # Archive if larger than 1MB
            if [[ $DIR_SIZE_BYTES -gt 1048576 ]]; then
                log "INFO" "Archiving: $session_dir -> $ARCHIVE_PATH"
                tar -czf "$ARCHIVE_PATH" -C "$(dirname "$session_dir")" "$(basename "$session_dir")" 2>/dev/null
                SESSIONS_ARCHIVED=$((SESSIONS_ARCHIVED + 1))
            fi

            # Delete the directory
            rm -rf "$session_dir"
            SESSIONS_DELETED=$((SESSIONS_DELETED + 1))
            SPACE_FREED=$((SPACE_FREED + DIR_SIZE_BYTES))
            log "INFO" "Deleted: $session_dir"
        fi
    fi
done < <(find "$WORK_DIR" -mindepth 2 -maxdepth 3 -type d -name "[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_*" -mtime +$RETENTION_DAYS -print0 2>/dev/null)

# Summary
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ Summary                                                     │"
echo "└─────────────────────────────────────────────────────────────┘"
echo "Sessions found older than $RETENTION_DAYS days: $SESSIONS_FOUND"

if [[ "$DRY_RUN" = true ]]; then
    echo ""
    echo "This was a DRY RUN. To actually delete, run:"
    echo "  $0 --execute"
else
    echo "Sessions archived: $SESSIONS_ARCHIVED"
    echo "Sessions deleted: $SESSIONS_DELETED"
    AFTER_SIZE=$(du -sh "$WORK_DIR" 2>/dev/null | cut -f1)
    echo ""
    echo "Space before: $BEFORE_SIZE"
    echo "Space after: $AFTER_SIZE"
    if [[ $SPACE_FREED -gt 0 ]]; then
        SPACE_MB=$(echo "scale=2; $SPACE_FREED / 1048576" | bc)
        echo "Space freed: ${SPACE_MB}MB"
    fi
fi

log "INFO" "Sessions found: $SESSIONS_FOUND, Archived: $SESSIONS_ARCHIVED, Deleted: $SESSIONS_DELETED"
log "INFO" "=== Session Cleanup Complete ==="

echo ""
echo "Log file: $LOG_FILE"
