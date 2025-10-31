#!/usr/bin/env python3
"""
Fast Drive Scanner - Shows progress and scans efficiently
"""

import os
from pathlib import Path
from datetime import datetime
import json

class FastDriveScanner:
    def __init__(self):
        self.home = Path.home()
        
        # All locations to scan
        self.scan_locations = [
            ("Local Documents", self.home / "Documents"),
            ("Local Downloads", self.home / "Downloads"), 
            ("Local Desktop", self.home / "Desktop"),
            ("Local Pictures", self.home / "Pictures"),
            ("Local Scans", self.home / "Scans"),
            ("OneDrive Cloud", self.home / "OneDrive"),
            ("Dropbox Cloud", self.home / "Dropbox"),
            ("Google Drive Cloud", self.home / "GoogleDrive")
        ]
        
        # File types to count
        self.file_extensions = {
            'Documents': ['.pdf', '.doc', '.docx', '.txt', '.odt'],
            'Spreadsheets': ['.xls', '.xlsx', '.csv', '.ods'],
            'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'],
            'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
            'Code': ['.py', '.js', '.html', '.css', '.java', '.cpp']
        }

    def scan_location(self, name: str, location: Path) -> dict:
        """Quick scan of a location"""
        stats = {
            'name': name,
            'path': str(location),
            'exists': location.exists(),
            'total_files': 0,
            'total_dirs': 0,
            'by_type': {},
            'size_total': 0
        }
        
        if not location.exists():
            return stats
        
        print(f"\nScanning {name}...")
        
        try:
            # Count files and directories
            for item in location.rglob("*"):
                if item.is_file():
                    stats['total_files'] += 1
                    
                    # Count by extension type
                    ext = item.suffix.lower()
                    for category, extensions in self.file_extensions.items():
                        if ext in extensions:
                            if category not in stats['by_type']:
                                stats['by_type'][category] = 0
                            stats['by_type'][category] += 1
                            break
                    
                    # Add to total size
                    try:
                        stats['size_total'] += item.stat().st_size
                    except:
                        pass
                        
                elif item.is_dir():
                    stats['total_dirs'] += 1
                
                # Show progress every 100 items
                if (stats['total_files'] + stats['total_dirs']) % 100 == 0:
                    print(f"  ...processed {stats['total_files']} files, {stats['total_dirs']} dirs")
        
        except PermissionError:
            print(f"  Permission denied for some items in {name}")
        except Exception as e:
            print(f"  Error scanning {name}: {e}")
        
        # Convert size to human readable
        size_mb = stats['size_total'] / (1024 * 1024)
        size_gb = size_mb / 1024
        if size_gb > 1:
            stats['size_human'] = f"{size_gb:.1f} GB"
        else:
            stats['size_human'] = f"{size_mb:.1f} MB"
        
        print(f"  Found: {stats['total_files']} files, {stats['total_dirs']} directories ({stats['size_human']})")
        
        return stats

    def run_scan(self):
        """Run fast comprehensive scan"""
        print("=" * 60)
        print("FAST COMPREHENSIVE DRIVE SCAN")
        print("=" * 60)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = []
        
        # Scan each location
        for name, location in self.scan_locations:
            stats = self.scan_location(name, location)
            results.append(stats)
        
        # Generate summary
        print("\n" + "=" * 60)
        print("SCAN SUMMARY")
        print("=" * 60)
        
        total_files = 0
        total_dirs = 0
        total_size = 0
        
        for result in results:
            if result['exists']:
                print(f"\n{result['name']}:")
                print(f"  Files: {result['total_files']:,}")
                print(f"  Directories: {result['total_dirs']:,}")
                print(f"  Total Size: {result['size_human']}")
                
                if result['by_type']:
                    print("  File Types:")
                    for ftype, count in sorted(result['by_type'].items()):
                        print(f"    - {ftype}: {count}")
                
                total_files += result['total_files']
                total_dirs += result['total_dirs']
                total_size += result['size_total']
            else:
                print(f"\n{result['name']}: NOT FOUND")
        
        # Overall totals
        print("\n" + "=" * 60)
        print("OVERALL TOTALS:")
        print(f"  Total Files: {total_files:,}")
        print(f"  Total Directories: {total_dirs:,}")
        
        size_gb = total_size / (1024 * 1024 * 1024)
        print(f"  Total Size: {size_gb:.2f} GB")
        
        # Save results
        report_path = self.home / "drive_scan_summary.json"
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nDetailed results saved to: {report_path}")
        
        return results

if __name__ == "__main__":
    scanner = FastDriveScanner()
    scanner.run_scan()