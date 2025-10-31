#!/bin/bash

# Music Library Organizer for Jellyfin
# Organizes flat music files into Artist/Album structure

SERVER="ebon@10.0.0.29"
MUSIC_DIR="/mnt/media/music"
ORGANIZED_DIR="/mnt/media/music_organized"

echo "=== Music Library Organizer ==="
echo "This script will organize your music into Artist/Album folders"
echo "for better Jellyfin album art detection."
echo ""
echo "Source: $MUSIC_DIR"
echo "Target: $ORGANIZED_DIR"
echo ""
read -p "Continue? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Function to run commands on server
run_on_server() {
    ssh "$SERVER" "$1"
}

# Create organized directory
echo "Creating organized music directory..."
run_on_server "mkdir -p '$ORGANIZED_DIR'"

# Install ffprobe if needed (for metadata reading)
echo "Checking for ffprobe..."
run_on_server "which ffprobe || sudo apt-get update && sudo apt-get install -y ffmpeg"

# Create organization script on server
echo "Creating organization script..."
cat << 'ORGANIZE_SCRIPT' | ssh "$SERVER" "cat > /tmp/organize_music.py && chmod +x /tmp/organize_music.py"
#!/usr/bin/env python3
import os
import re
import shutil
import subprocess
import json
from pathlib import Path

def get_metadata(file_path):
    """Extract metadata using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            tags = data.get('format', {}).get('tags', {})
            
            # Try different tag names (case insensitive)
            artist = None
            album = None
            title = None
            
            for key, value in tags.items():
                key_lower = key.lower()
                if key_lower in ['artist', 'albumartist', 'album_artist']:
                    artist = value
                elif key_lower in ['album']:
                    album = value
                elif key_lower in ['title', 'track']:
                    title = value
            
            return artist, album, title
    except Exception as e:
        print(f"Error reading metadata from {file_path}: {e}")
    
    return None, None, None

def clean_filename(name):
    """Clean filename for filesystem"""
    if not name:
        return "Unknown"
    
    # Remove invalid characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'[_]+', ' ', name)  # Replace underscores with spaces
    name = name.strip()
    
    return name if name else "Unknown"

def organize_music(source_dir, target_dir):
    """Organize music files into Artist/Album structure"""
    source_path = Path(source_dir)
    target_path = Path(target_dir)
    
    print(f"Organizing music from {source_dir} to {target_dir}")
    
    # Process each music file
    music_extensions = {'.mp3', '.m4a', '.flac', '.wav', '.aac', '.ogg'}
    
    for file_path in source_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in music_extensions:
            print(f"Processing: {file_path.name}")
            
            # Get metadata
            artist, album, title = get_metadata(str(file_path))
            
            # Fallback to filename parsing if no metadata
            if not artist or not album:
                filename = file_path.stem
                
                # Try to parse "Track Artist - Album" format
                if ' - ' in filename:
                    parts = filename.split(' - ', 2)
                    if len(parts) >= 2:
                        if not artist:
                            artist = parts[1] if len(parts) > 2 else parts[0]
                        if not album:
                            album = parts[2] if len(parts) > 2 else parts[1]
                
                # Try to extract from track number prefix
                track_match = re.match(r'^\d+\s+(.+)', filename)
                if track_match and not title:
                    title = track_match.group(1)
            
            # Clean names
            artist = clean_filename(artist)
            album = clean_filename(album)
            title = clean_filename(title) if title else file_path.name
            
            # Create target directory structure
            artist_dir = target_path / artist
            album_dir = artist_dir / album
            album_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy file to organized location
            target_file = album_dir / file_path.name
            try:
                shutil.copy2(file_path, target_file)
                print(f"  -> {artist}/{album}/{file_path.name}")
            except Exception as e:
                print(f"  Error copying {file_path.name}: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: organize_music.py <source_dir> <target_dir>")
        sys.exit(1)
    
    organize_music(sys.argv[1], sys.argv[2])
ORGANIZE_SCRIPT

# Run the organization script
echo "Organizing music files..."
run_on_server "python3 /tmp/organize_music.py '$MUSIC_DIR' '$ORGANIZED_DIR'"

echo ""
echo "Organization complete!"
echo ""
echo "Next steps:"
echo "1. Check the organized structure: ls '$ORGANIZED_DIR'"
echo "2. Update Jellyfin library path to point to '$ORGANIZED_DIR'"
echo "3. Trigger library rescan in Jellyfin"
echo "4. Jellyfin will now automatically fetch album art!"