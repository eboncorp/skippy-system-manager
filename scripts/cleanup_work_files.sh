#!/bin/bash
# Work Files Cleanup - Remove files older than 30 days
# Auto-runs daily via cron
# Part of: Work Files Preservation Protocol v1.0

WORK_DIR="/home/dave/skippy/work"
ARCHIVE_DIR="/home/dave/skippy/work/archive"
LOG_FILE="/home/dave/skippy/logs/work_cleanup.log"

# Ensure log directory exists
mkdir -p /home/dave/skippy/logs

# Log start
echo "[$(date)] Starting work files cleanup..." >> "$LOG_FILE"

# Find directories older than 30 days and move to archive
find "$WORK_DIR" -mindepth 2 -maxdepth 3 -type d -mtime +30 ! -path "*/archive/*" 2>/dev/null | while read -r dir; do
    # Get relative path
    rel_path="${dir#$WORK_DIR/}"

    # Create archive subdirectory structure
    archive_path="$ARCHIVE_DIR/$rel_path"
    mkdir -p "$(dirname "$archive_path")"

    # Move to archive with timestamp
    archive_name="$(basename "$dir")_archived_$(date +%Y%m%d)"
    mv "$dir" "$(dirname "$archive_path")/$archive_name"

    echo "[$(date)] Archived: $rel_path -> archive/$(dirname "$rel_path")/$archive_name" >> "$LOG_FILE"
done

# Delete archived files older than 90 days (total retention: 120 days)
find "$ARCHIVE_DIR" -type d -mtime +90 2>/dev/null | while read -r dir; do
    # Don't delete the archive root directories
    if [ "$dir" != "$ARCHIVE_DIR" ] && [ "$dir" != "$ARCHIVE_DIR/wordpress" ] && [ "$dir" != "$ARCHIVE_DIR/scripts" ] && [ "$dir" != "$ARCHIVE_DIR/documents" ]; then
        rm -rf "$dir"
        echo "[$(date)] Deleted archived directory: ${dir#$ARCHIVE_DIR/}" >> "$LOG_FILE"
    fi
done

# Log completion with stats
if [ -d "$WORK_DIR" ]; then
    WORK_SIZE=$(du -sh "$WORK_DIR" 2>/dev/null | cut -f1)
else
    WORK_SIZE="0"
fi

if [ -d "$ARCHIVE_DIR" ]; then
    ARCHIVE_SIZE=$(du -sh "$ARCHIVE_DIR" 2>/dev/null | cut -f1)
else
    ARCHIVE_SIZE="0"
fi

echo "[$(date)] Cleanup complete. Work dir: $WORK_SIZE, Archive dir: $ARCHIVE_SIZE" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Keep log file manageable (keep last 1000 lines)
if [ -f "$LOG_FILE" ]; then
    tail -1000 "$LOG_FILE" > "$LOG_FILE.tmp"
    mv "$LOG_FILE.tmp" "$LOG_FILE"
fi
