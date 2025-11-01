#!/usr/bin/env python3
"""
Smart Music Organizer for Jellyfin
Organizes music in a way that Jellyfin can properly understand:
- Single artist albums: /Artist/Album/tracks
- Compilations: /Various Artists/Album/tracks
- Soundtracks: /Soundtracks/Album/tracks
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

# Configuration
SOURCE_DIR = "/mnt/media/music_fixed"
TARGET_DIR = "/mnt/media/music_jellyfin"
LOG_FILE = "/home/ebon/smart_org.log"

class SmartMusicOrganizer:
    def __init__(self):
        self.processed = 0
        self.errors = 0
        self.albums = defaultdict(list)  # album -> list of tracks
        self.start_time = datetime.now()
        
    def log(self, message):
        """Log message"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        with open(LOG_FILE, 'a') as f:
            f.write(log_msg + '\n')
    
    def get_metadata(self, file_path):
        """Extract metadata using ffprobe"""
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                tags = data.get('format', {}).get('tags', {})
                
                # Get metadata with fallbacks
                artist = tags.get('artist') or tags.get('ARTIST') or ''
                album_artist = tags.get('albumartist') or tags.get('ALBUMARTIST') or tags.get('album_artist') or ''
                album = tags.get('album') or tags.get('ALBUM') or 'Unknown Album'
                title = tags.get('title') or tags.get('TITLE') or Path(file_path).stem
                track = tags.get('track') or tags.get('TRACK') or ''
                genre = tags.get('genre') or tags.get('GENRE') or ''
                
                # Clean up track number
                if '/' in str(track):
                    track = track.split('/')[0]
                
                return {
                    'artist': artist.strip(),
                    'album_artist': album_artist.strip(),
                    'album': album.strip(),
                    'title': title.strip(),
                    'track': track,
                    'genre': genre.strip(),
                    'file_path': file_path
                }
        except:
            pass
        
        # Fallback to filename parsing
        return {
            'artist': 'Unknown Artist',
            'album_artist': '',
            'album': 'Unknown Album',
            'title': Path(file_path).stem,
            'track': '',
            'genre': '',
            'file_path': file_path
        }
    
    def clean_name(self, name):
        """Clean name for filesystem"""
        # Remove invalid characters
        invalid = '<>:"/\\|?*'
        for char in invalid:
            name = name.replace(char, '_')
        
        # Clean up whitespace
        name = ' '.join(name.split())
        
        # Limit length
        if len(name) > 100:
            name = name[:100]
        
        return name or 'Unknown'
    
    def determine_album_type(self, tracks):
        """Determine if album is compilation, soundtrack, or single artist"""
        if not tracks:
            return 'single', 'Unknown Artist'
        
        # Check album name for hints
        album_name = tracks[0]['album'].lower()
        
        # Soundtrack detection
        soundtrack_keywords = ['soundtrack', 'ost', 'motion picture', 'score']
        if any(keyword in album_name for keyword in soundtrack_keywords):
            return 'soundtrack', 'Soundtracks'
        
        # Get unique artists
        artists = set()
        for track in tracks:
            # Use album_artist if available, otherwise artist
            artist = track['album_artist'] or track['artist']
            if artist and artist != 'Various Artists':
                artists.add(artist)
        
        # Compilation detection
        if len(artists) > 3:  # More than 3 different artists
            return 'compilation', 'Various Artists'
        
        # Check for "Various Artists" in album artist
        if any(track['album_artist'].lower() == 'various artists' for track in tracks):
            return 'compilation', 'Various Artists'
        
        # Single artist or small collaboration
        if len(artists) == 1:
            return 'single', list(artists)[0]
        elif len(artists) <= 3:
            # For 2-3 artists, use the most frequent one
            artist_counts = defaultdict(int)
            for track in tracks:
                artist = track['album_artist'] or track['artist']
                if artist:
                    artist_counts[artist] += 1
            
            if artist_counts:
                main_artist = max(artist_counts, key=artist_counts.get)
                return 'single', main_artist
        
        return 'compilation', 'Various Artists'
    
    def scan_music(self):
        """Scan all music files and group by album"""
        self.log("Scanning music library...")
        
        extensions = ['.mp3', '.m4a', '.flac', '.ogg', '.opus']
        file_count = 0
        
        for root, dirs, files in os.walk(SOURCE_DIR):
            for file in files:
                if any(file.lower().endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    file_count += 1
                    
                    if file_count % 100 == 0:
                        self.log(f"Scanned {file_count} files...")
                    
                    metadata = self.get_metadata(file_path)
                    
                    # Group by album
                    album_key = metadata['album']
                    self.albums[album_key].append(metadata)
        
        self.log(f"Found {file_count} music files in {len(self.albums)} albums")
    
    def organize_music(self):
        """Organize music into proper structure"""
        self.log("Organizing music library...")
        
        # Create target directory
        Path(TARGET_DIR).mkdir(exist_ok=True)
        
        for album_name, tracks in self.albums.items():
            if not tracks:
                continue
            
            # Determine album type and main artist
            album_type, main_artist = self.determine_album_type(tracks)
            
            # Clean names
            clean_artist = self.clean_name(main_artist)
            clean_album = self.clean_name(album_name)
            
            # Create directory structure
            if album_type == 'soundtrack':
                album_dir = Path(TARGET_DIR) / 'Soundtracks' / clean_album
            elif album_type == 'compilation':
                album_dir = Path(TARGET_DIR) / 'Various Artists' / clean_album
            else:
                album_dir = Path(TARGET_DIR) / clean_artist / clean_album
            
            album_dir.mkdir(parents=True, exist_ok=True)
            
            # Sort tracks by track number
            tracks.sort(key=lambda x: (
                int(x['track']) if x['track'].isdigit() else 999,
                x['title']
            ))
            
            # Copy tracks
            for track in tracks:
                try:
                    source = track['file_path']
                    
                    # Build filename
                    track_num = track['track']
                    if track_num and track_num.isdigit():
                        track_num = track_num.zfill(2)
                    else:
                        track_num = None
                    
                    # For compilations/soundtracks, include artist in filename
                    if album_type in ['compilation', 'soundtrack'] and track['artist']:
                        if track_num:
                            filename = f"{track_num} - {track['artist']} - {track['title']}"
                        else:
                            filename = f"{track['artist']} - {track['title']}"
                    else:
                        if track_num:
                            filename = f"{track_num} - {track['title']}"
                        else:
                            filename = track['title']
                    
                    # Clean and add extension
                    filename = self.clean_name(filename) + Path(source).suffix
                    target = album_dir / filename
                    
                    # Handle duplicates
                    if target.exists():
                        base = target.stem
                        ext = target.suffix
                        counter = 1
                        while target.exists():
                            target = album_dir / f"{base} ({counter}){ext}"
                            counter += 1
                    
                    # Copy file
                    shutil.copy2(source, target)
                    self.processed += 1
                    
                    if self.processed % 100 == 0:
                        self.log(f"Processed {self.processed} files...")
                    
                except Exception as e:
                    self.log(f"Error processing {track.get('title', 'unknown')}: {e}")
                    self.errors += 1
            
            # Create album.nfo for Jellyfin
            self.create_album_nfo(album_dir, tracks, album_type, main_artist)
    
    def create_album_nfo(self, album_dir, tracks, album_type, main_artist):
        """Create NFO file for Jellyfin metadata"""
        nfo_path = album_dir / 'album.nfo'
        
        album_name = album_dir.name
        
        with open(nfo_path, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<album>\n')
            f.write(f'  <title>{album_name}</title>\n')
            f.write(f'  <albumartist>{main_artist}</albumartist>\n')
            
            if album_type == 'compilation':
                f.write('  <compilation>true</compilation>\n')
            
            # Add genre if consistent across tracks
            genres = set(t['genre'] for t in tracks if t['genre'])
            if len(genres) == 1:
                f.write(f'  <genre>{list(genres)[0]}</genre>\n')
            
            f.write('</album>\n')
    
    def create_summary(self):
        """Create organization summary"""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        # Count final structure
        artist_dirs = len([d for d in Path(TARGET_DIR).iterdir() if d.is_dir()])
        album_count = sum(1 for _ in Path(TARGET_DIR).glob('*/*/'))
        
        summary = {
            'processed_files': self.processed,
            'errors': self.errors,
            'artist_folders': artist_dirs,
            'total_albums': album_count,
            'duration_seconds': duration,
            'completed_at': datetime.now().isoformat()
        }
        
        summary_path = '/home/ebon/smart_org_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.log(f"Organization complete!")
        self.log(f"Processed: {self.processed} files")
        self.log(f"Artists: {artist_dirs}")
        self.log(f"Albums: {album_count}")
        self.log(f"Errors: {self.errors}")
        self.log(f"Duration: {duration:.1f} seconds")
    
    def run(self):
        """Main process"""
        self.log("Starting smart music organization...")
        
        # Scan music
        self.scan_music()
        
        # Organize
        self.organize_music()
        
        # Create summary
        self.create_summary()

if __name__ == "__main__":
    organizer = SmartMusicOrganizer()
    organizer.run()

    def find_duplicates(self):
        """Find and mark duplicate tracks"""
        self.log("Finding duplicates...")
        
        # Track seen songs by hash of artist+title+duration
        seen = {}
        duplicates = []
        
        for album_name, tracks in self.albums.items():
            for track in tracks:
                # Create unique key
                key = f"{track['artist']}_{track['title']}".lower()
                
                if key in seen:
                    # This is a duplicate
                    duplicates.append(track)
                    track['is_duplicate'] = True
                    self.log(f"Duplicate found: {track['artist']} - {track['title']}")
                else:
                    seen[key] = track
                    track['is_duplicate'] = False
        
        # Move duplicates to separate folder
        if duplicates:
            dup_dir = Path(TARGET_DIR) / '_Duplicates'
            dup_dir.mkdir(exist_ok=True)
            
            for dup in duplicates:
                try:
                    source = dup['file_path']
                    filename = f"{dup['artist']} - {dup['title']}{Path(source).suffix}"
                    filename = self.clean_name(filename)
                    target = dup_dir / filename
                    
                    # Handle multiple duplicates with same name
                    if target.exists():
                        base = target.stem
                        ext = target.suffix
                        counter = 1
                        while target.exists():
                            target = dup_dir / f"{base} ({counter}){ext}"
                            counter += 1
                    
                    shutil.copy2(source, target)
                    self.log(f"Moved duplicate to: {target.name}")
                    
                except Exception as e:
                    self.log(f"Error moving duplicate: {e}")
        
        # Remove duplicates from albums
        for album_name in self.albums:
            self.albums[album_name] = [t for t in self.albums[album_name] if not t.get('is_duplicate', False)]
        
        self.log(f"Found and moved {len(duplicates)} duplicates")
        return len(duplicates)

# Update run method to include duplicate handling
SmartMusicOrganizer.run_original = SmartMusicOrganizer.run

def run_with_duplicates(self):
    """Main process with duplicate handling"""
    self.log("Starting smart music organization with duplicate removal...")
    
    # Scan music
    self.scan_music()
    
    # Find and remove duplicates
    dup_count = self.find_duplicates()
    
    # Organize remaining music
    self.organize_music()
    
    # Create summary
    self.create_summary()

SmartMusicOrganizer.run = run_with_duplicates
SmartMusicOrganizer.find_duplicates = find_duplicates
