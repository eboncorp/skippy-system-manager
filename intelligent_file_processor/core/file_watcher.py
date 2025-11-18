#!/usr/bin/env python3
"""
File Watcher Daemon for Intelligent File Processor
Monitors configured folders for new files using watchdog
"""

import time
import logging
from pathlib import Path
from typing import Callable, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import fnmatch


class FileProcessorHandler(FileSystemEventHandler):
    """Handles file system events"""

    def __init__(self, callback: Callable, ignore_patterns: List[str], logger: logging.Logger):
        """
        Initialize handler

        Args:
            callback: Function to call when new file detected
            ignore_patterns: List of glob patterns to ignore
            logger: Logger instance
        """
        super().__init__()
        self.callback = callback
        self.ignore_patterns = ignore_patterns
        self.logger = logger
        self.processed_files = set()  # Track recently processed files

    def should_ignore(self, file_path: str) -> bool:
        """
        Check if file should be ignored

        Args:
            file_path: Path to file

        Returns:
            True if file should be ignored
        """
        filename = Path(file_path).name

        # Check against ignore patterns
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True

        return False

    def on_created(self, event: FileSystemEvent):
        """Called when a file is created"""
        if event.is_directory:
            return

        file_path = event.src_path

        # Ignore if matches ignore patterns
        if self.should_ignore(file_path):
            self.logger.debug(f"Ignoring file (matches pattern): {file_path}")
            return

        # Ignore if already processed recently
        if file_path in self.processed_files:
            return

        self.logger.info(f"New file detected: {file_path}")
        self.processed_files.add(file_path)

        # Call the callback function
        try:
            self.callback(file_path)
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")

    def on_modified(self, event: FileSystemEvent):
        """Called when a file is modified"""
        # We primarily care about CLOSE_WRITE but watchdog doesn't have that
        # So we'll handle this in on_created with a stabilization delay
        pass

    def on_moved(self, event: FileSystemEvent):
        """Called when a file is moved"""
        if event.is_directory:
            return

        # Treat move_to as a new file
        file_path = event.dest_path

        if self.should_ignore(file_path):
            self.logger.debug(f"Ignoring moved file (matches pattern): {file_path}")
            return

        if file_path in self.processed_files:
            return

        self.logger.info(f"File moved to watched location: {file_path}")
        self.processed_files.add(file_path)

        try:
            self.callback(file_path)
        except Exception as e:
            self.logger.error(f"Error processing moved file {file_path}: {e}")


class FileWatcher:
    """Watches configured directories for new files"""

    def __init__(self, watch_folders: List[dict], callback: Callable,
                 ignore_patterns: List[str], logger: logging.Logger):
        """
        Initialize file watcher

        Args:
            watch_folders: List of folder configs to watch
            callback: Function to call when new file detected
            ignore_patterns: List of glob patterns to ignore
            logger: Logger instance
        """
        self.watch_folders = watch_folders
        self.callback = callback
        self.ignore_patterns = ignore_patterns
        self.logger = logger
        self.observer = Observer()
        self.handlers = []

    def start(self):
        """Start watching all configured folders"""
        self.logger.info("Starting file watcher daemon...")

        for folder_config in self.watch_folders:
            path = folder_config['path']
            recursive = folder_config.get('recursive', False)

            # Create folder if it doesn't exist
            Path(path).mkdir(parents=True, exist_ok=True)

            # Create handler for this folder
            handler = FileProcessorHandler(
                self.callback,
                self.ignore_patterns,
                self.logger
            )
            self.handlers.append(handler)

            # Schedule watching
            self.observer.schedule(handler, path, recursive=recursive)
            self.logger.info(f"Watching: {path} (recursive={recursive})")

        # Start the observer
        self.observer.start()
        self.logger.info("File watcher started successfully")

    def stop(self):
        """Stop watching all folders"""
        self.logger.info("Stopping file watcher...")
        self.observer.stop()
        self.observer.join()
        self.logger.info("File watcher stopped")

    def run(self):
        """Run the file watcher (blocking)"""
        self.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()


if __name__ == "__main__":
    # Test file watcher
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    logger = logging.getLogger(__name__)

    def test_callback(file_path: str):
        """Test callback function"""
        print(f">>> Would process: {file_path}")

    # Watch current directory for testing
    test_config = [{
        'path': '/tmp/file_watcher_test',
        'enabled': True,
        'recursive': False
    }]

    # Create test directory
    Path('/tmp/file_watcher_test').mkdir(exist_ok=True)

    ignore_patterns = ['*.tmp', '*.swp']

    watcher = FileWatcher(test_config, test_callback, ignore_patterns, logger)

    print(f"\nWatching /tmp/file_watcher_test/ for new files...")
    print("Try: touch /tmp/file_watcher_test/test.txt")
    print("Press Ctrl+C to stop\n")

    watcher.run()
