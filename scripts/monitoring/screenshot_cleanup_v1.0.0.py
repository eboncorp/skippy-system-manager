#!/usr/bin/env python3
"""
Screenshot Auto-Cleanup System
Version: 1.0.0
Created: 2025-10-28
Purpose: Automatically manage screenshots folder with retention policies

Features:
- Keep only N most recent screenshots
- Archive old screenshots by month
- Auto-consolidate Screenshots/screenshots folders
- Run as daemon or one-time cleanup
"""

import os
import sys
import time
import shutil
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
SCREENSHOTS_DIRS = [
    Path.home() / "Pictures" / "Screenshots",
    Path.home() / "Pictures" / "screenshots"
]
ARCHIVE_DIR = Path.home() / "Pictures" / "screenshots_archive"
KEEP_RECENT = 20  # Keep most recent N screenshots
ARCHIVE_OLDER_THAN_DAYS = 30  # Archive screenshots older than N days
DELETE_ARCHIVED_AFTER_DAYS = 180  # Delete archived screenshots after N days

class ScreenshotCleaner:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.stats = {
            'archived': 0,
            'deleted': 0,
            'kept': 0,
            'consolidated': 0
        }

    def log(self, message, level='INFO'):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")

    def consolidate_folders(self):
        """Merge Screenshots and screenshots folders"""
        self.log("Consolidating screenshot folders...")

        # Use lowercase screenshots as primary
        primary = Path.home() / "Pictures" / "screenshots"
        secondary = Path.home() / "Pictures" / "Screenshots"

        if not primary.exists():
            primary.mkdir(parents=True, exist_ok=True)

        if secondary.exists() and secondary != primary:
            for file in secondary.glob("*.png"):
                target = primary / file.name
                if not target.exists():
                    if not self.dry_run:
                        shutil.move(str(file), str(target))
                    self.log(f"Moved: {file.name} to primary folder")
                    self.stats['consolidated'] += 1
                else:
                    self.log(f"Skipped: {file.name} (already exists in primary)")

            # Remove empty secondary folder
            if not self.dry_run and not any(secondary.iterdir()):
                secondary.rmdir()
                self.log(f"Removed empty folder: {secondary}")

    def get_all_screenshots(self):
        """Get all screenshots sorted by modification time"""
        screenshots = []

        for dir_path in SCREENSHOTS_DIRS:
            if dir_path.exists():
                for file in dir_path.glob("Screenshot*.png"):
                    screenshots.append({
                        'path': file,
                        'mtime': file.stat().st_mtime,
                        'size': file.stat().st_size,
                        'date': datetime.fromtimestamp(file.stat().st_mtime)
                    })

        # Sort by modification time (newest first)
        screenshots.sort(key=lambda x: x['mtime'], reverse=True)
        return screenshots

    def archive_screenshot(self, screenshot):
        """Archive a screenshot to monthly folder"""
        date = screenshot['date']
        archive_month = ARCHIVE_DIR / date.strftime('%Y-%m')
        archive_month.mkdir(parents=True, exist_ok=True)

        target = archive_month / screenshot['path'].name

        if not self.dry_run:
            shutil.move(str(screenshot['path']), str(target))

        self.log(f"Archived: {screenshot['path'].name} -> {archive_month.name}/")
        self.stats['archived'] += 1

    def cleanup_old_archives(self):
        """Delete archived screenshots older than threshold"""
        if not ARCHIVE_DIR.exists():
            return

        cutoff_date = datetime.now() - timedelta(days=DELETE_ARCHIVED_AFTER_DAYS)
        self.log(f"Checking archives older than {cutoff_date.strftime('%Y-%m-%d')}...")

        for month_dir in ARCHIVE_DIR.iterdir():
            if not month_dir.is_dir():
                continue

            for screenshot in month_dir.glob("*.png"):
                mtime = datetime.fromtimestamp(screenshot.stat().st_mtime)
                if mtime < cutoff_date:
                    if not self.dry_run:
                        screenshot.unlink()
                    self.log(f"Deleted old archive: {month_dir.name}/{screenshot.name}")
                    self.stats['deleted'] += 1

            # Remove empty archive folders
            if not self.dry_run and month_dir.exists() and not any(month_dir.iterdir()):
                month_dir.rmdir()
                self.log(f"Removed empty archive folder: {month_dir.name}")

    def clean(self):
        """Main cleanup routine"""
        self.log("=" * 70)
        self.log("Screenshot Cleanup Starting")
        self.log("=" * 70)

        if self.dry_run:
            self.log("DRY RUN MODE - No changes will be made", "WARNING")

        # Step 1: Consolidate folders
        self.consolidate_folders()

        # Step 2: Get all screenshots
        screenshots = self.get_all_screenshots()
        self.log(f"Found {len(screenshots)} total screenshots")

        if not screenshots:
            self.log("No screenshots to process")
            return

        # Step 3: Keep recent, archive old
        cutoff_date = datetime.now() - timedelta(days=ARCHIVE_OLDER_THAN_DAYS)

        for i, screenshot in enumerate(screenshots):
            if i < KEEP_RECENT:
                # Keep recent screenshots
                self.log(f"Keeping recent: {screenshot['path'].name}")
                self.stats['kept'] += 1
            elif screenshot['date'] < cutoff_date:
                # Archive old screenshots
                self.archive_screenshot(screenshot)
            else:
                # Keep screenshots that aren't old enough yet
                self.log(f"Keeping (not old enough): {screenshot['path'].name}")
                self.stats['kept'] += 1

        # Step 4: Cleanup old archives
        self.cleanup_old_archives()

        # Summary
        self.log("=" * 70)
        self.log("Cleanup Summary:")
        self.log(f"  Consolidated: {self.stats['consolidated']} files")
        self.log(f"  Kept current: {self.stats['kept']} files")
        self.log(f"  Archived: {self.stats['archived']} files")
        self.log(f"  Deleted old: {self.stats['deleted']} files")
        self.log("=" * 70)

        if self.dry_run:
            self.log("This was a DRY RUN - run without --dry-run to apply changes", "WARNING")

def run_daemon():
    """Run cleanup as a daemon (daily at 2 AM)"""
    print("Screenshot cleanup daemon starting...")
    print(f"Will run daily cleanup at 2:00 AM")
    print(f"Keeping {KEEP_RECENT} most recent screenshots")
    print(f"Archiving screenshots older than {ARCHIVE_OLDER_THAN_DAYS} days")
    print(f"Deleting archives older than {DELETE_ARCHIVED_AFTER_DAYS} days")
    print()

    while True:
        now = datetime.now()
        # Run at 2 AM
        next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
        if now >= next_run:
            next_run += timedelta(days=1)

        sleep_seconds = (next_run - now).total_seconds()
        print(f"Next cleanup: {next_run.strftime('%Y-%m-%d %H:%M:%S')} (in {sleep_seconds/3600:.1f} hours)")

        time.sleep(sleep_seconds)

        # Run cleanup
        cleaner = ScreenshotCleaner(dry_run=False)
        cleaner.clean()

def main():
    parser = argparse.ArgumentParser(description='Screenshot Auto-Cleanup System')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon (daily cleanup)')
    parser.add_argument('--now', action='store_true', help='Run cleanup immediately')

    args = parser.parse_args()

    if args.daemon:
        run_daemon()
    elif args.now or args.dry_run:
        cleaner = ScreenshotCleaner(dry_run=args.dry_run)
        cleaner.clean()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
