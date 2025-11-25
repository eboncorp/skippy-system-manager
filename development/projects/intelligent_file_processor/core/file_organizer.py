#!/usr/bin/env python3
"""
File Organizer for Intelligent File Processor
Safely moves and organizes files to correct destinations
"""

import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class FileOrganizer:
    """Organizes files by moving them to appropriate destinations"""

    def __init__(self, config, logger: logging.Logger):
        """
        Initialize file organizer

        Args:
            config: Configuration object
            logger: Logger instance
        """
        self.config = config
        self.logger = logger

    def organize(self, file_path: str, category: str, subcategory: Optional[str],
                 new_filename: str) -> Dict[str, Any]:
        """
        Organize file - move to correct destination with new name

        Args:
            file_path: Original file path
            category: Main category
            subcategory: Subcategory (optional)
            new_filename: New filename (without path)

        Returns:
            Dictionary with organization results
        """
        source = Path(file_path)

        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")

        # Get destination directory
        dest_dir = self._get_destination_dir(category, subcategory)

        # Create destination directory if needed
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Build destination path
        dest_path = dest_dir / new_filename

        # Handle naming conflicts
        dest_path = self._resolve_conflicts(dest_path)

        # Create backup if configured
        backup_path = None
        if self.config.should_create_backup():
            backup_path = self._create_backup(source)

        # Move file
        try:
            shutil.move(str(source), str(dest_path))
            self.logger.info(f"Moved: {source.name} → {dest_path}")

            return {
                'success': True,
                'source': str(source),
                'destination': str(dest_path),
                'backup': str(backup_path) if backup_path else None,
                'timestamp': datetime.now()
            }

        except Exception as e:
            self.logger.error(f"Error moving file {source} to {dest_path}: {e}")

            # Restore from backup if we created one
            if backup_path and backup_path.exists():
                self.logger.info(f"Restoring from backup: {backup_path}")
                shutil.copy2(str(backup_path), str(source))

            return {
                'success': False,
                'source': str(source),
                'error': str(e),
                'timestamp': datetime.now()
            }

    def _get_destination_dir(self, category: str, subcategory: Optional[str]) -> Path:
        """
        Get destination directory for category

        Args:
            category: Main category
            subcategory: Subcategory (optional)

        Returns:
            Path to destination directory
        """
        # Get base destination for category
        base_dest = self.config.get_destination(category)

        # Add subcategory if provided
        if subcategory:
            dest = base_dest / subcategory
        else:
            dest = base_dest

        return dest

    def _resolve_conflicts(self, dest_path: Path) -> Path:
        """
        Resolve naming conflicts by adding suffix

        Args:
            dest_path: Proposed destination path

        Returns:
            Non-conflicting path
        """
        if not dest_path.exists():
            return dest_path

        # File exists - add numerical suffix
        stem = dest_path.stem
        extension = dest_path.suffix
        parent = dest_path.parent

        counter = 1
        while True:
            new_name = f"{stem}_{counter:03d}{extension}"
            new_path = parent / new_name

            if not new_path.exists():
                self.logger.warning(f"Naming conflict resolved: {dest_path.name} → {new_name}")
                return new_path

            counter += 1

            if counter > 999:
                raise ValueError(f"Too many naming conflicts for {dest_path.name}")

    def _create_backup(self, source: Path) -> Optional[Path]:
        """
        Create backup copy of file

        Args:
            source: Source file path

        Returns:
            Path to backup file
        """
        try:
            # Get backup directory
            backup_dir = self.config.get_destination('backups')
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Create dated subdirectory
            date_dir = backup_dir / datetime.now().strftime('%Y/%m')
            date_dir.mkdir(parents=True, exist_ok=True)

            # Create backup with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{timestamp}_{source.name}"
            backup_path = date_dir / backup_name

            # Copy file
            shutil.copy2(str(source), str(backup_path))
            self.logger.debug(f"Backup created: {backup_path}")

            return backup_path

        except Exception as e:
            self.logger.error(f"Error creating backup for {source}: {e}")
            return None

    def quarantine(self, file_path: str, reason: str) -> Dict[str, Any]:
        """
        Move file to quarantine for manual review

        Args:
            file_path: File to quarantine
            reason: Reason for quarantine

        Returns:
            Dictionary with quarantine results
        """
        source = Path(file_path)

        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")

        # Get quarantine directory
        quarantine_dir = self.config.get_destination('quarantine')
        quarantine_dir.mkdir(parents=True, exist_ok=True)

        # Keep original filename in quarantine
        dest_path = quarantine_dir / source.name
        dest_path = self._resolve_conflicts(dest_path)

        # Create backup
        backup_path = None
        if self.config.should_create_backup():
            backup_path = self._create_backup(source)

        # Move to quarantine
        try:
            shutil.move(str(source), str(dest_path))
            self.logger.warning(f"Quarantined: {source.name} → {dest_path} (Reason: {reason})")

            # Create metadata file
            meta_path = dest_path.with_suffix(dest_path.suffix + '.meta')
            with open(meta_path, 'w') as f:
                f.write(f"Reason: {reason}\n")
                f.write(f"Timestamp: {datetime.now()}\n")
                f.write(f"Original path: {source}\n")

            return {
                'success': True,
                'quarantined': True,
                'source': str(source),
                'destination': str(dest_path),
                'backup': str(backup_path) if backup_path else None,
                'reason': reason,
                'timestamp': datetime.now()
            }

        except Exception as e:
            self.logger.error(f"Error quarantining file {source}: {e}")

            return {
                'success': False,
                'source': str(source),
                'error': str(e),
                'timestamp': datetime.now()
            }


if __name__ == "__main__":
    # Test file organizer
    import sys
    from config_loader import ConfigLoader

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Load config
    config = ConfigLoader()

    organizer = FileOrganizer(config, logger)

    print("File Organizer Test")
    print(f"Destinations configured:")
    for cat in ['campaign', 'business', 'personal', 'quarantine']:
        dest = config.get_destination(cat)
        print(f"  {cat}: {dest}")
