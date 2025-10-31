#!/usr/bin/env python3
"""
Duplicate File Finder
Version: 1.0.1
Created: 2025-10-28
Purpose: Find duplicate files by content (MD5 hash)
"""

import os
import sys
import hashlib
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def calculate_md5(filepath):
    """Calculate MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except (IOError, OSError):
        return None

def find_duplicates(search_dir):
    """Find all duplicate files in directory"""
    print(f"=== Duplicate File Finder ===")
    print(f"Searching in: {search_dir}")
    print()

    # Collect files
    print("[1/3] Finding all files...")
    files_by_hash = defaultdict(list)
    files_by_size = defaultdict(list)
    total_files = 0

    for root, dirs, files in os.walk(search_dir):
        # Skip certain directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]

        for filename in files:
            if filename.startswith('.'):
                continue

            filepath = Path(root) / filename
            try:
                size = filepath.stat().st_size
                files_by_size[size].append(filepath)
                total_files += 1
            except (IOError, OSError):
                continue

    print(f"Found {total_files} files to analyze")

    # Calculate hashes only for files with same size
    print("[2/3] Calculating MD5 hashes for files with matching sizes...")
    candidates = sum(1 for files in files_by_size.values() if len(files) > 1)
    print(f"Found {candidates} file size groups with potential duplicates")

    processed = 0
    for size, filepaths in files_by_size.items():
        if len(filepaths) > 1:
            # Only hash files that have potential duplicates (same size)
            for filepath in filepaths:
                md5 = calculate_md5(filepath)
                if md5:
                    files_by_hash[md5].append((filepath, size))
                processed += 1
                if processed % 100 == 0:
                    print(f"  Processed {processed} files...")

    # Find duplicates
    print("[3/3] Identifying duplicates...")
    duplicates = {md5: files for md5, files in files_by_hash.items() if len(files) > 1}

    print()
    print("=" * 70)
    print("DUPLICATE FILES REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Search Directory: {search_dir}")
    print("=" * 70)
    print()
    print(f"Summary:")
    print(f"  Total files scanned: {total_files}")
    print(f"  Duplicate groups found: {len(duplicates)}")
    print()

    if not duplicates:
        print("No duplicates found!")
        return

    # Calculate statistics
    total_wasted = 0
    total_duplicates = 0

    duplicate_list = []
    for md5, files in duplicates.items():
        size = files[0][1]
        wasted = size * (len(files) - 1)
        total_wasted += wasted
        total_duplicates += len(files) - 1
        duplicate_list.append((md5, files, size, wasted))

    # Sort by wasted space (most first)
    duplicate_list.sort(key=lambda x: x[3], reverse=True)

    print("=" * 70)
    print()

    # Show top 20 duplicate groups by wasted space
    print("Top 20 Duplicate Groups by Wasted Space:")
    print()

    for i, (md5, files, size, wasted) in enumerate(duplicate_list[:20], 1):
        print(f"Duplicate Group #{i}")
        print(f"  MD5: {md5}")
        print(f"  File size: {size:,} bytes ({size/1024:.1f} KB)")
        print(f"  Copies: {len(files)}")
        print(f"  Wasted space: {wasted:,} bytes ({wasted/1024:.1f} KB)")
        print(f"  Files:")
        for filepath, _ in files:
            print(f"    - {filepath}")
        print()

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total duplicate files: {total_duplicates}")
    print(f"Total wasted space: {total_wasted:,} bytes")
    print(f"  = {total_wasted/1024:.1f} KB")
    print(f"  = {total_wasted/1024/1024:.1f} MB")
    print(f"  = {total_wasted/1024/1024/1024:.2f} GB")
    print("=" * 70)

    # Save full report
    report_file = f"/tmp/duplicate_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("COMPLETE DUPLICATE FILES REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Search Directory: {search_dir}\n")
        f.write("=" * 70 + "\n\n")

        for i, (md5, files, size, wasted) in enumerate(duplicate_list, 1):
            f.write(f"\nDuplicate Group #{i}\n")
            f.write(f"  MD5: {md5}\n")
            f.write(f"  File size: {size:,} bytes ({size/1024:.1f} KB)\n")
            f.write(f"  Copies: {len(files)}\n")
            f.write(f"  Wasted space: {wasted:,} bytes ({wasted/1024:.1f} KB)\n")
            f.write(f"  Files:\n")
            for filepath, _ in files:
                f.write(f"    - {filepath}\n")
            f.write("\n")

        f.write("=" * 70 + "\n")
        f.write("SUMMARY\n")
        f.write("=" * 70 + "\n")
        f.write(f"Total duplicate files: {total_duplicates}\n")
        f.write(f"Total wasted space: {total_wasted:,} bytes ({total_wasted/1024/1024:.1f} MB)\n")

    print()
    print(f"Full report saved to: {report_file}")

if __name__ == '__main__':
    search_dir = sys.argv[1] if len(sys.argv) > 1 else '/home/dave/skippy'
    find_duplicates(search_dir)
