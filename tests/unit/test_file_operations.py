"""
Unit tests for file operations
"""
import pytest
from pathlib import Path


@pytest.mark.unit
class TestFileReading:
    """Test file reading operations."""

    def test_read_entire_file(self, sample_file):
        """Test reading an entire file."""
        content = sample_file.read_text()
        lines = content.split("\n")

        assert len(lines) == 6  # 5 lines + empty line from trailing newline
        assert lines[0] == "Line 1"
        assert lines[4] == "Line 5"

    def test_read_file_with_offset(self, sample_file):
        """Test reading file with start offset."""
        all_lines = sample_file.read_text().splitlines()
        lines_from_offset = all_lines[2:]  # Start from line 3 (0-indexed)

        assert len(lines_from_offset) == 3
        assert lines_from_offset[0] == "Line 3"

    def test_read_file_with_limit(self, sample_file):
        """Test reading file with line limit."""
        all_lines = sample_file.read_text().splitlines()
        limited_lines = all_lines[:2]  # First 2 lines

        assert len(limited_lines) == 2
        assert limited_lines[0] == "Line 1"
        assert limited_lines[1] == "Line 2"

    def test_read_nonexistent_file(self, temp_dir):
        """Test reading a file that doesn't exist."""
        nonexistent = temp_dir / "nonexistent.txt"

        assert not nonexistent.exists()

        # Reading should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            nonexistent.read_text()


@pytest.mark.unit
class TestFileWriting:
    """Test file writing operations."""

    def test_write_new_file(self, temp_dir):
        """Test writing to a new file."""
        new_file = temp_dir / "new_file.txt"
        content = "Test content"

        new_file.write_text(content)

        assert new_file.exists()
        assert new_file.read_text() == content

    def test_overwrite_existing_file(self, sample_file):
        """Test overwriting an existing file."""
        original_content = sample_file.read_text()
        new_content = "New content"

        sample_file.write_text(new_content)

        assert sample_file.read_text() == new_content
        assert sample_file.read_text() != original_content

    def test_append_to_file(self, sample_file):
        """Test appending to an existing file."""
        original_content = sample_file.read_text()
        additional_content = "Additional line"

        # Append mode
        with open(sample_file, "a") as f:
            f.write(additional_content)

        new_content = sample_file.read_text()

        assert new_content.startswith(original_content)
        assert additional_content in new_content

    def test_write_creates_parent_directories(self, temp_dir):
        """Test that writing creates parent directories if needed."""
        nested_file = temp_dir / "sub1" / "sub2" / "file.txt"
        content = "Nested content"

        # Create parent directories
        nested_file.parent.mkdir(parents=True, exist_ok=True)
        nested_file.write_text(content)

        assert nested_file.exists()
        assert nested_file.read_text() == content


@pytest.mark.unit
class TestDirectoryOperations:
    """Test directory operations."""

    def test_list_directory(self, temp_dir):
        """Test listing directory contents."""
        # Create some files
        (temp_dir / "file1.txt").write_text("content1")
        (temp_dir / "file2.txt").write_text("content2")
        (temp_dir / "file3.py").write_text("content3")

        all_files = list(temp_dir.glob("*"))
        txt_files = list(temp_dir.glob("*.txt"))
        py_files = list(temp_dir.glob("*.py"))

        assert len(all_files) == 3
        assert len(txt_files) == 2
        assert len(py_files) == 1

    def test_recursive_directory_listing(self, temp_dir):
        """Test recursive directory listing."""
        # Create nested structure
        (temp_dir / "sub1").mkdir()
        (temp_dir / "sub1" / "file1.txt").write_text("content1")
        (temp_dir / "sub2").mkdir()
        (temp_dir / "sub2" / "file2.txt").write_text("content2")

        all_txt_files = list(temp_dir.rglob("*.txt"))

        assert len(all_txt_files) == 2

    def test_directory_exists(self, temp_dir):
        """Test checking if directory exists."""
        existing_dir = temp_dir / "existing"
        existing_dir.mkdir()

        nonexistent_dir = temp_dir / "nonexistent"

        assert existing_dir.exists()
        assert existing_dir.is_dir()
        assert not nonexistent_dir.exists()

    def test_create_nested_directories(self, temp_dir):
        """Test creating nested directories."""
        nested_dir = temp_dir / "level1" / "level2" / "level3"

        nested_dir.mkdir(parents=True)

        assert nested_dir.exists()
        assert nested_dir.is_dir()
        assert (temp_dir / "level1").exists()
        assert (temp_dir / "level1" / "level2").exists()


@pytest.mark.unit
class TestPathOperations:
    """Test path manipulation operations."""

    def test_path_expansion(self, monkeypatch):
        """Test path expansion with environment variables."""
        monkeypatch.setenv("TEST_VAR", "/test/path")

        # Test expanduser (though not using ~ here)
        path = Path("/tmp/test")
        expanded = path.expanduser()

        assert expanded == path

    def test_absolute_path(self, temp_dir):
        """Test converting to absolute path."""
        relative_path = Path("relative/path")

        # Get absolute path
        absolute = (temp_dir / relative_path).absolute()

        assert absolute.is_absolute()

    def test_path_joining(self, temp_dir):
        """Test joining paths."""
        base_path = temp_dir
        sub_path = "sub" / Path("dir")
        file_name = "file.txt"

        full_path = base_path / sub_path / file_name

        assert str(sub_path) in str(full_path)
        assert file_name in str(full_path)

    def test_path_parent(self, temp_dir):
        """Test getting parent directory."""
        nested_path = temp_dir / "sub1" / "sub2" / "file.txt"

        parent = nested_path.parent
        grandparent = nested_path.parent.parent

        assert parent.name == "sub2"
        assert grandparent.name == "sub1"
