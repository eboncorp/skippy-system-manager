"""
Pytest configuration and shared fixtures
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def mock_skippy_env(monkeypatch, temp_dir):
    """Mock Skippy environment variables."""
    skippy_path = temp_dir / "skippy"
    wordpress_path = temp_dir / "wordpress"

    # Create directory structure
    skippy_path.mkdir(parents=True)
    wordpress_path.mkdir(parents=True)
    (skippy_path / "scripts").mkdir()
    (skippy_path / "conversations").mkdir()
    (skippy_path / "documentation" / "protocols").mkdir(parents=True)
    (wordpress_path / "backups").mkdir()

    # Set environment variables
    monkeypatch.setenv("SKIPPY_BASE_PATH", str(skippy_path))
    monkeypatch.setenv("WORDPRESS_BASE_PATH", str(wordpress_path))
    monkeypatch.setenv("SKIPPY_SCRIPTS_PATH", str(skippy_path / "scripts"))
    monkeypatch.setenv("SKIPPY_CONVERSATIONS_PATH", str(skippy_path / "conversations"))
    monkeypatch.setenv("WORDPRESS_BACKUP_PATH", str(wordpress_path / "backups"))

    yield {
        "skippy_path": skippy_path,
        "wordpress_path": wordpress_path,
        "scripts_path": skippy_path / "scripts",
        "conversations_path": skippy_path / "conversations",
        "backup_path": wordpress_path / "backups",
    }


@pytest.fixture
def sample_file(temp_dir):
    """Create a sample file for testing."""
    file_path = temp_dir / "sample.txt"
    content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def mock_env_file(temp_dir):
    """Create a mock .env file."""
    env_file = temp_dir / ".env"
    env_content = """
EBON_HOST=testuser@10.0.0.99
EBON_PASSWORD=testpassword
SKIPPY_BASE_PATH=/test/skippy
WORDPRESS_BASE_PATH=/test/wordpress
"""
    env_file.write_text(env_content)
    return env_file


@pytest.fixture(autouse=True)
def reset_env():
    """Reset environment variables before each test."""
    # Store original environment
    original_env = os.environ.copy()

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
