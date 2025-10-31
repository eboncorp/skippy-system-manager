#!/usr/bin/env python3
"""
Timestamp Scanner Helper
Launches Simple Scan and automatically renames files with timestamps
"""

import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path
import threading

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

class TimestampScanner:
    def __init__(self):
        self.scan_dir = Path.home() / "Documents"
        self.target_dir = Path.home() / "Scans" / "Incoming"
        self.target_dir.mkdir(parents=True, exist_ok=True)
        
        # Watch for new files and track statistics
        self.initial_files = set()
        self.files_processed = 0
        self.total_pages = 0
        
        if self.scan_dir.exists():
            self.initial_files = {f.name for f in self.scan_dir.iterdir() if f.is_file()}
    
    def count_pdf_pages(self, file_path):
        """Count pages in a PDF file"""
        if not PDF_AVAILABLE:
            return 1  # Assume 1 page if PyPDF2 not available
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return len(pdf_reader.pages)
        except Exception:
            return 1  # Default to 1 page if can't read
    
    def launch_scanner_and_monitor(self):
        """Launch Simple Scan and monitor for new files"""
        print("🖨️  Launching Simple Scan...")
        print(f"   Files will be auto-renamed with timestamps")
        print(f"   Target folder: {self.target_dir}")
        print()
        
        # Launch Simple Scan in background
        try:
            process = subprocess.Popen(['simple-scan'], 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL)
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=self.monitor_files, daemon=True)
            monitor_thread.start()
            
            # Wait for Simple Scan to close
            process.wait()
            
            # Give a moment for final file operations
            time.sleep(2)
            
            # Final check for any new files
            self.check_for_new_files()
            
        except Exception as e:
            print(f"❌ Error launching Simple Scan: {e}")
    
    def monitor_files(self):
        """Monitor for new files being created"""
        while True:
            try:
                self.check_for_new_files()
                time.sleep(1)  # Check every second
            except:
                break
    
    def check_for_new_files(self):
        """Check for new files and rename them"""
        if not self.scan_dir.exists():
            return
        
        current_files = {f.name for f in self.scan_dir.iterdir() if f.is_file()}
        new_files = current_files - self.initial_files
        
        for filename in new_files:
            file_path = self.scan_dir / filename
            
            # Skip if file is still being written (check if size is stable)
            try:
                size1 = file_path.stat().st_size
                time.sleep(0.5)
                size2 = file_path.stat().st_size
                if size1 != size2:
                    continue  # File still being written
            except:
                continue
            
            # Generate timestamp filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extension = file_path.suffix or '.pdf'
            new_filename = f"scan_{timestamp}{extension}"
            
            # Move to target directory with timestamp name
            target_path = self.target_dir / new_filename
            
            # Ensure unique filename
            counter = 1
            while target_path.exists():
                target_path = self.target_dir / f"scan_{timestamp}_{counter}{extension}"
                counter += 1
            
            try:
                # Count pages before moving
                if extension.lower() == '.pdf':
                    page_count = self.count_pdf_pages(file_path)
                else:
                    page_count = 1  # Assume 1 page for images
                
                # Move and rename
                file_path.rename(target_path)
                
                # Update statistics
                self.files_processed += 1
                self.total_pages += page_count
                
                # Display progress
                print(f"✅ File {self.files_processed}: {filename} → {target_path.name}")
                print(f"   📄 Pages: {page_count} | Total pages scanned: {self.total_pages}")
                
                self.initial_files.add(filename)  # Avoid processing again
            except Exception as e:
                print(f"❌ Error renaming {filename}: {e}")

def main():
    print("📄 TIMESTAMP SCANNER")
    print("=" * 30)
    
    scanner = TimestampScanner()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("This tool launches Simple Scan and automatically renames")
        print("scanned files with timestamps in format: scan_YYYYMMDD_HHMMSS.pdf")
        print()
        print("Usage: python3 timestamp_scanner.py")
        return
    
    scanner.launch_scanner_and_monitor()
    
    print(f"\n📄 Scanning session complete!")
    print(f"   Files processed: {scanner.files_processed}")
    print(f"   Total pages scanned: {scanner.total_pages}")
    print()
    print("Run the document organizer to categorize your scans:")
    print("   python3 smart_document_organizer.py auto")

if __name__ == "__main__":
    main()