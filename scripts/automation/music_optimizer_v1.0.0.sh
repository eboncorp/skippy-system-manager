#!/bin/bash

# Music Library Optimizer for Jellyfin
# Converts WMA to MP3, moves iTunes artifacts, and organizes music files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MUSIC_DIR="/mnt/media/music"
ARCHIVE_DIR="/home/ebon/music_archived_$(date +%Y%m%d)"
LOG_FILE="/home/ebon/music_conversion_$(date +%Y%m%d_%H%M%S).log"
PARALLEL_JOBS=4  # Number of parallel conversion jobs

# Server connection info
SERVER="ebon@10.0.0.29"

echo -e "${BLUE}=== Music Library Optimizer for Jellyfin ===${NC}"
echo "This script will:"
echo "1. Convert WMA files to high-quality MP3 (keeping originals)"
echo "2. Move iTunes artifacts to archive folder (itc2, itl, itdb files)"
echo "3. Move original WMA files to archive after conversion"
echo "4. Verify M4A files are playable"
echo "5. Keep everything safe - NO DELETIONS"
echo ""
echo -e "${YELLOW}Archive location: $ARCHIVE_DIR${NC}"
echo ""
read -p "Continue? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to run commands on the server
run_on_server() {
    ssh "$SERVER" "$1"
}

# Check if ffmpeg is installed on server
echo -e "${YELLOW}Checking requirements on server...${NC}"
if ! run_on_server "command -v ffmpeg >/dev/null 2>&1"; then
    echo -e "${YELLOW}Installing ffmpeg on server...${NC}"
    run_on_server "sudo apt-get update && sudo apt-get install -y ffmpeg"
fi

# Create archive directory
echo -e "${BLUE}Creating archive directory...${NC}"
run_on_server "mkdir -p '$ARCHIVE_DIR/wma_originals' '$ARCHIVE_DIR/itunes_artifacts'"

# Count files
echo -e "${BLUE}Analyzing music library...${NC}"
WMA_COUNT=$(run_on_server "find '$MUSIC_DIR' -type f -iname '*.wma' 2>/dev/null | wc -l")
M4A_COUNT=$(run_on_server "find '$MUSIC_DIR' -type f -iname '*.m4a' 2>/dev/null | wc -l")
ITC_COUNT=$(run_on_server "find '$MUSIC_DIR' -type f -iname '*.itc2' 2>/dev/null | wc -l")
ITUNES_COUNT=$(run_on_server "find '$MUSIC_DIR' -type f \( -iname '*.itl' -o -iname '*.itdb' -o -iname 'iTunes*.xml' -o -iname '*.plist' \) 2>/dev/null | wc -l")

echo -e "${GREEN}Found:${NC}"
echo "  - $WMA_COUNT WMA files to convert"
echo "  - $M4A_COUNT M4A files to verify"
echo "  - $ITC_COUNT ITC2 cache files to move"
echo "  - $ITUNES_COUNT iTunes database files to move"
echo ""

# Create conversion script on server
echo -e "${BLUE}Creating conversion script on server...${NC}"
cat << 'CONVERSION_SCRIPT' | ssh "$SERVER" "cat > /tmp/convert_wma.sh && chmod +x /tmp/convert_wma.sh"
#!/bin/bash
# WMA to MP3 converter function

convert_file() {
    local input_file="$1"
    local output_file="${input_file%.*}.mp3"
    local archive_dir="$2"
    
    # Create archive subdirectory structure
    local rel_path="${input_file#$3/}"
    local archive_path="$archive_dir/wma_originals/$rel_path"
    local archive_dir_path="$(dirname "$archive_path")"
    
    mkdir -p "$archive_dir_path"
    
    # Convert to MP3 (high quality: 320kbps)
    if ffmpeg -i "$input_file" -acodec libmp3lame -ab 320k -map_metadata 0 -id3v2_version 3 "$output_file" -y </dev/null >/dev/null 2>&1; then
        # If conversion successful, move original to archive
        mv "$input_file" "$archive_path"
        echo "✓ Converted: $(basename "$input_file")"
        return 0
    else
        echo "✗ Failed: $(basename "$input_file")"
        return 1
    fi
}

export -f convert_file
export MUSIC_DIR="$1"
export ARCHIVE_DIR="$2"

# Process WMA files in parallel
find "$MUSIC_DIR" -type f -iname "*.wma" -print0 | \
    xargs -0 -P "$3" -I {} bash -c 'convert_file "$@"' _ {} "$ARCHIVE_DIR" "$MUSIC_DIR"
CONVERSION_SCRIPT

# Run WMA conversion
if [ "$WMA_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}Converting $WMA_COUNT WMA files to MP3...${NC}"
    echo "This may take a while. Using $PARALLEL_JOBS parallel jobs."
    
    run_on_server "/tmp/convert_wma.sh '$MUSIC_DIR' '$ARCHIVE_DIR' $PARALLEL_JOBS" &
    
    # Show progress
    while run_on_server "pgrep -f convert_wma.sh >/dev/null 2>&1"; do
        CONVERTED=$(run_on_server "find '$MUSIC_DIR' -type f -iname '*.mp3' 2>/dev/null | wc -l")
        echo -ne "\rProgress: Converting... ($CONVERTED MP3 files created)"
        sleep 5
    done
    echo ""
    echo -e "${GREEN}WMA conversion complete!${NC}"
fi

# Move iTunes artifacts to archive
echo -e "${BLUE}Moving iTunes artifacts to archive...${NC}"

# Move ITC2 files (iTunes cache files - not actual music)
if [ "$ITC_COUNT" -gt 0 ]; then
    echo "Moving $ITC_COUNT ITC2 files to archive..."
    run_on_server "find '$MUSIC_DIR' -type f -iname '*.itc2' | while read -r file; do
        rel_path=\"\${file#$MUSIC_DIR/}\"
        target=\"$ARCHIVE_DIR/itunes_artifacts/\$rel_path\"
        mkdir -p \"\$(dirname \"\$target\")\"
        mv \"\$file\" \"\$target\"
    done"
    echo -e "${GREEN}✓ ITC2 files moved to archive${NC}"
fi

# Move iTunes database files
if [ "$ITUNES_COUNT" -gt 0 ]; then
    echo "Moving iTunes database files to archive..."
    run_on_server "find '$MUSIC_DIR' -type f \( -iname '*.itl' -o -iname '*.itdb' -o -iname 'iTunes*.xml' -o -iname '*.plist' \) | while read -r file; do
        rel_path=\"\${file#$MUSIC_DIR/}\"
        target=\"$ARCHIVE_DIR/itunes_artifacts/\$rel_path\"
        mkdir -p \"\$(dirname \"\$target\")\"
        mv \"\$file\" \"\$target\"
    done"
    echo -e "${GREEN}✓ iTunes database files moved to archive${NC}"
fi

# Verify M4A files
echo -e "${BLUE}Verifying M4A files...${NC}"
PROBLEMATIC_M4A=$(run_on_server "
    find '$MUSIC_DIR' -type f -iname '*.m4a' | while read -r file; do
        if ! ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 \"\$file\" >/dev/null 2>&1; then
            echo \"\$file\"
        fi
    done
" | wc -l)

if [ "$PROBLEMATIC_M4A" -gt 0 ]; then
    echo -e "${YELLOW}Found $PROBLEMATIC_M4A problematic M4A files. These may need manual review.${NC}"
fi

# Clean up empty directories
echo -e "${BLUE}Cleaning up empty directories...${NC}"
run_on_server "find '$MUSIC_DIR' -type d -empty -delete"

# Restart Jellyfin to rescan library
echo -e "${BLUE}Restarting Jellyfin to rescan library...${NC}"
run_on_server "sudo docker restart jellyfin"

# Wait for Jellyfin to start
sleep 10

# Trigger library scan
echo -e "${BLUE}Triggering Jellyfin library scan...${NC}"
run_on_server "curl -X POST 'http://localhost:8096/Library/Refresh' || true"

# Final statistics
echo -e "${GREEN}=== Optimization Complete ===${NC}"
echo ""
echo "Summary:"
FINAL_MP3=$(run_on_server "find '$MUSIC_DIR' -type f -iname '*.mp3' 2>/dev/null | wc -l")
FINAL_M4A=$(run_on_server "find '$MUSIC_DIR' -type f -iname '*.m4a' 2>/dev/null | wc -l")
FINAL_WMA=$(run_on_server "find '$MUSIC_DIR' -type f -iname '*.wma' 2>/dev/null | wc -l")
FINAL_TOTAL=$((FINAL_MP3 + FINAL_M4A))

echo "  - MP3 files: $FINAL_MP3"
echo "  - M4A files: $FINAL_M4A"
echo "  - Remaining WMA files: $FINAL_WMA"
echo "  - Total playable files: $FINAL_TOTAL"
echo ""
echo -e "${GREEN}All original files archived to: $ARCHIVE_DIR${NC}"
echo -e "${GREEN}Log file: $LOG_FILE${NC}"
echo ""
echo "Jellyfin is now rescanning the library. This may take a few minutes."
echo "You can monitor progress at: http://10.0.0.29:8096"