#!/bin/bash

# Add Album Art to Music Library
# Downloads and adds album art for better Jellyfin display

SERVER="ebon@10.0.0.29"
MUSIC_DIR="/mnt/media/music"

echo "=== Album Art Helper ==="
echo "This script helps add album art to your music library"
echo ""

# Function to run commands on server
run_on_server() {
    ssh "$SERVER" "$1"
}

echo "Jellyfin Album Art Solutions:"
echo ""
echo "1. AUTOMATIC (Recommended):"
echo "   - Run the music organizer script first"
echo "   - Jellyfin will auto-download album art"
echo ""
echo "2. MANUAL METHODS:"
echo "   a) Web Interface:"
echo "      - Go to http://10.0.0.29:8096"
echo "      - Navigate to each album"
echo "      - Click 'Edit Images' -> 'Search for images'"
echo ""
echo "   b) File-based:"
echo "      - Add images named 'cover.jpg' or 'folder.jpg'"
echo "      - Place in each album folder"
echo ""
echo "3. METADATA PROVIDERS:"
echo "   - Enable MusicBrainz in Jellyfin settings"
echo "   - Enable Last.fm plugin"
echo "   - Enable TheAudioDB plugin"

# Check current Jellyfin metadata providers
echo ""
echo "Checking current Jellyfin configuration..."
run_on_server "find /home/ebon/jellyfin-config -name '*.xml' -exec grep -l 'metadata' {} \; 2>/dev/null | head -3"

echo ""
echo "Recommended workflow:"
echo "1. ./organize_music_library.sh  # Organize into Artist/Album folders"
echo "2. Restart Jellyfin"
echo "3. Rescan music library"
echo "4. Jellyfin will automatically fetch album art"