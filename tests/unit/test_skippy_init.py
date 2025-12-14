"""
Unit tests for lib/python/__init__.py

Tests cover:
- Package metadata attributes (__version__, __author__, etc.)
- __all__ exports list
"""
import pytest
import sys
from pathlib import Path

# Add lib directory to path
lib_path = Path(__file__).parent.parent.parent / "lib" / "python"
sys.path.insert(0, str(lib_path))


@pytest.mark.unit
class TestPackageMetadata:
    """Test package metadata attributes."""

    def test_version_defined(self):
        """Test __version__ is defined and is a string."""
        from lib.python import __version__
        assert __version__ is not None
        assert isinstance(__version__, str)
        assert len(__version__) > 0

    def test_version_format(self):
        """Test __version__ follows semver format."""
        from lib.python import __version__
        parts = __version__.split(".")
        # Should have at least major.minor.patch
        assert len(parts) >= 2
        # Each part should be numeric (except possible suffix)
        assert parts[0].isdigit()
        assert parts[1].isdigit()

    def test_author_defined(self):
        """Test __author__ is defined."""
        from lib.python import __author__
        assert __author__ is not None
        assert isinstance(__author__, str)
        assert len(__author__) > 0

    def test_email_defined(self):
        """Test __email__ is defined and looks like an email."""
        from lib.python import __email__
        assert __email__ is not None
        assert isinstance(__email__, str)
        assert "@" in __email__
        assert "." in __email__

    def test_license_defined(self):
        """Test __license__ is defined."""
        from lib.python import __license__
        assert __license__ is not None
        assert isinstance(__license__, str)
        assert len(__license__) > 0


@pytest.mark.unit
class TestPackageExports:
    """Test __all__ exports."""

    def test_all_defined(self):
        """Test __all__ is defined and is a list."""
        from lib.python import __all__
        assert __all__ is not None
        assert isinstance(__all__, list)
        assert len(__all__) > 0

    def test_all_contains_expected_modules(self):
        """Test __all__ contains expected module names."""
        from lib.python import __all__
        expected_modules = [
            "skippy_validator",
            "skippy_logger",
            "skippy_errors",
            "skippy_performance",
        ]
        for module in expected_modules:
            assert module in __all__, f"{module} should be in __all__"

    def test_all_entries_are_strings(self):
        """Test all entries in __all__ are strings."""
        from lib.python import __all__
        for entry in __all__:
            assert isinstance(entry, str)
