#!/usr/bin/env python3
"""
Album-Only Music Organizer
Organizes music by album name only
"""

import os
import sys
import json
import shutil
import subprocess
import re
from pathlib import Path
from datetime import datetime

SOURCE_DIR = "/mnt/media/COMPLETE_MUSIC_LIBRARY"
TARGET_DIR = "/mnt/media/MUSIC_BY_ALBUM"
LOG_FILE = "/home/ebon/album_organize.log"

class AlbumOrganizer:
    def __init__(self):
        self.processed = 0
        self.errors = 0
        self.start_time = datetime.now()
        
    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        with open(LOG_FILE, 'a') as f:
            f.write(log_msg + '\n')
    
    def get_metadata(self, file_path):
        """Extract metadata from file"""
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                tags = data.get('format', {}).get('tags', {})
                
                artist = tags.get('artist') or tags.get('ARTIST') or 'Unknown Artist'
                album = tags.get('album') or tags.get('ALBUM') or 'Singles'
                title = tags.get('title') or tags.get('TITLE') or Path(file_path).stem
                track = tags.get('track') or tags.get('TRACK') or ''
                
                # Clean track number
                if '/' in str(track):
                    track = track.split('/')[0]
                
                return {
                    'artist': self.clean_name(artist),
                    'album': self.clean_name(album),
                    'title': self.clean_name(title),
                    'track': track
                }
        except:
            pass
        
        # Fallback to filename
        return {
            'artist': 'Unknown Artist',
            'album': 'Singles',
            'title': Path(file_path).stem,
            'track': ''
        }
    
    def clean_name(self, name):
        """Clean name for filesystem"""
        # Remove invalid characters
        invalid = '<>:"/\\|?*'
        for char in invalid:
            name = name.replace(char, '')
        
        # Clean up whitespace and underscores
        name = name.replace('_', ' ')
        name = ' '.join(name.split())
        
        # Limit length
        if len(name) > 150:
            name = name[:150]
        
        return name.strip() or 'Unknown'
    
    def organize_by_album(self):
        """Organize all music files by album only"""
        self.log("Starting album-only organization...")
        
        # Create target directory
        Path(TARGET_DIR).mkdir(exist_ok=True)
        
        # Get all music files
        music_files = []
        for file in os.listdir(SOURCE_DIR):
            if any(file.lower().endswith(ext) for ext in ['.mp3', '.m4a', '.flac']):
                music_files.append(os.path.join(SOURCE_DIR, file))
        
        self.log(f"Found {len(music_files)} files to organize")
        
        for file_path in music_files:
            try:
                # Get metadata
                metadata = self.get_metadata(file_path)
                
                # Create album directory directly under target
                album_dir = Path(TARGET_DIR) / metadata['album']
                album_dir.mkdir(exist_ok=True)
                
                # Create filename with artist (since multiple artists may be in one album)
                track = metadata['track']
                if track and track.isdigit():
                    filename = f"{track.zfill(2)} - {metadata['artist']} - {metadata['title']}"
                else:
                    filename = f"{metadata['artist']} - {metadata['title']}"
                
                # Add extension
                ext = Path(file_path).suffix
                filename = f"{filename}{ext}"
                
                target_file = album_dir / filename
                
                # Handle duplicates
                if target_file.exists():
                    base = target_file.stem
                    counter = 1
                    while target_file.exists():
                        target_file = album_dir / f"{base} ({counter}){ext}"
                        counter += 1
                
                # Copy file
                shutil.copy2(file_path, target_file)
                self.processed += 1
                
                if self.processed % 100 == 0:
                    self.log(f"Organized {self.processed} files...")
                
            except Exception as e:
                self.log(f"Error processing {os.path.basename(file_path)}: {e}")
                self.errors += 1
    
    def create_summary(self):
        """Create organization summary"""
        # Count albums
        albums = len([d for d in Path(TARGET_DIR).iterdir() if d.is_dir()])
        
        duration = (datetime.now() - self.start_time).total_seconds()
        
        summary = {
            'files_processed': self.processed,
            'errors': self.errors,
            'albums_created': albums,
            'duration_seconds': duration,
            'completed_at': datetime.now().isoformat()
        }
        
        with open('/home/ebon/album_organize_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.log(f"Album organization complete!")
        self.log(f"Files processed: {self.processed}")
        self.log(f"Albums created: {albums}")
        self.log(f"Errors: {self.errors}")
        self.log(f"Duration: {duration:.1f} seconds")
    
    def run(self):
        self.organize_by_album()
        self.create_summary()

if __name__ == "__main__":
    organizer = AlbumOrganizer()
    organizer.run()
