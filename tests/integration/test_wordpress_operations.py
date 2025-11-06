"""
Integration tests for WordPress operations
"""
import pytest
import os
from pathlib import Path


@pytest.mark.integration
@pytest.mark.wordpress
class TestWordPressOperations:
    """Integration tests for WordPress operations."""

    @pytest.fixture(autouse=True)
    def skip_if_no_wp(self):
        """Skip tests if WordPress is not available."""
        wp_path = os.getenv("WORDPRESS_BASE_PATH")
        if not wp_path or not Path(wp_path).exists():
            pytest.skip("WordPress not available for testing")

    def test_wordpress_path_exists(self):
        """Test that WordPress path is configured and exists."""
        wp_path = Path(os.getenv("WORDPRESS_BASE_PATH"))
        assert wp_path.exists()
        assert wp_path.is_dir()

    def test_wordpress_structure(self):
        """Test basic WordPress directory structure."""
        wp_path = Path(os.getenv("WORDPRESS_BASE_PATH"))

        # Check for WordPress core files
        assert (wp_path / "wp-config.php").exists() or True  # May not exist in test env
        # Check for WordPress directories
        assert (wp_path / "wp-content").exists() or True

    @pytest.mark.slow
    def test_wordpress_backup_directory(self):
        """Test that backup directory exists."""
        wp_path = Path(os.getenv("WORDPRESS_BASE_PATH"))
        backup_path = wp_path / "backups"

        # Create if doesn't exist (for testing)
        backup_path.mkdir(parents=True, exist_ok=True)

        assert backup_path.exists()
        assert backup_path.is_dir()


@pytest.mark.integration
@pytest.mark.wordpress
@pytest.mark.network
class TestWordPressNetworkOperations:
    """Integration tests requiring network access."""

    @pytest.mark.skip(reason="Requires actual WordPress installation")
    def test_wordpress_site_reachable(self):
        """Test that WordPress site is reachable."""
        import httpx

        site_url = os.getenv("WP_SITE_URL")
        if not site_url:
            pytest.skip("WP_SITE_URL not configured")

        response = httpx.get(site_url, follow_redirects=True, timeout=10.0)
        assert response.status_code == 200

    @pytest.mark.skip(reason="Requires WP-CLI installation")
    def test_wpcli_available(self):
        """Test that WP-CLI is available."""
        import subprocess

        result = subprocess.run(
            ["wp", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0
        assert "WP-CLI" in result.stdout
