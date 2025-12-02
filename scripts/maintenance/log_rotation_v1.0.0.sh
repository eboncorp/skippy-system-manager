#!/bin/bash
# log_rotation_v1.0.0.sh
# Rotate and compress log files across all Skippy systems
#
# Usage:
#   log_rotation_v1.0.0.sh              # Rotate all logs
#   log_rotation_v1.0.0.sh --dry-run    # Preview only
#
# Features:
#   - Rotates logs older than retention period
#   - Compresses rotated logs
#   - Removes very old archives
#   - Reports space freed
#
# Cron: 0 4 * * 0 /home/dave/skippy/scripts/maintenance/log_rotation_v1.0.0.sh
#
# Dependencies:
#   - gzip
#   - find
#
# Created: 2025-12-01

set -euo pipefail

# Configuration
DRY_RUN=false
ROTATE_DAYS=7
ARCHIVE_DAYS=30
DELETE_DAYS=90

# Log directories to manage
LOG_DIRS=(
    "/home/dave/skippy/logs"
    "$HOME/.claude/logs"
)

# Parse arguments
for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            ;;
        --help)
            echo "Usage: log_rotation_v1.0.0.sh [--dry-run]"
            echo ""
            echo "Options:"
            echo "  --dry-run    Preview changes without executing"
            echo ""
            echo "Policy:"
            echo "  - Rotate logs older than $ROTATE_DAYS days"
            echo "  - Compress archives older than $ARCHIVE_DAYS days"
            echo "  - Delete archives older than $DELETE_DAYS days"
            exit 0
            ;;
    esac
done

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              LOG ROTATION v1.0.0                             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Mode: $([ "$DRY_RUN" = true ] && echo 'DRY RUN' || echo 'EXECUTE')"
echo "Rotate: $ROTATE_DAYS days | Archive: $ARCHIVE_DAYS days | Delete: $DELETE_DAYS days"
echo ""

# Initialize counters
ROTATED=0
COMPRESSED=0
DELETED=0
SPACE_FREED=0

for LOG_DIR in "${LOG_DIRS[@]}"; do
    if [[ ! -d "$LOG_DIR" ]]; then
        echo "⊘  Skipping: $LOG_DIR (not found)"
        continue
    fi

    echo "┌─────────────────────────────────────────────────────────────┐"
    echo "│ $LOG_DIR"
    echo "└─────────────────────────────────────────────────────────────┘"

    BEFORE_SIZE=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1)
    echo "  Size before: $BEFORE_SIZE"

    # Step 1: Rotate large logs (> 10MB and older than ROTATE_DAYS)
    echo "  [1/3] Rotating large logs..."
    while IFS= read -r -d '' log_file; do
        FILE_SIZE=$(stat -c %s "$log_file" 2>/dev/null || echo 0)
        if [[ $FILE_SIZE -gt 10485760 ]]; then  # 10MB
            TIMESTAMP=$(date +%Y%m%d_%H%M%S)
            ROTATED_NAME="${log_file}.${TIMESTAMP}"

            if [[ "$DRY_RUN" = true ]]; then
                echo "    Would rotate: $(basename "$log_file") ($(numfmt --to=iec-i --suffix=B "$FILE_SIZE"))"
            else
                mv "$log_file" "$ROTATED_NAME"
                touch "$log_file"
                echo "    Rotated: $(basename "$log_file")"
            fi
            ROTATED=$((ROTATED + 1))
        fi
    done < <(find "$LOG_DIR" -name "*.log" -type f -mtime +$ROTATE_DAYS -print0 2>/dev/null)

    # Step 2: Compress uncompressed rotated logs (older than ARCHIVE_DAYS)
    echo "  [2/3] Compressing old logs..."
    while IFS= read -r -d '' log_file; do
        if [[ ! "$log_file" == *.gz ]]; then
            FILE_SIZE=$(stat -c %s "$log_file" 2>/dev/null || echo 0)
            if [[ "$DRY_RUN" = true ]]; then
                echo "    Would compress: $(basename "$log_file")"
            else
                gzip "$log_file"
                echo "    Compressed: $(basename "$log_file")"
            fi
            COMPRESSED=$((COMPRESSED + 1))
        fi
    done < <(find "$LOG_DIR" -name "*.log.*" -type f ! -name "*.gz" -mtime +$ARCHIVE_DAYS -print0 2>/dev/null)

    # Step 3: Delete very old archives (older than DELETE_DAYS)
    echo "  [3/3] Removing old archives..."
    while IFS= read -r -d '' archive; do
        FILE_SIZE=$(stat -c %s "$archive" 2>/dev/null || echo 0)
        SPACE_FREED=$((SPACE_FREED + FILE_SIZE))

        if [[ "$DRY_RUN" = true ]]; then
            echo "    Would delete: $(basename "$archive")"
        else
            rm "$archive"
            echo "    Deleted: $(basename "$archive")"
        fi
        DELETED=$((DELETED + 1))
    done < <(find "$LOG_DIR" -name "*.log.*.gz" -type f -mtime +$DELETE_DAYS -print0 2>/dev/null)

    AFTER_SIZE=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1)
    echo "  Size after: $AFTER_SIZE"
    echo ""
done

# Summary
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ Summary                                                     │"
echo "└─────────────────────────────────────────────────────────────┘"
echo "  Logs rotated: $ROTATED"
echo "  Logs compressed: $COMPRESSED"
echo "  Archives deleted: $DELETED"

if [[ $SPACE_FREED -gt 0 ]]; then
    echo "  Space freed: $(numfmt --to=iec-i --suffix=B "$SPACE_FREED" 2>/dev/null || echo "${SPACE_FREED}B")"
fi

if [[ "$DRY_RUN" = true ]]; then
    echo ""
    echo "This was a DRY RUN. To execute, run:"
    echo "  $0"
fi

echo ""
