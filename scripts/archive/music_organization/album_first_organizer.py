#!/usr/bin/env python3
"""
Album-First Music Organizer
Groups music by Album name first, making it easier for Jellyfin to detect compilations
Structure: /Album Name/[Artist -] Track Title.ext
"""

import os
import sys
import json
import shutil
import subprocess
import re
from pathlib import Path
from datetime import datetime
import hashlib

# Configuration
SOURCE_DIR = "/mnt/media/music_fixed"  # Use the fixed directory as source
TARGET_DIR = "/mnt/media/music_album_organized"
LOG_FILE = "/home/ebon/album_org.log"
STATE_FILE = "/home/ebon/album_org_state.json"

class AlbumOrganizer:
    def __init__(self):
        self.processed_count = 0
        self.error_count = 0
        self.album_map = {}  # Map albums to their tracks
        self.start_time = datetime.now()
        
    def log(self, message):
        """Log message to file and stdout"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        
        with open(LOG_FILE, 'a') as f:
            f.write(log_msg + '\n')
    
    def get_metadata(self, file_path):
        """Extract metadata from audio file"""
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', file_path
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                tags = data.get('format', {}).get('tags', {})
                
                # Get all metadata
                artist = (tags.get('artist') or tags.get('ARTIST') or 
                         tags.get('albumartist') or tags.get('ALBUMARTIST') or 
                         'Unknown Artist')
                album = tags.get('album') or tags.get('ALBUM') or 'Unknown Album'
                title = tags.get('title') or tags.get('TITLE') or Path(file_path).stem
                track = tags.get('track') or tags.get('TRACK') or ''
                date = tags.get('date') or tags.get('DATE') or tags.get('year') or ''
                
                return {
                    'artist': self.clean_name(artist),
                    'album': self.clean_album_name(album),
                    'title': self.clean_name(title),
                    'track': track.split('/')[0] if '/' in track else track,
                    'year': date[:4] if date else ''
                }
        except Exception as e:
            self.log(f"Error reading metadata from {file_path}: {e}")
            
        return None
    
    def clean_name(self, name):
        """Clean names for filesystem"""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        
        # Clean up extra spaces
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Limit length
        if len(name) > 150:
            name = name[:150]
            
        return name or 'Unknown'
    
    def clean_album_name(self, album):
        """Clean and normalize album names"""
        # Remove disc/CD indicators for grouping
        album = re.sub(r'\s*[\[\(]?(CD|Disc|Disk)\s*\d+[\]\)]?\s*', '', album, flags=re.IGNORECASE)
        
        # Remove [Clean], [Explicit], etc. for grouping
        album = re.sub(r'\s*\[(Clean|Explicit|Deluxe|Edition|Remastered|Bonus)\]', '', album, flags=re.IGNORECASE)
        
        # Clean parenthetical content but keep important ones
        if '(feat' not in album.lower():
            album = re.sub(r'\s*\([^)]*\)\s*$', '', album)
        
        return self.clean_name(album)
    
    def get_album_key(self, metadata):
        """Generate unique key for album grouping"""
        album = metadata['album']
        
        # For compilations, soundtracks, greatest hits - just use album name
        lower_album = album.lower()
        if any(word in lower_album for word in ['compilation', 'soundtrack', 'greatest', 'best of', 'collection', 'various']):
            return album
        
        # For regular albums, include year if available to distinguish same-named albums
        if metadata['year']:
            return f"{album} ({metadata['year']})"
        
        return album
    
    def scan_music_files(self):
        """Scan all music files and group by album"""
        self.log("Scanning music files and grouping by album...")
        
        music_extensions = ['.mp3', '.m4a', '.flac', '.ogg', '.opus']
        
        for root, dirs, files in os.walk(SOURCE_DIR):
            for file in files:
                if any(file.lower().endswith(ext) for ext in music_extensions):
                    file_path = os.path.join(root, file)
                    
                    # Get metadata
                    metadata = self.get_metadata(file_path)
                    if not metadata:
                        # Fallback - use folder structure
                        parts = root.replace(SOURCE_DIR, '').strip('/').split('/')
                        artist = parts[0] if parts else 'Unknown Artist'
                        album = parts[1] if len(parts) > 1 else 'Unknown Album'
                        metadata = {
                            'artist': artist,
                            'album': album,
                            'title': Path(file).stem,
                            'track': '',
                            'year': ''
                        }
                    
                    # Group by album
                    album_key = self.get_album_key(metadata)
                    
                    if album_key not in self.album_map:
                        self.album_map[album_key] = []
                    
                    self.album_map[album_key].append({
                        'path': file_path,
                        'metadata': metadata,
                        'filename': file
                    })
        
        self.log(f"Found {len(self.album_map)} unique albums")
        
        # Sort tracks within each album
        for album_key in self.album_map:
            # Sort by track number if available, then by filename
            self.album_map[album_key].sort(key=lambda x: (
                int(x['metadata']['track']) if x['metadata']['track'].isdigit() else 999,
                x['metadata']['title']
            ))
    
    def organize_albums(self):
        """Create the album-based directory structure"""
        self.log("Organizing music by album...")
        
        Path(TARGET_DIR).mkdir(exist_ok=True)
        
        for album_key, tracks in self.album_map.items():
            # Create album directory
            album_dir = Path(TARGET_DIR) / album_key
            album_dir.mkdir(exist_ok=True)
            
            # Check if this is a various artists compilation
            artists = set(track['metadata']['artist'] for track in tracks)
            is_compilation = len(artists) > 3  # More than 3 artists = compilation
            
            for track_info in tracks:
                metadata = track_info['metadata']
                source_path = track_info['path']
                
                # Create filename
                if metadata['track'] and metadata['track'].isdigit():
                    track_num = metadata['track'].zfill(2)
                else:
                    track_num = None
                
                # For compilations, include artist in filename
                if is_compilation and metadata['artist'] != 'Unknown Artist':
                    if track_num:
                        filename = f"{track_num} - {metadata['artist']} - {metadata['title']}"
                    else:
                        filename = f"{metadata['artist']} - {metadata['title']}"
                else:
                    if track_num:
                        filename = f"{track_num} - {metadata['title']}"
                    else:
                        filename = metadata['title']
                
                # Add extension
                ext = Path(source_path).suffix
                filename = self.clean_name(filename) + ext
                
                target_path = album_dir / filename
                
                # Handle duplicates
                if target_path.exists():
                    base = target_path.stem
                    counter = 1
                    while target_path.exists():
                        target_path = album_dir / f"{base}_{counter}{ext}"
                        counter += 1
                
                # Copy file
                try:
                    shutil.copy2(source_path, target_path)
                    self.processed_count += 1
                    
                    if self.processed_count % 100 == 0:
                        self.log(f"Processed {self.processed_count} files...")
                    
                except Exception as e:
                    self.log(f"Error copying {source_path}: {e}")
                    self.error_count += 1
            
            # Create album info file for Jellyfin
            self.create_album_info(album_dir, tracks, is_compilation)
    
    def create_album_info(self, album_dir, tracks, is_compilation):
        """Create an info file to help Jellyfin understand the album"""
        info = {
            'album': album_dir.name,
            'track_count': len(tracks),
            'is_compilation': is_compilation
        }
        
        if not is_compilation and tracks:
            # Use first track's artist as album artist
            info['album_artist'] = tracks[0]['metadata']['artist']
        else:
            info['album_artist'] = 'Various Artists'
        
        # Get year from tracks
        years = [t['metadata']['year'] for t in tracks if t['metadata']['year']]
        if years:
            info['year'] = min(years)  # Use earliest year
        
        # Save info file
        info_file = album_dir / 'album.nfo'
        with open(info_file, 'w') as f:
            f.write(f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
            f.write(f"<album>\n")
            f.write(f"  <title>{info['album']}</title>\n")
            f.write(f"  <artist>{info['album_artist']}</artist>\n")
            if 'year' in info:
                f.write(f"  <year>{info['year']}</year>\n")
            f.write(f"  <compilation>{str(is_compilation).lower()}</compilation>\n")
            f.write(f"</album>\n")
    
    def run(self):
        """Main organization process"""
        self.log("Starting album-first organization...")
        
        # Scan and group files
        self.scan_music_files()
        
        # Organize into album structure
        self.organize_albums()
        
        # Summary
        duration = (datetime.now() - self.start_time).total_seconds()
        self.log(f"Organization complete!")
        self.log(f"Processed: {self.processed_count} files")
        self.log(f"Albums created: {len(self.album_map)}")
        self.log(f"Errors: {self.error_count}")
        self.log(f"Duration: {duration:.1f} seconds")
        
        # Save summary
        summary = {
            'processed_files': self.processed_count,
            'albums_created': len(self.album_map),
            'errors': self.error_count,
            'duration_seconds': duration,
            'completed_at': datetime.now().isoformat()
        }
        
        with open('/home/ebon/album_org_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)

if __name__ == "__main__":
    organizer = AlbumOrganizer()
    organizer.run()

    def handle_duplicates(self):
        """Move duplicate tracks to a separate folder"""
        duplicates_dir = Path(TARGET_DIR) / "_Duplicates"
        
        # Track seen files by content hash
        seen_hashes = {}
        
        for album_key, tracks in self.album_map.items():
            for track in tracks:
                # Quick hash based on artist, title, and file size
                file_stats = os.stat(track['path'])
                content_key = f"{track['metadata']['artist']}_{track['metadata']['title']}_{file_stats.st_size}"
                content_hash = hashlib.md5(content_key.encode()).hexdigest()
                
                if content_hash in seen_hashes:
                    # This is a duplicate
                    if not duplicates_dir.exists():
                        duplicates_dir.mkdir(exist_ok=True)
                    
                    # Move to duplicates folder
                    dup_path = duplicates_dir / Path(track['path']).name
                    if dup_path.exists():
                        base = dup_path.stem
                        ext = dup_path.suffix
                        counter = 1
                        while dup_path.exists():
                            dup_path = duplicates_dir / f"{base}_{counter}{ext}"
                            counter += 1
                    
                    track['duplicate'] = True
                    track['duplicate_of'] = seen_hashes[content_hash]
                    self.log(f"Found duplicate: {track['metadata']['title']} by {track['metadata']['artist']}")
                else:
                    seen_hashes[content_hash] = track['path']
                    track['duplicate'] = False

# Update the run method
AlbumOrganizer.run_original = AlbumOrganizer.run
def run_with_duplicates(self):
    self.log("Starting album-first organization with duplicate handling...")
    
    # Scan and group files
    self.scan_music_files()
    
    # Find duplicates
    self.handle_duplicates()
    
    # Filter out duplicates from album_map
    for album_key in self.album_map:
        self.album_map[album_key] = [t for t in self.album_map[album_key] if not t.get('duplicate', False)]
    
    # Remove empty albums
    self.album_map = {k: v for k, v in self.album_map.items() if v}
    
    # Organize into album structure
    self.organize_albums()
    
    # Summary
    duration = (datetime.now() - self.start_time).total_seconds()
    self.log(f"Organization complete!")
    self.log(f"Processed: {self.processed_count} files")
    self.log(f"Albums created: {len(self.album_map)}")
    self.log(f"Errors: {self.error_count}")
    self.log(f"Duration: {duration:.1f} seconds")
    
    # Save summary
    summary = {
        'processed_files': self.processed_count,
        'albums_created': len(self.album_map),
        'errors': self.error_count,
        'duration_seconds': duration,
        'completed_at': datetime.now().isoformat()
    }
    
    with open('/home/ebon/album_org_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

AlbumOrganizer.run = run_with_duplicates
AlbumOrganizer.handle_duplicates = handle_duplicates
