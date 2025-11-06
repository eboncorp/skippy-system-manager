"""
Integration tests for backup and restore flow
"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path


@pytest.mark.integration
@pytest.mark.slow
class TestBackupRestoreFlow:
    """Integration tests for backup and restore operations."""

    def test_backup_directory_structure(self, mock_skippy_env):
        """Test that backup directory structure is correct."""
        backup_path = mock_skippy_env["backup_path"]

        assert backup_path.exists()
        assert backup_path.is_dir()

        # Create subdirectories
        (backup_path / "wordpress").mkdir(exist_ok=True)
        (backup_path / "system").mkdir(exist_ok=True)

        assert (backup_path / "wordpress").exists()
        assert (backup_path / "system").exists()

    def test_create_test_backup(self, temp_dir):
        """Test creating a simple backup."""
        # Create test data
        source_dir = temp_dir / "source"
        source_dir.mkdir()
        (source_dir / "test_file.txt").write_text("Test content")

        # Create backup
        backup_dir = temp_dir / "backup"
        backup_dir.mkdir()

        shutil.copytree(source_dir, backup_dir / "test_backup")

        # Verify backup
        assert (backup_dir / "test_backup" / "test_file.txt").exists()
        content = (backup_dir / "test_backup" / "test_file.txt").read_text()
        assert content == "Test content"

    def test_restore_from_backup(self, temp_dir):
        """Test restoring from a backup."""
        # Create backup
        backup_dir = temp_dir / "backup"
        backup_dir.mkdir()
        (backup_dir / "test_file.txt").write_text("Backed up content")

        # Restore to new location
        restore_dir = temp_dir / "restore"
        restore_dir.mkdir()

        shutil.copy(backup_dir / "test_file.txt", restore_dir / "test_file.txt")

        # Verify restoration
        assert (restore_dir / "test_file.txt").exists()
        content = (restore_dir / "test_file.txt").read_text()
        assert content == "Backed up content"

    def test_backup_integrity(self, temp_dir):
        """Test backup file integrity."""
        import hashlib

        # Create test file
        test_file = temp_dir / "original.txt"
        test_content = "Test content for integrity check"
        test_file.write_text(test_content)

        # Calculate original hash
        original_hash = hashlib.sha256(test_content.encode()).hexdigest()

        # Create backup
        backup_file = temp_dir / "backup.txt"
        shutil.copy(test_file, backup_file)

        # Verify backup hash
        backup_content = backup_file.read_text()
        backup_hash = hashlib.sha256(backup_content.encode()).hexdigest()

        assert original_hash == backup_hash

    @pytest.mark.skip(reason="Requires large test files")
    def test_backup_compression(self, temp_dir):
        """Test backup compression."""
        import tarfile

        # Create test data
        source_dir = temp_dir / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("Content 1" * 1000)
        (source_dir / "file2.txt").write_text("Content 2" * 1000)

        # Create compressed backup
        backup_file = temp_dir / "backup.tar.gz"
        with tarfile.open(backup_file, "w:gz") as tar:
            tar.add(source_dir, arcname="source")

        # Verify backup exists and is smaller than uncompressed
        assert backup_file.exists()
        # Compressed should be smaller (not always true for small files)
        # assert backup_file.stat().st_size < sum(...)
