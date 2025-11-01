#!/usr/bin/env python3
"""
Complete Music Deduplication Script
- Compares ALL music files across the system
- Moves duplicates to /mnt/media/DUPLICATES folder
- Only converts WMA if no matching MP3 exists
- Preserves highest quality version
"""

import os
import sys
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
import re
import subprocess
import json

# All source directories
SOURCE_DIRS = [
    "/home/ebon/Music",
    "/mnt/media/music", 
    "/home/ebon/music_archived_20250816",
    "/home/ebon/music_archived_20250817"
]

DUPLICATES_DIR = "/mnt/media/DUPLICATES"
LOG_FILE = "/home/ebon/dedup.log"
COMPLETE_MUSIC_DIR = "/mnt/media/COMPLETE_MUSIC_LIBRARY"

class MusicDeduplicator:
    def __init__(self):
        self.processed = 0
        self.duplicates_moved = 0
        self.wma_converted = 0
        self.music_map = {}  # key -> best file info
        self.start_time = datetime.now()
        
    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        with open(LOG_FILE, 'a') as f:
            f.write(log_msg + '\n')
    
    def get_file_key(self, filepath):
        """Generate key for duplicate detection based on filename"""
        filename = Path(filepath).stem
        
        # Remove common prefixes (track numbers, disc numbers)
        key = re.sub(r'^(\d+-?)?\d+\s*-?\s*', '', filename)
        
        # Remove featuring/feat variations
        key = re.sub(r'\s+(feat\.?|featuring|ft\.?|with)\s+.*', '', key, flags=re.IGNORECASE)
        
        # Remove parenthetical content
        key = re.sub(r'\s*\([^)]*\)', '', key)
        key = re.sub(r'\s*\[[^\]]*\]', '', key)
        
        # Clean up
        key = key.lower().strip()
        key = re.sub(r'[^\w\s]', '', key)
        key = ' '.join(key.split())
        
        return key
    
    def get_quality_score(self, filepath):
        """Assign quality score to determine best version"""
        ext = Path(filepath).suffix.lower()
        
        # File format priority (higher is better)
        format_scores = {
            '.flac': 100,
            '.m4a': 80, 
            '.mp3': 70,
            '.wma': 40,
            '.ogg': 60,
            '.opus': 60
        }
        
        score = format_scores.get(ext, 0)
        
        # Bonus for file size (larger usually means better quality)
        try:
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            score += min(size_mb / 10, 20)  # Up to 20 bonus points
        except:
            pass
        
        return score
    
    def scan_all_music(self):
        """Scan all music files and find the best version of each"""
        self.log("Scanning ALL music files for duplicates...")
        
        extensions = ['.mp3', '.m4a', '.flac', '.wma', '.ogg', '.opus']
        
        for source_dir in SOURCE_DIRS:
            if not os.path.exists(source_dir):
                continue
                
            self.log(f"Scanning {source_dir}...")
            
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in extensions):
                        filepath = os.path.join(root, file)
                        
                        # Generate key
                        key = self.get_file_key(filepath)
                        if not key:  # Skip if no meaningful key
                            continue
                        
                        # Get quality score
                        score = self.get_quality_score(filepath)
                        
                        # Store info
                        file_info = {
                            'path': filepath,
                            'score': score,
                            'ext': Path(filepath).suffix.lower(),
                            'size': os.path.getsize(filepath)
                        }
                        
                        if key in self.music_map:
                            # Compare with existing
                            if score > self.music_map[key]['score']:
                                # This is better, mark old as duplicate
                                self.music_map[key] = file_info
                            # else: keep existing, this one will be marked as duplicate
                        else:
                            self.music_map[key] = file_info
                        
                        self.processed += 1
                        if self.processed % 1000 == 0:
                            self.log(f"Processed {self.processed} files, found {len(self.music_map)} unique tracks...")
        
        self.log(f"Scan complete: {self.processed} files -> {len(self.music_map)} unique tracks")
    
    def move_duplicates_and_organize(self):
        """Move duplicates and organize remaining music"""
        self.log("Moving duplicates and organizing music...")
        
        # Create directories
        Path(DUPLICATES_DIR).mkdir(exist_ok=True)
        Path(COMPLETE_MUSIC_DIR).mkdir(exist_ok=True)
        
        # Get all keepers
        keepers = set(info['path'] for info in self.music_map.values())
        
        # Process all files again
        for source_dir in SOURCE_DIRS:
            if not os.path.exists(source_dir):
                continue
                
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in ['.mp3', '.m4a', '.flac', '.wma', '.ogg', '.opus']):
                        filepath = os.path.join(root, file)
                        
                        if filepath in keepers:
                            # This is a keeper - copy to main library
                            filename = os.path.basename(filepath)
                            target = os.path.join(COMPLETE_MUSIC_DIR, filename)
                            
                            # Handle filename conflicts
                            if os.path.exists(target):
                                base = Path(filename).stem
                                ext = Path(filename).suffix
                                counter = 1
                                while os.path.exists(target):
                                    target = os.path.join(COMPLETE_MUSIC_DIR, f"{base}_{counter}{ext}")
                                    counter += 1
                            
                            shutil.copy2(filepath, target)
                        else:
                            # This is a duplicate - move to duplicates
                            key = self.get_file_key(filepath)
                            if key and key in self.music_map:  # Only move if we have a better version
                                filename = os.path.basename(filepath)
                                dup_target = os.path.join(DUPLICATES_DIR, filename)
                                
                                # Handle conflicts in duplicates folder
                                if os.path.exists(dup_target):
                                    base = Path(filename).stem
                                    ext = Path(filename).suffix
                                    counter = 1
                                    while os.path.exists(dup_target):
                                        dup_target = os.path.join(DUPLICATES_DIR, f"{base}_dup{counter}{ext}")
                                        counter += 1
                                
                                shutil.copy2(filepath, dup_target)
                                self.duplicates_moved += 1
                                
                                if self.duplicates_moved % 100 == 0:
                                    self.log(f"Moved {self.duplicates_moved} duplicates...")
    
    def handle_wma_conversion(self):
        """Convert WMA files only if no MP3 equivalent exists"""
        self.log("Checking WMA files for conversion...")
        
        wma_files = []
        mp3_files = set()
        
        # Collect all files in complete library
        for file in os.listdir(COMPLETE_MUSIC_DIR):
            if file.lower().endswith('.wma'):
                wma_files.append(file)
            elif file.lower().endswith('.mp3'):
                # Store the stem (filename without extension)
                mp3_files.add(Path(file).stem.lower())
        
        # Convert WMA files that don't have MP3 equivalents
        for wma_file in wma_files:
            wma_stem = Path(wma_file).stem.lower()
            
            if wma_stem not in mp3_files:
                self.log(f"Converting WMA (no MP3 equivalent): {wma_file}")
                
                wma_path = os.path.join(COMPLETE_MUSIC_DIR, wma_file)
                mp3_path = os.path.join(COMPLETE_MUSIC_DIR, f"{Path(wma_file).stem}.mp3")
                
                try:
                    # Convert with ffmpeg
                    result = subprocess.run([
                        'ffmpeg', '-i', wma_path, 
                        '-acodec', 'libmp3lame', '-ab', '320k',
                        '-map_metadata', '0', mp3_path, '-y'
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        # Remove original WMA
                        os.remove(wma_path)
                        self.wma_converted += 1
                        self.log(f"Successfully converted: {wma_file}")
                    else:
                        self.log(f"Failed to convert: {wma_file}")
                        
                except Exception as e:
                    self.log(f"Error converting {wma_file}: {e}")
    
    def create_summary(self):
        """Create final summary"""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        # Count final results
        final_count = len([f for f in os.listdir(COMPLETE_MUSIC_DIR) 
                          if any(f.lower().endswith(ext) for ext in ['.mp3', '.m4a', '.flac'])])
        
        duplicate_count = len([f for f in os.listdir(DUPLICATES_DIR)
                              if any(f.lower().endswith(ext) for ext in ['.mp3', '.m4a', '.flac', '.wma'])])
        
        summary = {
            'total_processed': self.processed,
            'unique_tracks': len(self.music_map),
            'duplicates_moved': duplicate_count,
            'wma_converted': self.wma_converted,
            'final_library_count': final_count,
            'duration_minutes': duration / 60,
            'completed_at': datetime.now().isoformat()
        }
        
        with open('/home/ebon/dedup_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.log(f"=== DEDUPLICATION COMPLETE ===")
        self.log(f"Processed: {self.processed} files")
        self.log(f"Unique tracks: {len(self.music_map)}")
        self.log(f"Duplicates moved: {duplicate_count}")
        self.log(f"WMA converted: {self.wma_converted}")
        self.log(f"Final library: {final_count} files")
        self.log(f"Duration: {duration/60:.1f} minutes")
    
    def run(self):
        self.log("=== Starting Complete Music Deduplication ===")
        
        # Step 1: Scan all music
        self.scan_all_music()
        
        # Step 2: Move duplicates and organize
        self.move_duplicates_and_organize()
        
        # Step 3: Handle WMA conversion
        self.handle_wma_conversion()
        
        # Step 4: Create summary
        self.create_summary()

if __name__ == "__main__":
    deduplicator = MusicDeduplicator()
    deduplicator.run()
