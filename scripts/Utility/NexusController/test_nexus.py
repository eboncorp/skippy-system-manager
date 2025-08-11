#!/usr/bin/env python3
"""
NexusController v2.0 Test Suite
Comprehensive unit and integration tests
"""

import os
import sys
import json
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import threading
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nexus_controller_v2 import (
    NexusConfig, SecurityManager, SSHManager, NetworkDiscovery,
    CloudIntegration, SystemMonitor, BackupManager, ConfigValidator
)

class TestConfigValidator(unittest.TestCase):
    """Test configuration validation functions"""
    
    def test_validate_ip(self):
        """Test IP address validation"""
        # Valid IPs
        self.assertTrue(ConfigValidator.validate_ip("192.168.1.1"))
        self.assertTrue(ConfigValidator.validate_ip("10.0.0.1"))
        self.assertTrue(ConfigValidator.validate_ip("127.0.0.1"))
        self.assertTrue(ConfigValidator.validate_ip("::1"))
        
        # Invalid IPs
        self.assertFalse(ConfigValidator.validate_ip("256.256.256.256"))
        self.assertFalse(ConfigValidator.validate_ip("192.168"))
        self.assertFalse(ConfigValidator.validate_ip("invalid"))
        self.assertFalse(ConfigValidator.validate_ip(""))
    
    def test_validate_network_range(self):
        """Test network range validation"""
        # Valid ranges
        self.assertTrue(ConfigValidator.validate_network_range("192.168.1.0/24"))
        self.assertTrue(ConfigValidator.validate_network_range("10.0.0.0/8"))
        self.assertTrue(ConfigValidator.validate_network_range("172.16.0.0/12"))
        
        # Invalid ranges
        self.assertFalse(ConfigValidator.validate_network_range("192.168.1.0/33"))
        self.assertFalse(ConfigValidator.validate_network_range("invalid/24"))
        self.assertFalse(ConfigValidator.validate_network_range("192.168.1.0"))
    
    def test_validate_port(self):
        """Test port number validation"""
        # Valid ports
        self.assertTrue(ConfigValidator.validate_port(22))
        self.assertTrue(ConfigValidator.validate_port(80))
        self.assertTrue(ConfigValidator.validate_port(443))
        self.assertTrue(ConfigValidator.validate_port(65535))
        
        # Invalid ports
        self.assertFalse(ConfigValidator.validate_port(0))
        self.assertFalse(ConfigValidator.validate_port(-1))
        self.assertFalse(ConfigValidator.validate_port(65536))
        self.assertFalse(ConfigValidator.validate_port(100000))
    
    def test_sanitize_command(self):
        """Test command sanitization"""
        # Test removal of dangerous characters
        self.assertEqual(ConfigValidator.sanitize_command("ls -la"), "ls -la")
        self.assertEqual(ConfigValidator.sanitize_command("ls; rm -rf /"), "ls rm -rf /")
        self.assertEqual(ConfigValidator.sanitize_command("cat file | grep test"), "cat file  grep test")
        self.assertEqual(ConfigValidator.sanitize_command("echo $HOME"), "echo HOME")
        self.assertEqual(ConfigValidator.sanitize_command("cmd `whoami`"), "cmd whoami")

class TestNexusConfig(unittest.TestCase):
    """Test NexusConfig class"""
    
    def setUp(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_home = Path(self.temp_dir)
        
        # Mock Path.home() to return our temp directory
        self.home_patcher = patch.object(Path, 'home', return_value=self.test_home)
        self.home_patcher.start()
    
    def tearDown(self):
        """Cleanup test environment"""
        self.home_patcher.stop()
        shutil.rmtree(self.temp_dir)
    
    def test_config_initialization(self):
        """Test configuration initialization"""
        config = NexusConfig()
        
        # Check default values
        self.assertEqual(config.default_network, "10.0.0.0/24")
        self.assertEqual(config.scan_timeout, 120)
        self.assertEqual(config.ssh_timeout, 30)
        
        # Check directories are created
        self.assertTrue(config.base_dir.exists())
        self.assertTrue(config.config_dir.exists())
        self.assertTrue(config.logs_dir.exists())
        self.assertTrue(config.keys_dir.exists())
        self.assertTrue(config.backup_dir.exists())
        
        # Check permissions
        self.assertEqual(oct(config.base_dir.stat().st_mode)[-3:], "700")

class TestSecurityManager(unittest.TestCase):
    """Test SecurityManager class"""
    
    def setUp(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_home = Path(self.temp_dir)
        
        # Mock Path.home()
        self.home_patcher = patch.object(Path, 'home', return_value=self.test_home)
        self.home_patcher.start()
        
        self.config = NexusConfig()
        self.security = SecurityManager(self.config)
    
    def tearDown(self):
        """Cleanup test environment"""
        self.home_patcher.stop()
        shutil.rmtree(self.temp_dir)
    
    def test_encryption_initialization(self):
        """Test encryption setup"""
        # Check key file is created
        self.assertTrue(self.security.key_file.exists())
        
        # Check key file permissions
        self.assertEqual(oct(self.security.key_file.stat().st_mode)[-3:], "600")
        
        # Check cipher is initialized
        self.assertIsNotNone(self.security.cipher)
    
    def test_data_encryption(self):
        """Test data encryption and decryption"""
        test_data = "This is sensitive data"
        
        # Encrypt data
        encrypted = self.security.encrypt_data(test_data)
        self.assertIsInstance(encrypted, bytes)
        self.assertNotEqual(encrypted, test_data.encode())
        
        # Decrypt data
        decrypted = self.security.decrypt_data(encrypted)
        self.assertEqual(decrypted, test_data)
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "test_password_123"
        
        # Hash password
        key, salt = self.security.hash_password(password)
        self.assertIsInstance(key, bytes)
        self.assertIsInstance(salt, bytes)
        self.assertEqual(len(key), 32)
        self.assertEqual(len(salt), 32)
        
        # Verify password
        self.assertTrue(self.security.verify_password(password, key, salt))
        self.assertFalse(self.security.verify_password("wrong_password", key, salt))
    
    def test_api_key_generation(self):
        """Test API key generation"""
        api_key = self.security.generate_api_key()
        
        self.assertIsInstance(api_key, str)
        self.assertGreater(len(api_key), 32)
        
        # Test uniqueness
        api_key2 = self.security.generate_api_key()
        self.assertNotEqual(api_key, api_key2)

class TestSSHManager(unittest.TestCase):
    """Test SSHManager class"""
    
    def setUp(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_home = Path(self.temp_dir)
        
        # Mock Path.home()
        self.home_patcher = patch.object(Path, 'home', return_value=self.test_home)
        self.home_patcher.start()
        
        self.config = NexusConfig()
        self.security = SecurityManager(self.config)
        self.ssh_manager = SSHManager(self.security, self.config)
    
    def tearDown(self):
        """Cleanup test environment"""
        self.home_patcher.stop()
        shutil.rmtree(self.temp_dir)
    
    def test_hostname_validation(self):
        """Test hostname validation"""
        # Valid hostnames
        self.assertTrue(self.ssh_manager._is_valid_hostname("example.com"))
        self.assertTrue(self.ssh_manager._is_valid_hostname("sub.example.com"))
        self.assertTrue(self.ssh_manager._is_valid_hostname("host123"))
        self.assertTrue(self.ssh_manager._is_valid_hostname("my-server"))
        
        # Invalid hostnames
        self.assertFalse(self.ssh_manager._is_valid_hostname(""))
        self.assertFalse(self.ssh_manager._is_valid_hostname("-invalid"))
        self.assertFalse(self.ssh_manager._is_valid_hostname("invalid-"))
        self.assertFalse(self.ssh_manager._is_valid_hostname("in..valid"))
    
    def test_connection_validation(self):
        """Test connection parameter validation"""
        # Test invalid IP
        with self.assertRaises(ValueError):
            self.ssh_manager.connect("999.999.999.999", "user")
        
        # Test invalid port
        with self.assertRaises(ValueError):
            self.ssh_manager.connect("192.168.1.1", "user", port=70000)
        
        # Test invalid key path
        with self.assertRaises(ValueError):
            self.ssh_manager.connect("192.168.1.1", "user", key_path="/nonexistent/key")
    
    @patch('paramiko.SSHClient')
    @patch('subprocess.run')
    def test_host_key_scanning(self, mock_subprocess, mock_ssh_client):
        """Test host key scanning functionality"""
        # Mock subprocess return
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "host.example.com ssh-rsa AAAAB3NzaC1yc2E..."
        
        # Test host key scanning
        result = self.ssh_manager._scan_and_verify_host("host.example.com", 22)
        self.assertTrue(result)
        
        # Check that ssh-keyscan was called
        mock_subprocess.assert_called_once()
        args = mock_subprocess.call_args[0][0]
        self.assertIn('ssh-keyscan', args)
        self.assertIn('host.example.com', args)

class TestNetworkDiscovery(unittest.TestCase):
    """Test NetworkDiscovery class"""
    
    def setUp(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_home = Path(self.temp_dir)
        
        # Mock Path.home()
        self.home_patcher = patch.object(Path, 'home', return_value=self.test_home)
        self.home_patcher.start()
        
        self.config = NexusConfig()
        self.discovery = NetworkDiscovery(self.config)
    
    def tearDown(self):
        """Cleanup test environment"""
        self.home_patcher.stop()
        shutil.rmtree(self.temp_dir)
    
    def test_network_range_validation(self):
        """Test network range validation in scan"""
        # Test invalid network range
        with self.assertRaises(ValueError):
            self.discovery.scan_network("invalid_range")
    
    @patch('shutil.which')
    def test_nmap_availability_check(self, mock_which):
        """Test nmap availability checking"""
        # Mock nmap not available
        mock_which.return_value = None
        
        with self.assertRaises(RuntimeError):
            self.discovery.scan_network("192.168.1.0/24")
    
    def test_nmap_output_parsing(self):
        """Test nmap output parsing"""
        sample_output = """
        Nmap scan report for router.local (192.168.1.1)
        Host is up (0.0012s latency).
        MAC Address: AA:BB:CC:DD:EE:FF (Vendor Corp)
        
        Nmap scan report for ebon-server (192.168.1.100)
        Host is up (0.0034s latency).
        MAC Address: 11:22:33:44:55:66 (Server Vendor)
        """
        
        devices = self.discovery._parse_nmap_output(sample_output)
        
        self.assertEqual(len(devices), 2)
        self.assertIn("192.168.1.1", devices)
        self.assertIn("192.168.1.100", devices)
        
        # Check first device
        router = devices["192.168.1.1"]
        self.assertEqual(router['hostname'], "router.local")
        self.assertEqual(router['mac'], "AA:BB:CC:DD:EE:FF")
        self.assertEqual(router['vendor'], "Vendor Corp")
        
        # Check second device
        server = devices["192.168.1.100"]
        self.assertEqual(server['hostname'], "ebon-server")
        self.assertEqual(server['mac'], "11:22:33:44:55:66")
        self.assertEqual(server['vendor'], "Server Vendor")
    
    def test_server_identification(self):
        """Test server identification by hostname prefix"""
        # Setup test devices
        self.discovery.discovered_devices = {
            "192.168.1.1": {"hostname": "router.local", "ip": "192.168.1.1"},
            "192.168.1.100": {"hostname": "ebon-server", "ip": "192.168.1.100"},
            "192.168.1.101": {"hostname": "ebon-media", "ip": "192.168.1.101"},
            "192.168.1.102": {"hostname": "desktop", "ip": "192.168.1.102"}
        }
        
        servers = self.discovery.identify_servers("ebon")
        self.assertEqual(len(servers), 2)
        
        server_ips = [device['ip'] for device in servers]
        self.assertIn("192.168.1.100", server_ips)
        self.assertIn("192.168.1.101", server_ips)

class TestSystemMonitor(unittest.TestCase):
    """Test SystemMonitor class"""
    
    def setUp(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_home = Path(self.temp_dir)
        
        # Mock Path.home()
        self.home_patcher = patch.object(Path, 'home', return_value=self.test_home)
        self.home_patcher.start()
        
        self.config = NexusConfig()
        self.monitor = SystemMonitor(self.config)
    
    def tearDown(self):
        """Cleanup test environment"""
        self.home_patcher.stop()
        shutil.rmtree(self.temp_dir)
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_partitions')
    @patch('psutil.net_io_counters')
    @patch('psutil.pids')
    @patch('psutil.process_iter')
    def test_metrics_collection(self, mock_process_iter, mock_pids, mock_net_io,
                               mock_disk_partitions, mock_virtual_memory, mock_cpu_percent):
        """Test system metrics collection"""
        # Mock psutil functions
        mock_cpu_percent.return_value = 25.5
        
        mock_memory = Mock()
        mock_memory.percent = 45.2
        mock_memory.available = 4000000000
        mock_memory.total = 8000000000
        mock_virtual_memory.return_value = mock_memory
        
        mock_partition = Mock()
        mock_partition.mountpoint = "/"
        mock_disk_partitions.return_value = [mock_partition]
        
        mock_net = Mock()
        mock_net.bytes_sent = 1000000
        mock_net.bytes_recv = 2000000
        mock_net.packets_sent = 1000
        mock_net.packets_recv = 2000
        mock_net.errin = 0
        mock_net.errout = 0
        mock_net_io.return_value = mock_net
        
        mock_pids.return_value = [1, 2, 3, 4, 5]
        
        mock_process = Mock()
        mock_process.info = {'status': 'running'}
        mock_process_iter.return_value = [mock_process] * 3
        
        # Mock disk usage
        with patch('psutil.disk_usage') as mock_disk_usage:
            mock_usage = Mock()
            mock_usage.percent = 65.0
            mock_usage.free = 1000000000
            mock_usage.total = 3000000000
            mock_disk_usage.return_value = mock_usage
            
            # Collect metrics
            metrics = self.monitor.collect_metrics()
            
            # Verify metrics structure
            self.assertIn('timestamp', metrics)
            self.assertIn('cpu', metrics)
            self.assertIn('memory', metrics)
            self.assertIn('disk', metrics)
            self.assertIn('network', metrics)
            self.assertIn('processes', metrics)
            
            # Verify CPU metrics
            self.assertEqual(metrics['cpu']['percent'], 25.5)
            
            # Verify memory metrics
            self.assertEqual(metrics['memory']['percent'], 45.2)
            
            # Verify process metrics
            self.assertEqual(metrics['processes']['total'], 5)
            self.assertEqual(metrics['processes']['running'], 3)
    
    def test_threshold_checking(self):
        """Test alert threshold checking"""
        # Setup test metrics that exceed thresholds
        test_metrics = {
            'cpu': {'percent': 85.0},  # Above 80% threshold
            'memory': {'percent': 90.0},  # Above 85% threshold
            'disk': {'/': {'percent': 95.0}},  # Above 90% threshold
            'network': {'errin': 50, 'errout': 60}  # Above 100 errors threshold
        }
        
        # Clear existing alerts
        self.monitor.alerts = []
        
        # Check thresholds
        self.monitor._check_thresholds(test_metrics)
        
        # Verify alerts were created
        self.assertGreater(len(self.monitor.alerts), 0)
        
        # Check for specific alerts
        alert_types = [alert['type'] for alert in self.monitor.alerts]
        self.assertIn('HIGH_CPU', alert_types)
        self.assertIn('HIGH_MEMORY', alert_types)
        self.assertIn('HIGH_DISK', alert_types)

class TestBackupManager(unittest.TestCase):
    """Test BackupManager class"""
    
    def setUp(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_home = Path(self.temp_dir)
        
        # Mock Path.home()
        self.home_patcher = patch.object(Path, 'home', return_value=self.test_home)
        self.home_patcher.start()
        
        self.config = NexusConfig()
        self.security = SecurityManager(self.config)
        self.backup_manager = BackupManager(self.config, self.security)
    
    def tearDown(self):
        """Cleanup test environment"""
        self.home_patcher.stop()
        shutil.rmtree(self.temp_dir)
    
    def test_manifest_initialization(self):
        """Test backup manifest initialization"""
        self.assertIsInstance(self.backup_manager.manifest, dict)
        self.assertIn('backups', self.backup_manager.manifest)
        self.assertIn('last_backup', self.backup_manager.manifest)
    
    @patch('subprocess.run')
    def test_backup_creation(self, mock_subprocess):
        """Test backup creation process"""
        # Mock successful tar command
        mock_subprocess.return_value.returncode = 0
        
        # Create some test files to backup
        test_config_file = self.config.config_dir / "test.json"
        test_config_file.write_text('{"test": "data"}')
        
        test_key_file = self.config.keys_dir / "test.key"
        test_key_file.write_bytes(b"test key data")
        
        # Create backup
        result = self.backup_manager.create_backup("test")
        
        # Verify backup was created
        self.assertTrue(result)
        self.assertEqual(len(self.backup_manager.manifest['backups']), 1)
        
        backup_info = self.backup_manager.manifest['backups'][0]
        self.assertEqual(backup_info['type'], 'test')
        self.assertIn('timestamp', backup_info)
        self.assertIn('size', backup_info)

class TestIntegration(unittest.TestCase):
    """Integration tests for component interaction"""
    
    def setUp(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_home = Path(self.temp_dir)
        
        # Mock Path.home()
        self.home_patcher = patch.object(Path, 'home', return_value=self.test_home)
        self.home_patcher.start()
        
        # Initialize components
        self.config = NexusConfig()
        self.security = SecurityManager(self.config)
    
    def tearDown(self):
        """Cleanup test environment"""
        self.home_patcher.stop()
        shutil.rmtree(self.temp_dir)
    
    def test_security_configuration_integration(self):
        """Test security manager and configuration integration"""
        # Test that security manager properly uses configuration
        self.assertEqual(self.security.config_dir, self.config.keys_dir.parent / "config")
        
        # Test encryption/decryption with configuration data
        config_data = {
            "test_setting": "sensitive_value",
            "another_setting": 12345
        }
        
        config_json = json.dumps(config_data)
        encrypted = self.security.encrypt_data(config_json)
        decrypted = self.security.decrypt_data(encrypted)
        
        self.assertEqual(json.loads(decrypted), config_data)
    
    def test_cloud_integration_security(self):
        """Test cloud integration with security manager"""
        cloud = CloudIntegration(self.config, self.security)
        
        # Test that cloud providers configuration is properly encrypted
        test_providers = {
            "aws": {
                "access_key": "test_key",
                "secret_key": "test_secret"
            }
        }
        
        cloud.providers = test_providers
        cloud.save_providers()
        
        # Reload and verify
        cloud2 = CloudIntegration(self.config, self.security)
        self.assertEqual(cloud2.providers, test_providers)

class TestThreadSafety(unittest.TestCase):
    """Test thread safety of components"""
    
    def setUp(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_home = Path(self.temp_dir)
        
        # Mock Path.home()
        self.home_patcher = patch.object(Path, 'home', return_value=self.test_home)
        self.home_patcher.start()
        
        self.config = NexusConfig()
        self.security = SecurityManager(self.config)
    
    def tearDown(self):
        """Cleanup test environment"""
        self.home_patcher.stop()
        shutil.rmtree(self.temp_dir)
    
    def test_concurrent_encryption(self):
        """Test concurrent encryption operations"""
        results = []
        errors = []
        
        def encrypt_data(data):
            try:
                encrypted = self.security.encrypt_data(data)
                decrypted = self.security.decrypt_data(encrypted)
                results.append(decrypted == data)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=encrypt_data, args=(f"test_data_{i}",))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        self.assertEqual(len(errors), 0, f"Encryption errors: {errors}")
        self.assertEqual(len(results), 10)
        self.assertTrue(all(results))

def run_tests():
    """Run all tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestConfigValidator,
        TestNexusConfig,
        TestSecurityManager,
        TestSSHManager,
        TestNetworkDiscovery,
        TestSystemMonitor,
        TestBackupManager,
        TestIntegration,
        TestThreadSafety
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)