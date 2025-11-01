#!/usr/bin/env python3
"""
Final Music Organization Fix
- Combines all "feat" artists under main artist
- Merges multi-disc albums
- Properly handles compilations
"""

import os
import sys
import json
import shutil
import subprocess
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

SOURCE_DIR = "/mnt/media/music_jellyfin"
TARGET_DIR = "/mnt/media/music_final"
LOG_FILE = "/home/ebon/final_fix.log"

class FinalMusicFix:
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
    
    def extract_main_artist(self, artist_name):
        """Extract the main artist from feat/featuring names"""
        # Clean up the artist name
        artist_lower = artist_name.lower()
        
        # Handle various featuring patterns
        for pattern in [' feat. ', ' feat ', ' featuring ', ' ft. ', ' ft ', ' with ', ' & ', ' and ']:
            if pattern in artist_lower:
                # Return the part before the pattern
                return artist_name[:artist_lower.index(pattern)].strip()
        
        # Handle semicolon separations
        if ';' in artist_name:
            return artist_name.split(';')[0].strip()
        
        return artist_name.strip()
    
    def normalize_album_name(self, album_name):
        """Normalize album names to merge multi-disc albums"""
        # Remove disc/CD indicators
        normalized = re.sub(r'\s*[\[\(]?(CD|Disc|Disk|Vol\.?)\s*\d+[\]\)]?\s*', '', album_name, flags=re.IGNORECASE)
        
        # Remove [Clean], [Explicit], etc.
        normalized = re.sub(r'\s*\[(Clean|Explicit|Deluxe|Bonus)\]', '', normalized, flags=re.IGNORECASE)
        
        # Clean up underscores and extra spaces
        normalized = normalized.replace('_', ' ')
        normalized = ' '.join(normalized.split())
        
        return normalized.strip()
    
    def is_compilation_album(self, album_path):
        """Check if an album is a compilation based on its tracks"""
        # Count unique artists in the album
        artists = set()
        
        for track_file in album_path.iterdir():
            if track_file.suffix.lower() in ['.mp3', '.m4a', '.flac']:
                # Try to extract artist from filename if it's there
                filename = track_file.stem
                if ' - ' in filename:
                    parts = filename.split(' - ')
                    if len(parts) >= 2:
                        # Check if first part after track number is artist
                        potential_artist = parts[0]
                        # Remove track number if present
                        potential_artist = re.sub(r'^\d+\s*', '', potential_artist)
                        if potential_artist:
                            artists.add(potential_artist)
        
        # If we found many different artists in filenames, it's likely a compilation
        return len(artists) > 3
    
    def reorganize_music(self):
        """Main reorganization process"""
        self.log("Starting final music reorganization...")
        
        # Create target directory
        Path(TARGET_DIR).mkdir(exist_ok=True)
        
        # Track albums to merge
        album_groups = defaultdict(lambda: defaultdict(list))
        
        # First pass: collect all music and group by artist and normalized album
        self.log("Scanning current structure...")
        
        for artist_dir in Path(SOURCE_DIR).iterdir():
            if not artist_dir.is_dir():
                continue
            
            artist_name = artist_dir.name
            
            # Skip special folders
            if artist_name in ['_Duplicates', '.', '..']:
                continue
            
            # Extract main artist
            main_artist = self.extract_main_artist(artist_name)
            
            # Handle special cases
            if main_artist.lower() in ['various artists', 'various', 'va']:
                main_artist = 'Various Artists'
            elif 'soundtrack' in artist_name.lower() or 'ost' in artist_name.lower():
                main_artist = 'Soundtracks'
            
            # Process albums
            for album_dir in artist_dir.iterdir():
                if not album_dir.is_dir():
                    continue
                
                album_name = album_dir.name
                normalized_album = self.normalize_album_name(album_name)
                
                # Check if it's a compilation
                if self.is_compilation_album(album_dir):
                    main_artist = 'Various Artists'
                
                # Group albums
                album_groups[main_artist][normalized_album].append(album_dir)
        
        # Second pass: create new structure
        self.log("Creating new structure...")
        
        for artist, albums in album_groups.items():
            # Create artist directory
            artist_path = Path(TARGET_DIR) / self.clean_name(artist)
            artist_path.mkdir(exist_ok=True)
            
            for album_name, source_dirs in albums.items():
                # Create album directory
                album_path = artist_path / self.clean_name(album_name)
                album_path.mkdir(exist_ok=True)
                
                # Copy all tracks from all source directories
                track_counter = {}
                
                for source_dir in source_dirs:
                    self.log(f"Processing {source_dir.parent.name}/{source_dir.name}...")
                    
                    for track_file in source_dir.iterdir():
                        if track_file.suffix.lower() in ['.mp3', '.m4a', '.flac', '.ogg']:
                            try:
                                # Generate target filename
                                target_name = track_file.name
                                
                                # Handle disc numbers in filenames
                                if len(source_dirs) > 1:
                                    # Multi-disc album - prefix with disc number
                                    disc_num = 1
                                    for i, sd in enumerate(source_dirs):
                                        if sd == source_dir:
                                            disc_num = i + 1
                                            break
                                    
                                    # Extract track number if present
                                    match = re.match(r'^(\d+)', target_name)
                                    if match:
                                        track_num = match.group(1)
                                        # Convert to disc-track format
                                        new_track_num = f"{disc_num}-{track_num.zfill(2)}"
                                        target_name = re.sub(r'^\d+', new_track_num, target_name)
                                
                                target_file = album_path / target_name
                                
                                # Handle duplicates
                                if target_file.exists():
                                    base = target_file.stem
                                    ext = target_file.suffix
                                    counter = 1
                                    while target_file.exists():
                                        target_file = album_path / f"{base} ({counter}){ext}"
                                        counter += 1
                                
                                # Copy file
                                shutil.copy2(track_file, target_file)
                                self.processed += 1
                                
                            except Exception as e:
                                self.log(f"Error copying {track_file}: {e}")
                                self.errors += 1
                
                # Copy NFO files if they exist
                for source_dir in source_dirs:
                    nfo_file = source_dir / 'album.nfo'
                    if nfo_file.exists() and not (album_path / 'album.nfo').exists():
                        shutil.copy2(nfo_file, album_path / 'album.nfo')
        
        self.log(f"Reorganization complete! Processed {self.processed} files with {self.errors} errors")
    
    def clean_name(self, name):
        """Clean name for filesystem"""
        invalid = '<>:"/\\|?*'
        for char in invalid:
            name = name.replace(char, '_')
        name = ' '.join(name.split())
        return name[:150] if len(name) > 150 else name
    
    def create_summary(self):
        """Create summary of reorganization"""
        # Count final structure
        artists = len([d for d in Path(TARGET_DIR).iterdir() if d.is_dir()])
        albums = sum(1 for _ in Path(TARGET_DIR).glob('*/*/'))
        
        summary = {
            'processed_files': self.processed,
            'errors': self.errors,
            'final_artists': artists,
            'final_albums': albums,
            'duration': (datetime.now() - self.start_time).total_seconds()
        }
        
        with open('/home/ebon/final_fix_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.log(f"Summary: {artists} artists, {albums} albums")
    
    def run(self):
        self.reorganize_music()
        self.create_summary()

if __name__ == "__main__":
    fixer = FinalMusicFix()
    fixer.run()
