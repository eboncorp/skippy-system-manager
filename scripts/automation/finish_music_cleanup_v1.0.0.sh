#!/bin/bash

# Complete Music Cleanup - Final Steps
# This script handles the remaining cleanup tasks

SERVER="ebon@10.0.0.29"
MUSIC_DIR="/mnt/media/music"
ARCHIVE_DIR="/home/ebon/music_archived_$(date +%Y%m%d)"

echo "=== Completing Music Library Cleanup ==="
echo "Archive location: $ARCHIVE_DIR"

# Function to run commands on server
run_on_server() {
    ssh "$SERVER" "$1"
}

# Count remaining files
echo "Checking current status..."
WMA_COUNT=$(run_on_server "find '$MUSIC_DIR' -type f -iname '*.wma' 2>/dev/null | wc -l")
MP3_COUNT=$(run_on_server "find '$MUSIC_DIR' -type f -iname '*.mp3' 2>/dev/null | wc -l")
ITC_COUNT=$(run_on_server "find '$MUSIC_DIR' -type f -iname '*.itc2' 2>/dev/null | wc -l")

echo "Current status:"
echo "  - MP3 files: $MP3_COUNT"
echo "  - Remaining WMA files: $WMA_COUNT"
echo "  - ITC2 files to move: $ITC_COUNT"

# Move iTunes artifacts to archive
if [ "$ITC_COUNT" -gt 0 ]; then
    echo "Moving $ITC_COUNT ITC2 files to archive..."
    run_on_server "find '$MUSIC_DIR' -type f -iname '*.itc2' | while read -r file; do
        rel_path=\"\${file#$MUSIC_DIR/}\"
        target=\"$ARCHIVE_DIR/itunes_artifacts/\$rel_path\"
        mkdir -p \"\$(dirname \"\$target\")\"
        mv \"\$file\" \"\$target\"
        echo \"Moved: \$(basename \"\$file\")\"
    done"
    echo "✓ ITC2 files moved to archive"
fi

# Move other iTunes files
echo "Moving iTunes database files..."
run_on_server "find '$MUSIC_DIR' -type f \( -iname '*.itl' -o -iname '*.itdb' -o -iname 'iTunes*.xml' -o -iname '*.plist' \) | while read -r file; do
    rel_path=\"\${file#$MUSIC_DIR/}\"
    target=\"$ARCHIVE_DIR/itunes_artifacts/\$rel_path\"
    mkdir -p \"\$(dirname \"\$target\")\"
    mv \"\$file\" \"\$target\"
    echo \"Moved: \$(basename \"\$file\")\"
done"

# Move remaining WMA files to archive
if [ "$WMA_COUNT" -gt 0 ]; then
    echo "Moving $WMA_COUNT remaining WMA files to archive..."
    run_on_server "find '$MUSIC_DIR' -type f -iname '*.wma' | while read -r file; do
        rel_path=\"\${file#$MUSIC_DIR/}\"
        target=\"$ARCHIVE_DIR/wma_originals/\$rel_path\"
        mkdir -p \"\$(dirname \"\$target\")\"
        mv \"\$file\" \"\$target\"
        echo \"Moved: \$(basename \"\$file\")\"
    done"
    echo "✓ Remaining WMA files moved to archive"
fi

# Clean up empty directories
echo "Cleaning up empty directories..."
run_on_server "find '$MUSIC_DIR' -type d -empty -delete"

# Restart Jellyfin
echo "Restarting Jellyfin to rescan library..."
run_on_server "sudo docker restart jellyfin"

# Wait for Jellyfin to start
sleep 10

# Trigger library scan
echo "Triggering Jellyfin library scan..."
run_on_server "curl -X POST 'http://localhost:8096/Library/Refresh' || true"

# Final statistics
echo ""
echo "=== Cleanup Complete ==="
FINAL_MP3=$(run_on_server "find '$MUSIC_DIR' -type f -iname '*.mp3' 2>/dev/null | wc -l")
FINAL_M4A=$(run_on_server "find '$MUSIC_DIR' -type f -iname '*.m4a' 2>/dev/null | wc -l")
FINAL_WMA=$(run_on_server "find '$MUSIC_DIR' -type f -iname '*.wma' 2>/dev/null | wc -l")
FINAL_TOTAL=$((FINAL_MP3 + FINAL_M4A))

echo "Final Summary:"
echo "  - MP3 files: $FINAL_MP3"
echo "  - M4A files: $FINAL_M4A"
echo "  - Remaining WMA files: $FINAL_WMA"
echo "  - Total playable files: $FINAL_TOTAL"
echo ""
echo "All original files archived to: $ARCHIVE_DIR"
echo "Jellyfin is rescanning the library..."
echo "Monitor progress at: http://10.0.0.29:8096"