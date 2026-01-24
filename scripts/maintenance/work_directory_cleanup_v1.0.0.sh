#!/bin/bash
# work_directory_cleanup_v1.0.0.sh
# Cleans up old session directories from /home/dave/skippy/work/
#
# Usage:
#   ./work_directory_cleanup_v1.0.0.sh [--dry-run] [--days N]
#
# Options:
#   --dry-run   Show what would be deleted without deleting
#   --days N    Delete sessions older than N days (default: 30)
#
# Created: 2026-01-24

set -euo pipefail

WORK_DIR="/home/dave/skippy/work"
DAYS=30
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --days)
            DAYS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "═══════════════════════════════════════════════════"
echo "  Work Directory Cleanup"
echo "═══════════════════════════════════════════════════"
echo "Directory: $WORK_DIR"
echo "Threshold: $DAYS days"
echo "Dry run:   $DRY_RUN"
echo ""

# Find directories older than N days
TOTAL_SIZE=0
TOTAL_COUNT=0

echo "Sessions to clean up:"
echo "─────────────────────────────────────────────────────"

while IFS= read -r dir; do
    if [[ -d "$dir" ]]; then
        # Get directory size
        SIZE=$(du -sh "$dir" 2>/dev/null | cut -f1)
        SIZE_BYTES=$(du -sb "$dir" 2>/dev/null | cut -f1)

        # Get last modified date
        MTIME=$(stat -c %y "$dir" 2>/dev/null | cut -d' ' -f1)

        echo "  $MTIME  $SIZE  $(basename "$dir")"

        TOTAL_SIZE=$((TOTAL_SIZE + SIZE_BYTES))
        TOTAL_COUNT=$((TOTAL_COUNT + 1))

        if [[ "$DRY_RUN" == "false" ]]; then
            rm -rf "$dir"
        fi
    fi
done < <(find "$WORK_DIR" -mindepth 2 -maxdepth 2 -type d -mtime +$DAYS 2>/dev/null)

# Convert total size to human readable
if [[ $TOTAL_SIZE -gt 1073741824 ]]; then
    HUMAN_SIZE=$(echo "scale=2; $TOTAL_SIZE / 1073741824" | bc)G
elif [[ $TOTAL_SIZE -gt 1048576 ]]; then
    HUMAN_SIZE=$(echo "scale=2; $TOTAL_SIZE / 1048576" | bc)M
elif [[ $TOTAL_SIZE -gt 1024 ]]; then
    HUMAN_SIZE=$(echo "scale=2; $TOTAL_SIZE / 1024" | bc)K
else
    HUMAN_SIZE="${TOTAL_SIZE}B"
fi

echo ""
echo "═══════════════════════════════════════════════════"
echo "Summary:"
echo "  Sessions: $TOTAL_COUNT"
echo "  Space:    $HUMAN_SIZE"
if [[ "$DRY_RUN" == "true" ]]; then
    echo ""
    echo "  (Dry run - nothing deleted)"
    echo "  Run without --dry-run to delete"
else
    echo ""
    echo "  ✅ Cleaned up $TOTAL_COUNT sessions ($HUMAN_SIZE freed)"
fi
echo "═══════════════════════════════════════════════════"
