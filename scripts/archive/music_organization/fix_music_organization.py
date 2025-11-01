#!/usr/bin/env python3
"""
Fix Music Organization Issues
- Extract primary artists from collaborations
- Consolidate albums under main artists
- Clean up metadata and folder structure
"""

import os
import sys
import json
import shutil
import re
from pathlib import Path
from datetime import datetime
import subprocess

# Configuration
ORGANIZED_DIR = "/mnt/media/music_organized"
FIXED_DIR = "/mnt/media/music_fixed"
STATE_FILE = "/home/ebon/music_fix_state.json"
LOG_FILE = "/home/ebon/music_fix.log"

class MusicFixer:
    def __init__(self):
        self.processed_count = 0
        self.error_count = 0
        self.moved_count = 0
        self.start_time = datetime.now()
        
    def log(self, message):
        """Log message to file and stdout"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        
        with open(LOG_FILE, 'a') as f:
            f.write(log_msg + '\n')
    
    def extract_primary_artist(self, artist_name):
        """Extract primary artist from collaboration string"""
        # Remove common separators and get first artist
        
        # Handle specific patterns
        if '; ' in artist_name:
            primary = artist_name.split('; ')[0]
        elif ' feat. ' in artist_name.lower():
            primary = artist_name.split(' feat. ')[0]
        elif ' featuring ' in artist_name.lower():
            primary = artist_name.split(' featuring ')[0]
        elif ' & ' in artist_name:
            primary = artist_name.split(' & ')[0]
        elif ' and ' in artist_name.lower():
            primary = artist_name.split(' and ')[0]
        else:
            primary = artist_name
        
        # Clean up the primary artist name
        primary = primary.strip()
        
        # Handle specific edge cases
        if primary.startswith('DJ '):
            # For DJ collaborations, might want to keep both
            if len(artist_name.split('; ')) == 2:
                parts = artist_name.split('; ')
                if not parts[1].startswith('DJ'):
                    primary = parts[1]  # Use the non-DJ artist as primary
        
        return self.clean_artist_name(primary)
    
    def clean_artist_name(self, name):
        """Clean artist name for filesystem"""
        # Remove invalid characters but keep the essence
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        name = re.sub(r'\s+', ' ', name)  # Multiple spaces to single
        return name.strip()
    
    def clean_album_name(self, name):
        """Clean album name"""
        # Fix common issues
        name = name.replace('_', ' ')
        name = re.sub(r'\[.*?\]', '', name)  # Remove bracketed content like [Clean], [Deluxe]
        name = re.sub(r'\s+', ' ', name)
        name = name.strip()
        
        # Handle disc/volume indicators
        if 'Disc ' in name or 'Vol.' in name or 'Vol ' in name:
            # Keep these as they're important for multi-disc albums
            pass
            
        return name
    
    def should_reorganize(self, artist_path):
        """Check if artist folder needs reorganization"""
        artist_name = os.path.basename(artist_path)
        
        # Check for collaboration indicators
        if ('; ' in artist_name or 
            ' feat. ' in artist_name.lower() or 
            ' featuring ' in artist_name.lower()):
            return True
            
        return False
    
    def get_album_key(self, album_name):
        """Generate a key for album matching"""
        # Remove disc/volume indicators for matching
        key = re.sub(r'(disc|vol\.?)\s*\d+', '', album_name, flags=re.IGNORECASE)
        key = re.sub(r'\[.*?\]', '', key)  # Remove brackets
        key = re.sub(r'\s+', ' ', key).strip().lower()
        return key
    
    def move_files_to_primary_artist(self, source_artist_path, target_artist_name):
        """Move all files from collaboration folder to primary artist"""
        source_artist_name = os.path.basename(source_artist_path)
        target_artist_path = Path(FIXED_DIR) / target_artist_name
        
        self.log(f"Moving {source_artist_name} -> {target_artist_name}")
        
        # Create target artist directory
        target_artist_path.mkdir(parents=True, exist_ok=True)
        
        # Process each album
        for album_dir in Path(source_artist_path).iterdir():
            if not album_dir.is_dir():
                continue
                
            album_name = album_dir.name
            cleaned_album = self.clean_album_name(album_name)
            
            target_album_path = target_artist_path / cleaned_album
            
            # Handle duplicate album names
            if target_album_path.exists():
                # Merge with existing album or create variant
                self.log(f"  Album exists: {cleaned_album} - merging files")
                self.merge_album_files(album_dir, target_album_path)
            else:
                # Move entire album folder
                try:
                    shutil.copytree(album_dir, target_album_path)
                    self.log(f"  Moved album: {cleaned_album}")
                    self.moved_count += 1
                except Exception as e:
                    self.log(f"  Error moving album {album_name}: {e}")
                    self.error_count += 1
    
    def merge_album_files(self, source_album_path, target_album_path):
        """Merge files from source album into target album"""
        for music_file in source_album_path.iterdir():
            if music_file.is_file() and music_file.suffix.lower() in ['.mp3', '.m4a', '.flac']:
                target_file = target_album_path / music_file.name
                
                # Handle duplicate filenames
                if target_file.exists():
                    base = target_file.stem
                    ext = target_file.suffix
                    counter = 1
                    while target_file.exists():
                        target_file = target_album_path / f"{base}_alt{counter}{ext}"
                        counter += 1
                
                try:
                    shutil.copy2(music_file, target_file)
                    self.log(f"    Merged: {music_file.name}")
                except Exception as e:
                    self.log(f"    Error merging {music_file.name}: {e}")
    
    def process_clean_artists(self):
        """Copy non-collaboration artists as-is"""
        self.log("Processing clean artists...")
        
        for artist_path in Path(ORGANIZED_DIR).iterdir():
            if not artist_path.is_dir():
                continue
                
            if not self.should_reorganize(str(artist_path)):
                artist_name = artist_path.name
                target_path = Path(FIXED_DIR) / artist_name
                
                if not target_path.exists():
                    try:
                        shutil.copytree(artist_path, target_path)
                        self.log(f"Copied clean artist: {artist_name}")
                        self.processed_count += 1
                    except Exception as e:
                        self.log(f"Error copying {artist_name}: {e}")
                        self.error_count += 1
    
    def run(self):
        """Main reorganization process"""
        self.log("Starting music organization fix...")
        
        # Create fixed directory
        Path(FIXED_DIR).mkdir(exist_ok=True)
        
        # First pass: Process collaboration artists
        self.log("Processing collaboration artists...")
        
        collaboration_artists = []
        for artist_path in Path(ORGANIZED_DIR).iterdir():
            if not artist_path.is_dir():
                continue
                
            if self.should_reorganize(str(artist_path)):
                collaboration_artists.append(artist_path)
        
        self.log(f"Found {len(collaboration_artists)} collaboration artists to fix")
        
        # Group by primary artist
        primary_artist_map = {}
        for collab_path in collaboration_artists:
            artist_name = collab_path.name
            primary = self.extract_primary_artist(artist_name)
            
            if primary not in primary_artist_map:
                primary_artist_map[primary] = []
            primary_artist_map[primary].append(collab_path)
        
        # Move files to primary artists
        for primary_artist, collab_paths in primary_artist_map.items():
            self.log(f"Consolidating under: {primary_artist}")
            for collab_path in collab_paths:
                self.move_files_to_primary_artist(collab_path, primary_artist)
        
        # Second pass: Copy clean artists
        self.process_clean_artists()
        
        # Final statistics
        duration = (datetime.now() - self.start_time).total_seconds()
        self.log(f"Fix completed in {duration:.1f} seconds")
        self.log(f"Processed: {self.processed_count}, Moved: {self.moved_count}, Errors: {self.error_count}")
        
        # Create summary
        self.create_summary(duration)
    
    def create_summary(self, duration):
        """Create completion summary"""
        summary = {
            'processed_artists': self.processed_count,
            'moved_collaborations': self.moved_count,
            'errors': self.error_count,
            'duration_seconds': duration,
            'completed_at': datetime.now().isoformat(),
            'fixed_directory': FIXED_DIR
        }
        
        with open('/home/ebon/music_fix_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)

if __name__ == "__main__":
    fixer = MusicFixer()
    fixer.run()
