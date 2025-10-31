#!/usr/bin/env python3
"""
Scan Folder Watcher
Automatically detects new files in scan directories and prompts for organization
"""

import os
import sys
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import tkinter as tk
from tkinter import messagebox
import threading

class ScanHandler(FileSystemEventHandler):
    def __init__(self):
        self.scan_base = Path.home() / "Scans"
        self.watch_folders = [
            self.scan_base,
            self.scan_base / "Incoming",
            Path.home() / "Documents",  # Default Simple Scan location
        ]
        
    def on_created(self, event):
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Check if it's a document file
        if file_path.suffix.lower() in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            # Wait a moment for file to be fully written
            time.sleep(1)
            self.prompt_organization(file_path)
    
    def prompt_organization(self, file_path):
        """Show notification about new scan and offer to organize"""
        def show_dialog():
            root = tk.Tk()
            root.withdraw()  # Hide main window
            
            result = messagebox.askyesno(
                "New Scan Detected", 
                f"New document detected:\n{file_path.name}\n\nOpen Scan Organizer to organize it?",
                icon='question'
            )
            
            if result:
                # Launch scan organizer
                subprocess.Popen([sys.executable, str(Path.home() / "scan_organizer.py")])
            
            root.destroy()
        
        # Run dialog in separate thread to avoid blocking
        thread = threading.Thread(target=show_dialog, daemon=True)
        thread.start()

def main():
    """Start the scan watcher service"""
    handler = ScanHandler()
    observer = Observer()
    
    # Watch multiple directories
    for folder in handler.watch_folders:
        if folder.exists():
            observer.schedule(handler, str(folder), recursive=False)
            print(f"Watching: {folder}")
    
    observer.start()
    print("Scan watcher started. Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nScan watcher stopped.")
    
    observer.join()

if __name__ == "__main__":
    main()