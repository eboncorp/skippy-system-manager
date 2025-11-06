"""
Integration tests for SSH connectivity
"""
import pytest
import os
from pathlib import Path


@pytest.mark.integration
@pytest.mark.ssh
@pytest.mark.network
class TestSSHConnectivity:
    """Integration tests for SSH connectivity."""

    @pytest.fixture(autouse=True)
    def skip_if_no_ssh_config(self):
        """Skip tests if SSH is not configured."""
        ebon_host = os.getenv("EBON_HOST")
        ebon_password = os.getenv("EBON_PASSWORD")

        if not ebon_host or not ebon_password:
            pytest.skip("SSH not configured for testing")

    @pytest.mark.skip(reason="Requires actual SSH server")
    def test_ssh_connection(self):
        """Test SSH connection to remote server."""
        import paramiko

        ebon_host = os.getenv("EBON_HOST")
        ebon_password = os.getenv("EBON_PASSWORD")

        # Parse user@host
        if "@" in ebon_host:
            username, hostname = ebon_host.split("@")
        else:
            pytest.skip("EBON_HOST format invalid")

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(
                hostname,
                username=username,
                password=ebon_password,
                timeout=10
            )
            # Test command execution
            stdin, stdout, stderr = client.exec_command("echo 'test'")
            output = stdout.read().decode().strip()
            assert output == "test"
        finally:
            client.close()

    @pytest.mark.skip(reason="Requires SSH keys to be set up")
    def test_ssh_key_authentication(self):
        """Test SSH key-based authentication."""
        import paramiko

        ebon_host = os.getenv("EBON_HOST")
        ssh_key_path = os.getenv("SSH_PRIVATE_KEY")

        if not ssh_key_path:
            pytest.skip("SSH_PRIVATE_KEY not configured")

        if "@" in ebon_host:
            username, hostname = ebon_host.split("@")
        else:
            pytest.skip("EBON_HOST format invalid")

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(
                hostname,
                username=username,
                key_filename=ssh_key_path,
                timeout=10
            )
            assert client.get_transport().is_active()
        finally:
            client.close()

    def test_ssh_config_validation(self):
        """Test that SSH configuration is valid."""
        ebon_host = os.getenv("EBON_HOST")

        # Check format
        assert "@" in ebon_host, "EBON_HOST should be in format user@host"

        username, hostname = ebon_host.split("@")
        assert len(username) > 0, "SSH username cannot be empty"
        assert len(hostname) > 0, "SSH hostname cannot be empty"

        # Check hostname format (basic validation)
        assert "." in hostname or hostname == "localhost", \
            "Hostname should be an IP address or domain"
