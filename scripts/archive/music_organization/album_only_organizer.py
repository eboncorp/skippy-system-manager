#!/usr/bin/env python3
"""
Album-Only Music Organizer
Groups ALL music by album name only, ignoring artists
This ensures complete albums stay together
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

# Use original fixed directory as source
SOURCE_DIR = "/mnt/media/music_fixed"
TARGET_DIR = "/mnt/media/music_albums_only"
LOG_FILE = "/home/ebon/album_only.log"

class AlbumOnlyOrganizer:
    def __init__(self):
        self.processed = 0
        self.errors = 0
        self.albums = defaultdict(list)  # album -> list of all tracks
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
                album = tags.get('album') or tags.get('ALBUM') or 'Unknown Album'
                title = tags.get('title') or tags.get('TITLE') or Path(file_path).stem
                track = tags.get('track') or tags.get('TRACK') or ''
                disc = tags.get('disc') or tags.get('DISC') or '1'
                
                # Clean track/disc numbers
                if '/' in str(track):
                    track = track.split('/')[0]
                if '/' in str(disc):
                    disc = disc.split('/')[0]
                
                return {
                    'artist': artist.strip(),
                    'album': album.strip(),
                    'title': title.strip(),
                    'track': track,
                    'disc': disc,
                    'file_path': file_path
                }
        except:
            pass
        
        # Fallback
        return {
            'artist': 'Unknown Artist',
            'album': 'Unknown Album',
            'title': Path(file_path).stem,
            'track': '',
            'disc': '1',
            'file_path': file_path
        }
    
    def normalize_album_name(self, album_name):
        """Normalize album names to group them properly"""
        # Remove disc/volume indicators
        normalized = re.sub(r'\s*[\[\(]?(CD|Disc|Disk|Vol\.?)\s*\d+[\]\)]?\s*', '', album_name, flags=re.IGNORECASE)
        
        # Remove edition markers
        normalized = re.sub(r'\s*\[(Clean|Explicit|Deluxe|Edition|Remastered|Bonus)\]', '', normalized, flags=re.IGNORECASE)
        normalized = re.sub(r'\s*\((Clean|Explicit|Deluxe|Edition|Remastered|Bonus)\)', '', normalized, flags=re.IGNORECASE)
        
        # Clean underscores and extra spaces
        normalized = normalized.replace('_', ' ')
        normalized = ' '.join(normalized.split())
        
        # Remove trailing punctuation
        normalized = normalized.rstrip('.')
        
        return normalized.strip()
    
    def clean_name(self, name):
        """Clean name for filesystem"""
        invalid = '<>:"/\\|?*'
        for char in invalid:
            name = name.replace(char, '')
        name = ' '.join(name.split())
        return name[:100] if len(name) > 100 else name
    
    def scan_all_music(self):
        """Scan ALL music files and group by normalized album name"""
        self.log("Scanning all music files...")
        
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
                    
                    # Normalize album name
                    album_key = self.normalize_album_name(metadata['album'])
                    
                    # Add to album collection
                    self.albums[album_key].append(metadata)
        
        self.log(f"Found {file_count} files grouped into {len(self.albums)} unique albums")
    
    def organize_by_album(self):
        """Create album-only structure"""
        self.log("Creating album-only organization...")
        
        Path(TARGET_DIR).mkdir(exist_ok=True)
        
        for album_name, tracks in self.albums.items():
            if not tracks:
                continue
            
            # Clean album name for folder
            clean_album = self.clean_name(album_name)
            
            # Skip if unknown
            if clean_album.lower() == 'unknown album':
                clean_album = 'Unknown Albums'
            
            # Create album directory
            album_dir = Path(TARGET_DIR) / clean_album
            album_dir.mkdir(exist_ok=True)
            
            # Get all unique artists for this album
            artists = set(t['artist'] for t in tracks)
            is_various = len(artists) > 3
            
            # Sort tracks by disc, then track number
            tracks.sort(key=lambda x: (
                int(x['disc']) if x['disc'].isdigit() else 1,
                int(x['track']) if x['track'].isdigit() else 999,
                x['title']
            ))
            
            # Copy tracks
            for track in tracks:
                try:
                    source = track['file_path']
                    
                    # Build filename
                    disc_num = track['disc']
                    track_num = track['track']
                    
                    # Handle multi-disc albums
                    if disc_num and disc_num != '1' and disc_num.isdigit():
                        if track_num and track_num.isdigit():
                            prefix = f"{disc_num}-{track_num.zfill(2)}"
                        else:
                            prefix = f"{disc_num}-00"
                    elif track_num and track_num.isdigit():
                        prefix = track_num.zfill(2)
                    else:
                        prefix = None
                    
                    # For various artist albums, include artist in filename
                    if is_various and track['artist'] != 'Unknown Artist':
                        if prefix:
                            filename = f"{prefix} - {track['artist']} - {track['title']}"
                        else:
                            filename = f"{track['artist']} - {track['title']}"
                    else:
                        if prefix:
                            filename = f"{prefix} - {track['title']}"
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
            
            # Create info file
            self.create_album_info(album_dir, tracks, artists)
    
    def create_album_info(self, album_dir, tracks, artists):
        """Create album info file"""
        info_file = album_dir / 'album_info.txt'
        
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write(f"Album: {album_dir.name}\n")
            f.write(f"Total Tracks: {len(tracks)}\n")
            f.write(f"Artists: {', '.join(sorted(artists))}\n")
            
            # Check for multi-disc
            discs = set(t['disc'] for t in tracks if t['disc'])
            if len(discs) > 1:
                f.write(f"Discs: {', '.join(sorted(discs))}\n")
    
    def remove_duplicates(self):
        """Move duplicate tracks to separate folder"""
        self.log("Finding and removing duplicates...")
        
        duplicates_dir = Path(TARGET_DIR) / '_Duplicates'
        dup_count = 0
        
        for album_dir in Path(TARGET_DIR).iterdir():
            if not album_dir.is_dir() or album_dir.name.startswith('_'):
                continue
            
            # Track seen files by artist+title
            seen = {}
            
            for track_file in album_dir.iterdir():
                if track_file.suffix.lower() in ['.mp3', '.m4a', '.flac']:
                    # Extract artist and title from filename
                    filename = track_file.stem
                    
                    # Remove track number
                    filename = re.sub(r'^\d+-?\d*\s*-?\s*', '', filename)
                    
                    # Create key
                    key = filename.lower()
                    
                    if key in seen:
                        # This is a duplicate
                        if not duplicates_dir.exists():
                            duplicates_dir.mkdir(exist_ok=True)
                        
                        # Move to duplicates
                        target = duplicates_dir / track_file.name
                        if target.exists():
                            target = duplicates_dir / f"{track_file.stem}_dup{track_file.suffix}"
                        
                        shutil.move(str(track_file), str(target))
                        dup_count += 1
                        self.log(f"Moved duplicate: {track_file.name}")
                    else:
                        seen[key] = track_file
        
        self.log(f"Moved {dup_count} duplicates")
    
    def create_summary(self):
        """Create final summary"""
        album_count = len([d for d in Path(TARGET_DIR).iterdir() if d.is_dir() and not d.name.startswith('_')])
        
        summary = {
            'processed_files': self.processed,
            'errors': self.errors,
            'total_albums': album_count,
            'duration': (datetime.now() - self.start_time).total_seconds()
        }
        
        with open('/home/ebon/album_only_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.log(f"Complete! {self.processed} files organized into {album_count} albums")
    
    def run(self):
        self.log("Starting album-only organization...")
        
        # Scan all music
        self.scan_all_music()
        
        # Organize by album
        self.organize_by_album()
        
        # Remove duplicates
        self.remove_duplicates()
        
        # Create summary
        self.create_summary()

if __name__ == "__main__":
    organizer = AlbumOnlyOrganizer()
    organizer.run()

    def organize_no_album_tracks(self):
        """Organize tracks with no album info into artist folders"""
        if 'Unknown Album' in self.albums or 'unknown album' in self.albums:
            self.log("Organizing tracks with no album info...")
            
            no_album_dir = Path(TARGET_DIR) / '_No Album Info'
            no_album_dir.mkdir(exist_ok=True)
            
            # Get all unknown album tracks
            unknown_tracks = self.albums.get('Unknown Album', []) + self.albums.get('unknown album', [])
            
            # Group by artist
            by_artist = defaultdict(list)
            for track in unknown_tracks:
                artist = track['artist']
                if artist.lower() == 'unknown artist':
                    artist = 'Unknown Artist'
                by_artist[artist].append(track)
            
            # Create artist folders
            for artist, tracks in by_artist.items():
                artist_dir = no_album_dir / self.clean_name(artist)
                artist_dir.mkdir(exist_ok=True)
                
                for track in tracks:
                    try:
                        source = track['file_path']
                        filename = f"{track['title']}{Path(source).suffix}"
                        filename = self.clean_name(filename)
                        target = artist_dir / filename
                        
                        # Handle duplicates
                        if target.exists():
                            base = target.stem
                            ext = target.suffix
                            counter = 1
                            while target.exists():
                                target = artist_dir / f"{base} ({counter}){ext}"
                                counter += 1
                        
                        shutil.copy2(source, target)
                        self.processed += 1
                        
                    except Exception as e:
                        self.log(f"Error processing no-album track: {e}")
                        self.errors += 1
            
            # Remove from main albums dict
            self.albums.pop('Unknown Album', None)
            self.albums.pop('unknown album', None)

# Update run method to handle no album tracks
AlbumOnlyOrganizer.run_original = AlbumOnlyOrganizer.run

def run_with_no_album_handling(self):
    self.log("Starting album-only organization with no-album handling...")
    
    # Scan all music
    self.scan_all_music()
    
    # Handle tracks with no album info first
    self.organize_no_album_tracks()
    
    # Organize remaining by album
    self.organize_by_album()
    
    # Remove duplicates
    self.remove_duplicates()
    
    # Create summary
    self.create_summary()

AlbumOnlyOrganizer.run = run_with_no_album_handling
AlbumOnlyOrganizer.organize_no_album_tracks = organize_no_album_tracks
