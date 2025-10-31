#!/usr/bin/env python3
"""
Downloads Folder Watcher - Automatic File Detection

Version: 1.0.0
Created: 2025-10-28
Author: Claude & Dave Biggers
Purpose: Monitor downloads folder and notify when new files appear

This daemon watches /home/dave/skippy/claude/downloads/ for new files
and creates a notification file that Claude Code can detect.

Usage:
    ./downloads_watcher_v1.0.0.py --daemon    # Run as background daemon
    ./downloads_watcher_v1.0.0.py --stop      # Stop the daemon
    ./downloads_watcher_v1.0.0.py --status    # Check daemon status
    ./downloads_watcher_v1.0.0.py --once      # Single check (manual trigger)

Dependencies:
    sudo apt install inotify-tools python3-inotify

Protocol Reference:
    /home/dave/skippy/conversations/file_download_management_protocol.md
"""

import os
import sys
import time
import json
import signal
import argparse
from pathlib import Path
from datetime import datetime
import inotify.adapters
import inotify.constants

# Configuration
DOWNLOADS_DIR = "/home/dave/skippy/claude/downloads"
NOTIFICATION_FILE = "/tmp/claude_downloads_notification.json"
PID_FILE = "/tmp/downloads_watcher.pid"
LOG_FILE = "/home/dave/skippy/scripts/monitoring/downloads_watcher.log"

# Ignore patterns
IGNORE_PATTERNS = [
    '.tmp',
    '.crdownload',  # Chrome partial downloads
    '.part',        # Firefox partial downloads
    '.download',
    'Thumbs.db',
    '.DS_Store'
]

def should_ignore(filename):
    """Check if file should be ignored"""
    for pattern in IGNORE_PATTERNS:
        if pattern in filename:
            return True
    return False

def log_message(message, level="INFO"):
    """Log message to file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}\n"

    try:
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Error writing to log: {e}", file=sys.stderr)

def create_notification(filepath):
    """Create notification file for Claude Code to detect"""
    file_stat = os.stat(filepath)

    notification = {
        "timestamp": datetime.now().isoformat(),
        "event": "new_download",
        "filepath": str(filepath),
        "filename": os.path.basename(filepath),
        "size": file_stat.st_size,
        "size_human": format_bytes(file_stat.st_size),
        "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
        "file_type": get_file_type(filepath)
    }

    try:
        with open(NOTIFICATION_FILE, 'w') as f:
            json.dump(notification, f, indent=2)
        log_message(f"Created notification for: {os.path.basename(filepath)}")
        return True
    except Exception as e:
        log_message(f"Error creating notification: {e}", "ERROR")
        return False

def format_bytes(bytes_size):
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f}TB"

def get_file_type(filepath):
    """Determine file type from extension"""
    ext = Path(filepath).suffix.lower()

    type_map = {
        '.txt': 'text',
        '.md': 'markdown',
        '.log': 'log',
        '.zip': 'archive',
        '.tar.gz': 'archive',
        '.7z': 'archive',
        '.png': 'image',
        '.jpg': 'image',
        '.jpeg': 'image',
        '.gif': 'image',
        '.webp': 'image',
        '.pdf': 'pdf',
        '.json': 'data',
        '.csv': 'data',
        '.xml': 'data',
        '.py': 'code',
        '.js': 'code',
        '.php': 'code',
        '.sh': 'code',
        '.css': 'code',
        '.html': 'code'
    }

    return type_map.get(ext, 'unknown')

def watch_downloads():
    """Main watch loop using inotify"""
    log_message("Starting downloads watcher daemon")

    i = inotify.adapters.Inotify()
    i.add_watch(DOWNLOADS_DIR)

    log_message(f"Watching: {DOWNLOADS_DIR}")

    try:
        for event in i.event_gen(yield_nones=False):
            (_, type_names, path, filename) = event

            # Only process file creation events
            if 'IN_CLOSE_WRITE' in type_names or 'IN_MOVED_TO' in type_names:
                # Handle both bytes and strings from inotify
                if isinstance(filename, bytes):
                    filename = filename.decode('utf-8')
                if isinstance(path, bytes):
                    path = path.decode('utf-8')

                if filename and not should_ignore(filename):
                    filepath = os.path.join(path, filename)

                    # Wait a moment to ensure file is fully written
                    time.sleep(0.5)

                    if os.path.exists(filepath) and os.path.isfile(filepath):
                        log_message(f"New file detected: {filename}")
                        create_notification(filepath)

    except KeyboardInterrupt:
        log_message("Watcher stopped by user")
    except Exception as e:
        log_message(f"Watcher error: {e}", "ERROR")
        raise

def start_daemon():
    """Start the watcher as a daemon"""
    # Check if already running
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                old_pid = int(f.read().strip())

            # Check if process is actually running
            try:
                os.kill(old_pid, 0)
                print(f"Watcher already running (PID: {old_pid})")
                return
            except OSError:
                # Process not running, remove stale PID file
                os.remove(PID_FILE)
        except Exception:
            pass

    # Fork to background
    pid = os.fork()
    if pid > 0:
        # Parent process
        print(f"Downloads watcher started (PID: {pid})")
        return

    # Child process (daemon)
    os.setsid()

    # Write PID file
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

    # Redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()

    # Start watching
    watch_downloads()

    # Cleanup on exit
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)

def stop_daemon():
    """Stop the running daemon"""
    if not os.path.exists(PID_FILE):
        print("Watcher is not running")
        return

    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())

        os.kill(pid, signal.SIGTERM)
        time.sleep(1)

        # Check if stopped
        try:
            os.kill(pid, 0)
            print("Watcher did not stop, forcing...")
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass

        os.remove(PID_FILE)
        log_message("Watcher stopped")
        print("Watcher stopped")

    except Exception as e:
        print(f"Error stopping watcher: {e}")
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

def check_status():
    """Check daemon status"""
    if not os.path.exists(PID_FILE):
        print("Status: Not running")
        return

    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())

        try:
            os.kill(pid, 0)
            print(f"Status: Running (PID: {pid})")
            print(f"Watching: {DOWNLOADS_DIR}")
            print(f"Log: {LOG_FILE}")
            print(f"Notifications: {NOTIFICATION_FILE}")
        except OSError:
            print("Status: PID file exists but process not running (stale)")
            os.remove(PID_FILE)

    except Exception as e:
        print(f"Error checking status: {e}")

def manual_check():
    """Manual check for new files (once)"""
    print(f"Checking {DOWNLOADS_DIR}...")

    try:
        files = []
        for entry in os.scandir(DOWNLOADS_DIR):
            if entry.is_file() and not should_ignore(entry.name):
                files.append((entry.stat().st_mtime, entry.path, entry.name))

        if not files:
            print("No files in downloads folder")
            return

        # Sort by modification time, newest first
        files.sort(reverse=True)

        # Show newest file
        _, filepath, filename = files[0]
        file_stat = os.stat(filepath)
        modified = datetime.fromtimestamp(file_stat.st_mtime)

        print(f"\nMost recent file:")
        print(f"  Name: {filename}")
        print(f"  Size: {format_bytes(file_stat.st_size)}")
        print(f"  Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Type: {get_file_type(filepath)}")

        # Create notification
        create_notification(filepath)
        print(f"\nNotification created: {NOTIFICATION_FILE}")

    except Exception as e:
        print(f"Error checking downloads: {e}")

def main():
    parser = argparse.ArgumentParser(description='Downloads Folder Watcher')
    parser.add_argument('--daemon', action='store_true', help='Run as background daemon')
    parser.add_argument('--stop', action='store_true', help='Stop the daemon')
    parser.add_argument('--status', action='store_true', help='Check daemon status')
    parser.add_argument('--once', action='store_true', help='Single check (manual trigger)')

    args = parser.parse_args()

    if args.daemon:
        start_daemon()
    elif args.stop:
        stop_daemon()
    elif args.status:
        check_status()
    elif args.once:
        manual_check()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
