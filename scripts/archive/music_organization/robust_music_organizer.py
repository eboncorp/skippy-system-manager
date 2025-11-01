#!/usr/bin/env python3
"""
Robust Music Organizer with Resume Capability
Organizes music into Artist/Album/Track structure for Jellyfin
"""

import os
import sys
import json
import time
import shutil
import subprocess
import signal
from pathlib import Path
from datetime import datetime
import hashlib

# Configuration
SOURCE_DIR = "/mnt/media/music"
TARGET_DIR = "/mnt/media/music_organized"
STATE_FILE = "/home/ebon/music_org_state.json"
LOG_FILE = "/home/ebon/music_org.log"
MAX_RETRIES = 3
BATCH_SIZE = 50  # Process in batches to allow periodic state saves

class MusicOrganizer:
    def __init__(self):
        self.state = self.load_state()
        self.processed_count = 0
        self.error_count = 0
        self.start_time = time.time()
        self.setup_signal_handlers()
        
    def setup_signal_handlers(self):
        """Handle interrupts gracefully"""
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        
    def handle_shutdown(self, signum, frame):
        """Save state before shutting down"""
        self.log(f"Received shutdown signal. Saving state...")
        self.save_state()
        sys.exit(0)
        
    def load_state(self):
        """Load previous state or create new one"""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)
                    self.log(f"Resuming from previous state: {state['processed_count']} files already processed")
                    return state
            except:
                pass
        
        return {
            'processed_files': set(),
            'processed_count': 0,
            'error_files': [],
            'last_file': None,
            'start_time': datetime.now().isoformat()
        }
    
    def save_state(self):
        """Save current state to disk"""
        state_to_save = {
            'processed_files': list(self.state['processed_files']),
            'processed_count': self.processed_count,
            'error_files': self.state['error_files'],
            'last_file': self.state['last_file'],
            'start_time': self.state['start_time'],
            'last_save': datetime.now().isoformat()
        }
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state_to_save, f, indent=2)
            
    def log(self, message):
        """Log message to file and stdout"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        
        with open(LOG_FILE, 'a') as f:
            f.write(log_msg + '\n')
            
    def get_file_hash(self, filepath):
        """Get a hash of file path for tracking"""
        return hashlib.md5(filepath.encode()).hexdigest()
        
    def get_metadata(self, file_path):
        """Extract metadata from audio file using ffprobe"""
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', file_path
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                tags = data.get('format', {}).get('tags', {})
                
                # Try different tag variations
                artist = (tags.get('artist') or tags.get('ARTIST') or 
                         tags.get('albumartist') or tags.get('ALBUMARTIST') or 
                         'Unknown Artist')
                album = tags.get('album') or tags.get('ALBUM') or 'Unknown Album'
                title = tags.get('title') or tags.get('TITLE') or Path(file_path).stem
                track = tags.get('track') or tags.get('TRACK') or ''
                
                # Clean up the values
                artist = self.clean_filename(artist)
                album = self.clean_filename(album)
                title = self.clean_filename(title)
                
                return {
                    'artist': artist,
                    'album': album,
                    'title': title,
                    'track': track.split('/')[0] if '/' in track else track
                }
        except subprocess.TimeoutExpired:
            self.log(f"Timeout reading metadata from: {file_path}")
        except Exception as e:
            self.log(f"Error reading metadata from {file_path}: {e}")
            
        # Fallback
        return {
            'artist': 'Unknown Artist',
            'album': 'Unknown Album',
            'title': Path(file_path).stem,
            'track': ''
        }
    
    def clean_filename(self, name):
        """Clean filename for filesystem compatibility"""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        
        # Limit length
        if len(name) > 200:
            name = name[:200]
            
        return name.strip() or 'Unknown'
    
    def organize_file(self, source_file):
        """Organize a single file"""
        try:
            # Get metadata
            metadata = self.get_metadata(source_file)
            
            # Construct target path
            artist_dir = Path(TARGET_DIR) / metadata['artist']
            album_dir = artist_dir / metadata['album']
            
            # Create filename
            if metadata['track'] and metadata['track'].isdigit():
                track_num = metadata['track'].zfill(2)
                filename = f"{track_num} {metadata['title']}{Path(source_file).suffix}"
            else:
                filename = f"{metadata['title']}{Path(source_file).suffix}"
            
            target_file = album_dir / filename
            
            # Create directories
            album_dir.mkdir(parents=True, exist_ok=True)
            
            # Handle duplicates
            if target_file.exists():
                base = target_file.stem
                ext = target_file.suffix
                counter = 1
                while target_file.exists():
                    target_file = album_dir / f"{base}_{counter}{ext}"
                    counter += 1
            
            # Copy file
            shutil.copy2(source_file, target_file)
            
            return True, str(target_file)
            
        except Exception as e:
            self.log(f"Error organizing {source_file}: {e}")
            return False, str(e)
    
    def run(self):
        """Main organization loop"""
        self.log("Starting music organization...")
        
        # Get all music files
        music_files = []
        for ext in ['*.mp3', '*.m4a', '*.flac', '*.ogg', '*.opus']:
            music_files.extend(Path(SOURCE_DIR).glob(ext))
        
        total_files = len(music_files)
        self.log(f"Found {total_files} music files to organize")
        
        # Filter out already processed files
        files_to_process = []
        for f in music_files:
            file_hash = self.get_file_hash(str(f))
            if file_hash not in self.state['processed_files']:
                files_to_process.append(f)
        
        remaining = len(files_to_process)
        self.log(f"{remaining} files remaining to process")
        
        if remaining == 0:
            self.log("All files already processed!")
            return
        
        # Process files in batches
        batch_count = 0
        for i, source_file in enumerate(files_to_process):
            # Organize the file
            success, result = self.organize_file(str(source_file))
            
            if success:
                self.processed_count += 1
                file_hash = self.get_file_hash(str(source_file))
                self.state['processed_files'].add(file_hash)
                self.state['last_file'] = str(source_file)
                
                # Progress update
                total_processed = len(self.state['processed_files'])
                percent = (total_processed / total_files) * 100
                rate = self.processed_count / (time.time() - self.start_time)
                eta = (remaining - i) / rate if rate > 0 else 0
                
                self.log(f"[{total_processed}/{total_files}] {percent:.1f}% - Organized: {source_file.name} -> {result}")
                self.log(f"  Rate: {rate:.1f} files/sec, ETA: {eta/60:.1f} minutes")
            else:
                self.error_count += 1
                self.state['error_files'].append({
                    'file': str(source_file),
                    'error': result,
                    'timestamp': datetime.now().isoformat()
                })
                self.log(f"Failed to organize: {source_file}")
            
            batch_count += 1
            
            # Save state periodically
            if batch_count >= BATCH_SIZE:
                self.save_state()
                batch_count = 0
                self.log(f"State saved. Processed: {self.processed_count}, Errors: {self.error_count}")
        
        # Final save
        self.save_state()
        self.log(f"Organization complete! Processed: {self.processed_count}, Errors: {self.error_count}")
        
        # Create summary
        self.create_summary()
    
    def create_summary(self):
        """Create a summary of the organization"""
        summary = {
            'total_processed': len(self.state['processed_files']),
            'session_processed': self.processed_count,
            'errors': self.error_count,
            'duration_seconds': time.time() - self.start_time,
            'completed_at': datetime.now().isoformat()
        }
        
        summary_file = "/home/ebon/music_org_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.log(f"Summary saved to {summary_file}")

if __name__ == "__main__":
    organizer = MusicOrganizer()
    organizer.run()
