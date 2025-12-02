#!/bin/bash
# conversation_archival_v1.0.0.sh
# Archive old conversation files per conversation_cleanup_protocol.md
#
# Usage:
#   conversation_archival_v1.0.0.sh           # Dry run (preview)
#   conversation_archival_v1.0.0.sh --execute # Actually move files
#   conversation_archival_v1.0.0.sh --days=60 # Custom age threshold
#
# Features:
#   - Archives conversations older than threshold (default 30 days)
#   - Organizes by YYYY-MM folders
#   - Updates INDEX.md
#   - Safe dry-run by default
#
# Cron: 0 5 1 * * /home/dave/skippy/scripts/maintenance/conversation_archival_v1.0.0.sh --execute
#
# Dependencies:
#   - find, mv, date
#
# Created: 2025-12-02

set -euo pipefail

# Configuration
CONVERSATIONS_DIR="/home/dave/skippy/conversations"
ARCHIVE_DIR="$CONVERSATIONS_DIR/archive"
LOG_DIR="/home/dave/skippy/logs/maintenance"
LOG_FILE="$LOG_DIR/conversation_archival.log"
DEFAULT_DAYS=30
DRY_RUN=true
DAYS=$DEFAULT_DAYS

# Parse arguments
for arg in "$@"; do
    case $arg in
        --execute)
            DRY_RUN=false
            ;;
        --days=*)
            DAYS="${arg#*=}"
            ;;
        --help)
            echo "Usage: conversation_archival_v1.0.0.sh [--execute] [--days=N]"
            echo ""
            echo "Options:"
            echo "  --execute    Actually archive (default is dry run)"
            echo "  --days=N     Age threshold in days (default: $DEFAULT_DAYS)"
            exit 0
            ;;
    esac
done

# Ensure directories exist
mkdir -p "$LOG_DIR"

# Logging function
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg" >> "$LOG_FILE"
    echo "$msg"
}

log "=== Conversation Archival Started (dry_run=$DRY_RUN, days=$DAYS) ==="

# Find old conversation files (excluding archive/, active/, and project dirs)
archived_count=0
skipped_count=0

while IFS= read -r -d '' file; do
    filename=$(basename "$file")

    # Skip non-markdown files
    [[ ! "$filename" =~ \.md$ ]] && continue

    # Skip INDEX files
    [[ "$filename" == "INDEX.md" ]] && continue
    [[ "$filename" == "PROTOCOL_INDEX.md" ]] && continue

    # Get file modification date for archive folder
    file_date=$(date -r "$file" +%Y-%m)
    archive_month_dir="$ARCHIVE_DIR/$file_date"

    if $DRY_RUN; then
        log "[DRY RUN] Would archive: $filename -> archive/$file_date/"
    else
        # Create archive month directory
        mkdir -p "$archive_month_dir"

        # Move file
        mv "$file" "$archive_month_dir/"
        log "Archived: $filename -> archive/$file_date/"
    fi

    ((archived_count++))

done < <(find "$CONVERSATIONS_DIR" -maxdepth 1 -name "*.md" -type f -mtime +$DAYS -print0 2>/dev/null)

# Also check for old session directories (YYYYMMDD_*)
while IFS= read -r -d '' dir; do
    dirname=$(basename "$dir")

    # Extract date from directory name (YYYYMMDD format)
    if [[ "$dirname" =~ ^([0-9]{8})_ ]]; then
        dir_date="${BASH_REMATCH[1]}"
        archive_month="${dir_date:0:4}-${dir_date:4:2}"
        archive_month_dir="$ARCHIVE_DIR/$archive_month"

        if $DRY_RUN; then
            log "[DRY RUN] Would archive dir: $dirname -> archive/$archive_month/"
        else
            mkdir -p "$archive_month_dir"
            mv "$dir" "$archive_month_dir/"
            log "Archived dir: $dirname -> archive/$archive_month/"
        fi

        ((archived_count++))
    fi
done < <(find "$CONVERSATIONS_DIR" -maxdepth 1 -type d -mtime +$DAYS -name "[0-9]*_*" -print0 2>/dev/null)

# Update INDEX.md if we archived anything
if [ $archived_count -gt 0 ] && ! $DRY_RUN; then
    # Get current file count
    current_count=$(find "$CONVERSATIONS_DIR" -maxdepth 1 -name "*.md" -type f | wc -l)

    # Update the index file count if it exists
    if [ -f "$CONVERSATIONS_DIR/INDEX.md" ]; then
        # Update the "Total Conversations" line
        sed -i "s/^\*\*Total Conversations:\*\* [0-9]* files/**Total Conversations:** $current_count files/" "$CONVERSATIONS_DIR/INDEX.md"
        # Update the "Last Updated" line
        sed -i "s/^\*\*Last Updated:\*\* [0-9-]*/**Last Updated:** $(date +%Y-%m-%d)/" "$CONVERSATIONS_DIR/INDEX.md"
        log "Updated INDEX.md (now $current_count files)"
    fi
fi

# Summary
log "=== Archival Complete ==="
log "Files/dirs processed: $archived_count"
if $DRY_RUN; then
    log "Mode: DRY RUN (use --execute to actually archive)"
fi

# Keep log file manageable
if [ -f "$LOG_FILE" ]; then
    tail -500 "$LOG_FILE" > "$LOG_FILE.tmp"
    mv "$LOG_FILE.tmp" "$LOG_FILE"
fi
