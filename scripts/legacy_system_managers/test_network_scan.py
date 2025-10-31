#!/usr/bin/env python3
"""
Unit tests for Active Network Scanner v2.0
Tests async operations, error handling, and device identification
"""

import unittest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path
import tempfile
import json
from datetime import datetime
import ipaddress

# Import the module to test
from active_network_scan_v2 import NetworkDevice, NetworkScanner


class TestNetworkDevice(unittest.TestCase):
    """Test NetworkDevice dataclass"""

    def test_device_creation(self):
        """Test creating a NetworkDevice"""
        device = NetworkDevice(
            ip_address="192.168.1.100",
            mac_address="AA:BB:CC:DD:EE:FF",
            hostname="test-device",
            vendor="TestVendor"
        )
        self.assertEqual(device.ip_address, "192.168.1.100")
        self.assertEqual(device.mac_address, "AA:BB:CC:DD:EE:FF")
        self.assertIsNotNone(device.last_seen)
        self.assertEqual(device.services, [])

    def test_device_to_dict(self):
        """Test converting device to dictionary"""
        device = NetworkDevice(
            ip_address="192.168.1.100",
            services=["SSH", "HTTP"]
        )
        data = device.to_dict()
        self.assertIn('ip_address', data)
        self.assertIn('services', data)
        self.assertIn('last_seen', data)
        self.assertEqual(data['services'], ["SSH", "HTTP"])


class TestNetworkScanner(unittest.TestCase):
    """Test NetworkScanner class"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.scanner = NetworkScanner(cache_dir=Path(self.temp_dir))

    def tearDown(self):
        """Clean up after tests"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_operations(self):
        """Test cache save and load operations"""
        # Add some devices
        device1 = NetworkDevice(ip_address="192.168.1.100", hostname="device1")
        device2 = NetworkDevice(ip_address="192.168.1.101", hostname="device2")

        self.scanner.devices = {
            "192.168.1.100": device1,
            "192.168.1.101": device2
        }

        # Save cache
        self.scanner.save_cache()
        self.assertTrue(self.scanner.cache_file.exists())

        # Create new scanner and load cache
        scanner2 = NetworkScanner(cache_dir=Path(self.temp_dir))
        self.assertEqual(len(scanner2.devices), 2)
        self.assertIn("192.168.1.100", scanner2.devices)
        self.assertEqual(scanner2.devices["192.168.1.100"].hostname, "device1")

    def test_classify_device(self):
        """Test device classification logic"""
        # Test media server
        device = NetworkDevice(
            ip_address="192.168.1.100",
            services=["SSH", "Jellyfin", "HTTP"]
        )
        device_type = self.scanner._classify_device(device)
        self.assertEqual(device_type, "Media Server")

        # Test Windows PC
        device = NetworkDevice(
            ip_address="192.168.1.101",
            services=["RDP", "SMB"]
        )
        device_type = self.scanner._classify_device(device)
        self.assertEqual(device_type, "Windows PC")

        # Test Raspberry Pi
        device = NetworkDevice(
            ip_address="192.168.1.102",
            vendor="Raspberry Pi"
        )
        device_type = self.scanner._classify_device(device)
        self.assertEqual(device_type, "Raspberry Pi")

    @patch('active_network_scan_v2.asyncio.create_subprocess_exec')
    async def test_get_network_info(self, mock_subprocess):
        """Test getting network information"""
        # Mock subprocess output
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (
            b"default via 192.168.1.1 dev eth0\n",
            b""
        )

        mock_proc2 = AsyncMock()
        mock_proc2.communicate.return_value = (
            b"    inet 192.168.1.100/24 brd 192.168.1.255 scope global eth0\n",
            b""
        )

        mock_subprocess.side_effect = [mock_proc, mock_proc2]

        result = await self.scanner.get_network_info()
        self.assertIsNotNone(result)
        our_ip, gateway, subnet, interface = result
        self.assertEqual(our_ip, "192.168.1.100")
        self.assertEqual(gateway, "192.168.1.1")
        self.assertEqual(interface, "eth0")

    @patch('active_network_scan_v2.asyncio.create_subprocess_exec')
    async def test_ping_host(self, mock_subprocess):
        """Test pinging a host"""
        # Mock successful ping
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"", b"")
        mock_subprocess.return_value = mock_proc

        ip, is_alive, response_time = await self.scanner.ping_host("192.168.1.100")
        self.assertEqual(ip, "192.168.1.100")
        self.assertTrue(is_alive)
        self.assertIsNotNone(response_time)

        # Mock failed ping
        mock_proc.returncode = 1
        ip, is_alive, response_time = await self.scanner.ping_host("192.168.1.200")
        self.assertEqual(ip, "192.168.1.200")
        self.assertFalse(is_alive)
        self.assertIsNone(response_time)

    @patch('active_network_scan_v2.asyncio.create_subprocess_exec')
    async def test_get_mac_address(self, mock_subprocess):
        """Test getting MAC address"""
        # Mock ARP table output
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (
            b"192.168.1.100 dev eth0 lladdr aa:bb:cc:dd:ee:ff REACHABLE\n",
            b""
        )
        mock_subprocess.return_value = mock_proc

        mac = await self.scanner.get_mac_address("192.168.1.100")
        self.assertEqual(mac, "AA:BB:CC:DD:EE:FF")

        # Test no MAC found
        mock_proc.communicate.return_value = (b"", b"")
        mac = await self.scanner.get_mac_address("192.168.1.200")
        self.assertIsNone(mac)

    @patch('active_network_scan_v2.asyncio.open_connection')
    async def test_scan_port(self, mock_connection):
        """Test port scanning"""
        # Mock open port
        mock_writer = AsyncMock()
        mock_connection.return_value = (None, mock_writer)

        is_open = await self.scanner.scan_port("192.168.1.100", 22)
        self.assertTrue(is_open)
        mock_writer.close.assert_called_once()

        # Mock closed port
        mock_connection.side_effect = asyncio.TimeoutError()
        is_open = await self.scanner.scan_port("192.168.1.100", 12345)
        self.assertFalse(is_open)

    async def test_identify_device(self):
        """Test device identification"""
        device = NetworkDevice(
            ip_address="192.168.1.100",
            mac_address="B8:27:EB:12:34:56"  # Raspberry Pi MAC
        )

        # Mock port scan results
        with patch.object(self.scanner, 'scan_port') as mock_scan:
            # SSH is open, HTTP is open, others closed
            mock_scan.side_effect = [
                True,   # SSH
                False,  # Telnet
                False,  # SMTP
                False,  # DNS
                True,   # HTTP
                False,  # POP3
                False,  # IMAP
                False,  # HTTPS
                False,  # SMB
                False,  # MySQL
                False,  # RDP
                False,  # PostgreSQL
                False,  # VNC
                False,  # HTTP-Alt
                False,  # Jellyfin
                False,  # Cockpit
                False,  # Webmin
            ]

            await self.scanner.identify_device(device)

        self.assertEqual(device.vendor, "Raspberry Pi")
        self.assertIn("SSH", device.services)
        self.assertIn("HTTP", device.services)
        self.assertEqual(device.device_type, "Raspberry Pi")


class TestNetworkScanIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for network scanning"""

    async def test_scan_network_invalid_subnet(self):
        """Test scanning with invalid subnet"""
        scanner = NetworkScanner()
        devices = await scanner.scan_network("invalid_subnet")
        self.assertEqual(devices, [])

    @patch('active_network_scan_v2.NetworkScanner.get_network_info')
    @patch('active_network_scan_v2.NetworkScanner.ping_host')
    @patch('active_network_scan_v2.NetworkScanner.get_mac_address')
    @patch('active_network_scan_v2.NetworkScanner.get_hostname')
    @patch('active_network_scan_v2.NetworkScanner.identify_device')
    async def test_scan_network_success(self, mock_identify, mock_hostname,
                                       mock_mac, mock_ping, mock_network):
        """Test successful network scan"""
        scanner = NetworkScanner()

        # Mock network info
        mock_network.return_value = ("192.168.1.100", "192.168.1.1", "192.168.1.0", "eth0")

        # Mock ping results - only 2 hosts alive
        async def ping_side_effect(ip):
            if ip in ["192.168.1.1", "192.168.1.100"]:
                return ip, True, 0.001
            return ip, False, None

        mock_ping.side_effect = ping_side_effect

        # Mock MAC addresses
        async def mac_side_effect(ip):
            if ip == "192.168.1.1":
                return "AA:BB:CC:DD:EE:FF"
            elif ip == "192.168.1.100":
                return "11:22:33:44:55:66"
            return None

        mock_mac.side_effect = mac_side_effect

        # Mock hostnames
        async def hostname_side_effect(ip):
            if ip == "192.168.1.1":
                return ("router.local", [], [])
            elif ip == "192.168.1.100":
                return ("mycomputer.local", [], [])
            return None

        mock_hostname.side_effect = hostname_side_effect

        # Mock device identification
        mock_identify.return_value = None

        # Run scan
        devices = await scanner.scan_network("192.168.1.0/24")

        # Verify results
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0].ip_address, "192.168.1.1")
        self.assertEqual(devices[1].ip_address, "192.168.1.100")


def run_tests():
    """Run all tests with verbose output"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestNetworkDevice))
    suite.addTests(loader.loadTestsFromTestCase(TestNetworkScanner))
    suite.addTests(loader.loadTestsFromTestCase(TestNetworkScanIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    if result.wasSuccessful():
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")

    return result.wasSuccessful()


if __name__ == "__main__":
    # Run tests
    success = run_tests()

    # Exit with appropriate code
    exit(0 if success else 1)