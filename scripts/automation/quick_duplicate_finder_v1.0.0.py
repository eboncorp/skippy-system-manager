#!/usr/bin/env python3
"""
Quick Duplicate File Finder - Command Line Version
Finds and organizes ALL duplicate files system-wide
"""

import os
import sys
import hashlib
import shutil
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import argparse

class QuickDuplicateFinder:
    def __init__(self):
        self.duplicates = defaultdict(list)
        self.processed = 0
        
    def get_file_hash(self, file_path, block_size=65536):
        """Calculate SHA256 hash of file"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(block_size)
                    if not data:
                        break
                    hasher.update(data)
            return hasher.hexdigest()
        except (IOError, OSError, PermissionError):
            return None
    
    def format_size(self, size_bytes):
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def should_skip_path(self, path_str):
        """Skip system and cache directories"""
        skip_patterns = [
            '/.cache/', '/.local/share/Trash/', '/.git/', 
            '/__pycache__/', '/.steam/', '/snap/',
            '/.config/google-chrome/', '/.config/BraveSoftware/',
            '/vfs/', '/vfsMeta/', '/.vscode/', '/node_modules/'
        ]
        return any(pattern in path_str for pattern in skip_patterns)
    
    def find_duplicates(self, scan_dir, min_size_kb=1, extensions=None):
        """Find duplicate files"""
        print(f"🔍 Scanning {scan_dir} for duplicates...")
        
        scan_path = Path(scan_dir)
        if not scan_path.exists():
            print(f"❌ Directory {scan_dir} does not exist!")
            return
        
        file_hashes = {}
        min_size = min_size_kb * 1024
        
        # Find all files
        try:
            for file_path in scan_path.rglob('*'):
                try:
                    if not file_path.is_file():
                        continue
                    
                    # Skip system paths
                    if self.should_skip_path(str(file_path)):
                        continue
                    
                    # Check size
                    file_size = file_path.stat().st_size
                    if file_size < min_size:
                        continue
                    
                    # Check extension
                    if extensions and file_path.suffix.lower() not in extensions:
                        continue
                    
                    # Calculate hash
                    file_hash = self.get_file_hash(file_path)
                    if file_hash:
                        if file_hash in file_hashes:
                            file_hashes[file_hash].append((file_path, file_size))
                        else:
                            file_hashes[file_hash] = [(file_path, file_size)]
                    
                    self.processed += 1
                    if self.processed % 500 == 0:
                        print(f"  📄 Processed {self.processed:,} files...")
                        
                except (PermissionError, OSError):
                    continue
                    
        except KeyboardInterrupt:
            print("\n⏹️  Scan interrupted by user")
            
        # Find duplicates
        total_duplicate_size = 0
        duplicate_files = 0
        
        for file_hash, files in file_hashes.items():
            if len(files) > 1:
                self.duplicates[file_hash] = files
                # Calculate wasted space (all except one)
                file_size = files[0][1]
                total_duplicate_size += file_size * (len(files) - 1)
                duplicate_files += len(files) - 1
        
        print(f"\n📊 SCAN RESULTS:")
        print(f"   Files processed: {self.processed:,}")
        print(f"   Duplicate groups: {len(self.duplicates):,}")
        print(f"   Duplicate files: {duplicate_files:,}")
        print(f"   Wasted space: {self.format_size(total_duplicate_size)}")
        
        return self.duplicates
    
    def analyze_duplicates(self):
        """Analyze types of duplicates found"""
        if not self.duplicates:
            return
        
        print(f"\n📈 DUPLICATE ANALYSIS:")
        
        # Categorize by type
        categories = defaultdict(lambda: {'count': 0, 'size': 0})
        
        for files in self.duplicates.values():
            for file_path, file_size in files:
                ext = file_path.suffix.lower()
                
                if 'eth' in str(file_path).lower() or 'ethereum' in str(file_path).lower():
                    cat = 'Ethereum/Blockchain'
                elif ext in ['.sh', '.py', '.js', '.pl']:
                    cat = 'Scripts'
                elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp']:
                    cat = 'Images'
                elif ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv']:
                    cat = 'Videos'
                elif ext in ['.mp3', '.wav', '.flac', '.ogg']:
                    cat = 'Audio'
                elif ext in ['.pdf', '.doc', '.docx', '.txt', '.md']:
                    cat = 'Documents'
                elif ext in ['.zip', '.tar', '.gz', '.rar', '.7z']:
                    cat = 'Archives'
                else:
                    cat = 'Other'
                
                categories[cat]['count'] += 1
                categories[cat]['size'] += file_size
        
        # Sort by wasted space
        for cat, data in sorted(categories.items(), key=lambda x: x[1]['size'], reverse=True):
            print(f"   {cat}: {data['count']:,} files, {self.format_size(data['size'])} wasted")
    
    def show_top_duplicates(self, limit=20):
        """Show top duplicate groups by size"""
        if not self.duplicates:
            return
        
        print(f"\n🔝 TOP {limit} DUPLICATE GROUPS BY SIZE:")
        
        # Sort by file size
        sorted_dupes = sorted(self.duplicates.items(), 
                             key=lambda x: x[1][0][1], reverse=True)
        
        for i, (file_hash, files) in enumerate(sorted_dupes[:limit], 1):
            file_size = files[0][1]
            wasted_size = file_size * (len(files) - 1)
            first_file = files[0][0]
            
            print(f"\n{i:2d}. {first_file.name}")
            print(f"    Size: {self.format_size(file_size)} x {len(files)} copies = {self.format_size(wasted_size)} wasted")
            print(f"    Locations:")
            
            for file_path, _ in files[:5]:  # Show first 5 locations
                print(f"      • {file_path}")
            if len(files) > 5:
                print(f"      • ... and {len(files) - 5} more")
    
    def create_cleanup_script(self, output_file="cleanup_duplicates.sh"):
        """Create a cleanup script"""
        if not self.duplicates:
            print("❌ No duplicates found to clean up!")
            return
        
        script_path = Path.home() / output_file
        
        with open(script_path, 'w') as f:
            f.write(f"""#!/bin/bash
# Duplicate File Cleanup Script
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Found {len(self.duplicates)} duplicate groups

set -euo pipefail

echo "🧹 Starting duplicate cleanup..."

BACKUP_DIR="$HOME/DuplicateBackup/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 Creating backup in $BACKUP_DIR"

REMOVED_COUNT=0
FREED_SPACE=0

""")
            
            # Generate removal commands
            for file_hash, files in self.duplicates.items():
                # Sort by modification time (keep newest)
                files_sorted = sorted(files, key=lambda x: x[0].stat().st_mtime, reverse=True)
                
                f.write(f"\n# Group: {files_sorted[0][0].name}\n")
                f.write(f"# Hash: {file_hash[:16]}...\n")
                
                # Keep the first (newest) file, remove the rest
                for file_path, file_size in files_sorted[1:]:
                    safe_path = str(file_path).replace("'", "'\"'\"'")  # Escape single quotes
                    f.write(f"if [ -f '{safe_path}' ]; then\n")
                    f.write(f"    cp '{safe_path}' '$BACKUP_DIR/'\n")
                    f.write(f"    rm '{safe_path}'\n")
                    f.write(f"    echo \"Removed: {safe_path}\"\n")
                    f.write(f"    REMOVED_COUNT=$((REMOVED_COUNT + 1))\n")
                    f.write(f"    FREED_SPACE=$((FREED_SPACE + {file_size}))\n")
                    f.write(f"fi\n\n")
            
            f.write(f"""
echo "✅ Cleanup complete!"
echo "   Removed: $REMOVED_COUNT files"
echo "   Freed: $(numfmt --to=iec $FREED_SPACE)"
echo "   Backup: $BACKUP_DIR"
""")
        
        os.chmod(script_path, 0o755)
        print(f"\n💾 Cleanup script created: {script_path}")
        print(f"   Run with: bash {script_path}")
        print(f"   (Creates backup before removing duplicates)")

def main():
    parser = argparse.ArgumentParser(description="Find and organize duplicate files")
    parser.add_argument('directory', nargs='?', default=str(Path.home()), 
                       help='Directory to scan (default: home directory)')
    parser.add_argument('--min-size', type=int, default=10, 
                       help='Minimum file size in KB (default: 10)')
    parser.add_argument('--extensions', 
                       help='Comma-separated list of extensions (e.g., .jpg,.png,.pdf)')
    parser.add_argument('--create-script', action='store_true',
                       help='Create cleanup script instead of just analyzing')
    parser.add_argument('--show-top', type=int, default=20,
                       help='Number of top duplicates to show (default: 20)')
    
    args = parser.parse_args()
    
    # Parse extensions
    extensions = None
    if args.extensions:
        extensions = [ext.strip().lower() for ext in args.extensions.split(',')]
        if not all(ext.startswith('.') for ext in extensions):
            extensions = ['.' + ext if not ext.startswith('.') else ext for ext in extensions]
    
    finder = QuickDuplicateFinder()
    
    print("🚀 DUPLICATE FILE FINDER")
    print("=" * 50)
    
    # Find duplicates
    finder.find_duplicates(args.directory, args.min_size, extensions)
    
    if finder.duplicates:
        # Analyze results
        finder.analyze_duplicates()
        finder.show_top_duplicates(args.show_top)
        
        if args.create_script:
            finder.create_cleanup_script()
        else:
            print(f"\n💡 TIP: Run with --create-script to generate cleanup script")
    else:
        print("\n✨ No duplicates found!")

if __name__ == "__main__":
    main()