#!/usr/bin/env python3
"""
NexusController Secure - Enterprise Security Implementation
Comprehensive security with YubiKey 5 FIDO2/WebAuthn support
"""

import sys
import os
import json
import subprocess
import socket
import time
import hashlib
import hmac
import secrets
import base64
import logging
import getpass
from datetime import datetime, timedelta
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import paramiko
import requests

# Try to import YubiKey libraries
try:
    from fido2.hid import CtapHidDevice
    from fido2.client import Fido2Client, ClientError
    from fido2.server import Fido2Server
    from fido2 import cbor
    YUBIKEY_AVAILABLE = True
except ImportError:
    YUBIKEY_AVAILABLE = False
    print("⚠️  YubiKey libraries not installed. Install with: pip install fido2")

# Try to import advanced crypto
try:
    import cryptography
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️  Cryptography library not installed. Install with: pip install cryptography")

class SecureConfig:
    """Encrypted configuration manager"""
    
    def __init__(self, config_path=None):
        self.config_path = config_path or Path.home() / '.nexus' / 'config.enc'
        self.config_dir = self.config_path.parent
        self.config_dir.mkdir(mode=0o700, exist_ok=True)
        self.master_key = None
        self.config_data = {}
        
    def derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password"""
        if not CRYPTO_AVAILABLE:
            return password.encode()[:32].ljust(32, b'0')
            
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def encrypt_config(self, data: dict, password: str) -> None:
        """Encrypt and save configuration"""
        if not CRYPTO_AVAILABLE:
            # Fallback: base64 encoding (not secure, but functional)
            encoded = base64.b64encode(json.dumps(data).encode())
            self.config_path.write_bytes(encoded)
            return
            
        salt = os.urandom(16)
        key = self.derive_key(password, salt)
        f = Fernet(key)
        
        encrypted_data = f.encrypt(json.dumps(data).encode())
        
        # Store salt + encrypted data
        with open(self.config_path, 'wb') as file:
            file.write(salt + encrypted_data)
        
        # Set secure permissions
        os.chmod(self.config_path, 0o600)
    
    def decrypt_config(self, password: str) -> dict:
        """Decrypt and load configuration"""
        if not self.config_path.exists():
            return {}
            
        if not CRYPTO_AVAILABLE:
            # Fallback: base64 decoding
            encoded = self.config_path.read_bytes()
            return json.loads(base64.b64decode(encoded))
            
        with open(self.config_path, 'rb') as file:
            data = file.read()
        
        salt = data[:16]
        encrypted_data = data[16:]
        
        key = self.derive_key(password, salt)
        f = Fernet(key)
        
        try:
            decrypted_data = f.decrypt(encrypted_data)
            return json.loads(decrypted_data)
        except Exception as e:
            raise ValueError("Invalid password or corrupted config") from e

class YubiKeyAuth:
    """YubiKey FIDO2/WebAuthn authentication"""
    
    def __init__(self):
        self.client = None
        self.server = None
        self.rp_id = "nexus.local"
        self.rp_name = "NexusController"
        
        if YUBIKEY_AVAILABLE:
            try:
                devices = list(CtapHidDevice.list_devices())
                if devices:
                    self.client = Fido2Client(devices[0])
                    self.server = Fido2Server({"id": self.rp_id, "name": self.rp_name})
                    print("🔐 YubiKey detected and ready")
                else:
                    print("⚠️  No YubiKey devices found")
            except Exception as e:
                print(f"⚠️  YubiKey initialization failed: {e}")
    
    def register_yubikey(self, username: str) -> dict:
        """Register YubiKey for user"""
        if not self.client or not self.server:
            raise RuntimeError("YubiKey not available")
            
        user = {"id": username.encode(), "name": username, "displayName": username}
        
        creation_options, state = self.server.register_begin(
            user, resident_key_requirement="discouraged"
        )
        
        print("🔐 Touch your YubiKey to register...")
        
        try:
            result = self.client.make_credential(creation_options["publicKey"])
            auth_data = self.server.register_complete(state, result.client_data, result.attestation_object)
            
            return {
                "credential_id": base64.b64encode(auth_data.credential_data.credential_id).decode(),
                "public_key": base64.b64encode(auth_data.credential_data.public_key).decode(),
                "username": username,
                "registered_at": datetime.now().isoformat()
            }
        except ClientError as e:
            raise RuntimeError(f"YubiKey registration failed: {e}")
    
    def authenticate_yubikey(self, username: str, credential_data: dict) -> bool:
        """Authenticate using YubiKey"""
        if not self.client or not self.server:
            return False
            
        credential_id = base64.b64decode(credential_data["credential_id"])
        
        auth_options, state = self.server.authenticate_begin([credential_id])
        
        print("🔐 Touch your YubiKey to authenticate...")
        
        try:
            result = self.client.get_assertion(auth_options["publicKey"])
            self.server.authenticate_complete(
                state,
                [credential_id],
                result.client_data,
                result.authenticator_data,
                result.signature
            )
            return True
        except ClientError as e:
            print(f"❌ YubiKey authentication failed: {e}")
            return False

class SecureLogger:
    """Secure audit logging"""
    
    def __init__(self, log_dir=None):
        self.log_dir = Path(log_dir or Path.home() / '.nexus' / 'logs')
        self.log_dir.mkdir(mode=0o700, exist_ok=True)
        
        # Setup main logger
        self.logger = logging.getLogger('nexus_secure')
        self.logger.setLevel(logging.INFO)
        
        # Create formatters
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler with rotation
        log_file = self.log_dir / f"nexus_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.WARNING)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Set secure permissions on log file
        os.chmod(log_file, 0o600)
    
    def log_event(self, event_type: str, details: dict):
        """Log security event"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user": os.getenv("USER", "unknown"),
            "pid": os.getpid(),
            **details
        }
        
        self.logger.info(json.dumps(log_entry))
    
    def log_auth_attempt(self, username: str, method: str, success: bool, details: str = ""):
        """Log authentication attempt"""
        self.log_event("auth_attempt", {
            "username": username,
            "method": method,
            "success": success,
            "details": details
        })
    
    def log_connection(self, target: str, method: str, success: bool, details: str = ""):
        """Log connection attempt"""
        self.log_event("connection", {
            "target": target,
            "method": method,
            "success": success,
            "details": details
        })

class PortKnocker:
    """Port knocking implementation"""
    
    def __init__(self, target_host: str):
        self.target_host = target_host
        self.knock_sequence = [12345, 23456, 34567]  # Default sequence
        self.knock_timeout = 1.0
    
    def set_sequence(self, sequence: list):
        """Set custom knock sequence"""
        self.knock_sequence = sequence
    
    def knock(self) -> bool:
        """Perform port knocking sequence"""
        try:
            for port in self.knock_sequence:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.knock_timeout)
                sock.connect_ex((self.target_host, port))
                sock.close()
                time.sleep(0.1)
            return True
        except Exception as e:
            print(f"⚠️  Port knocking failed: {e}")
            return False

class SecureConnection:
    """Secure connection manager with retry logic"""
    
    def __init__(self, logger: SecureLogger):
        self.logger = logger
        self.max_retries = 3
        self.retry_delay = 2.0
        self.connection_timeout = 10.0
    
    def test_connection(self, host: str, port: int, timeout: float = None) -> tuple[bool, float]:
        """Test connection with timing"""
        timeout = timeout or self.connection_timeout
        start_time = time.time()
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            
            elapsed = time.time() - start_time
            success = result == 0
            
            self.logger.log_connection(
                f"{host}:{port}", "tcp_test", success,
                f"latency={elapsed:.2f}s"
            )
            
            return success, elapsed
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.log_connection(
                f"{host}:{port}", "tcp_test", False,
                f"error={str(e)}, elapsed={elapsed:.2f}s"
            )
            return False, elapsed
    
    def connect_with_retry(self, host: str, port: int, knock_sequence: list = None) -> bool:
        """Connect with retry logic and optional port knocking"""
        for attempt in range(self.max_retries):
            try:
                # Port knocking if configured
                if knock_sequence:
                    knocker = PortKnocker(host)
                    knocker.set_sequence(knock_sequence)
                    knocker.knock()
                    time.sleep(1.0)  # Wait for firewall to open
                
                success, latency = self.test_connection(host, port)
                if success:
                    print(f"✅ Connected to {host}:{port} (attempt {attempt + 1}, {latency:.2f}s)")
                    return True
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"🔄 Retry {attempt + 1}/{self.max_retries} in {delay}s...")
                    time.sleep(delay)
                    
            except Exception as e:
                self.logger.log_connection(
                    f"{host}:{port}", "retry_connect", False,
                    f"attempt={attempt + 1}, error={str(e)}"
                )
        
        print(f"❌ Failed to connect to {host}:{port} after {self.max_retries} attempts")
        return False

class VPNManager:
    """VPN connection management"""
    
    def __init__(self, logger: SecureLogger):
        self.logger = logger
        self.vpn_configs = {
            'wireguard': '/etc/wireguard/nexus.conf',
            'openvpn': '/etc/openvpn/nexus.ovpn'
        }
    
    def is_vpn_connected(self) -> tuple[bool, str]:
        """Check if VPN is connected"""
        try:
            # Check for VPN interfaces
            result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
            routes = result.stdout
            
            if 'tun' in routes or 'wg' in routes:
                for line in routes.split('\n'):
                    if 'tun' in line or 'wg' in line:
                        return True, line.strip()
            return False, "No VPN connection detected"
        except Exception as e:
            return False, f"Error checking VPN: {e}"
    
    def connect_vpn(self, vpn_type: str = 'wireguard') -> bool:
        """Connect to VPN"""
        config_path = self.vpn_configs.get(vpn_type)
        if not config_path or not Path(config_path).exists():
            print(f"⚠️  VPN config not found: {config_path}")
            return False
        
        try:
            if vpn_type == 'wireguard':
                cmd = ['sudo', 'wg-quick', 'up', 'nexus']
            else:  # openvpn
                cmd = ['sudo', 'openvpn', '--config', config_path, '--daemon']
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            success = result.returncode == 0
            
            self.logger.log_event("vpn_connect", {
                "vpn_type": vpn_type,
                "success": success,
                "output": result.stdout + result.stderr
            })
            
            if success:
                print(f"✅ VPN connected ({vpn_type})")
            else:
                print(f"❌ VPN connection failed: {result.stderr}")
            
            return success
        except Exception as e:
            print(f"❌ VPN connection error: {e}")
            return False

class NexusSecure:
    """Main secure NexusController application"""
    
    def __init__(self):
        self.config = SecureConfig()
        self.logger = SecureLogger()
        self.yubikey_auth = YubiKeyAuth()
        self.vpn_manager = VPNManager(self.logger)
        self.secure_connection = SecureConnection(self.logger)
        
        self.user_authenticated = False
        self.config_password = None
        self.current_config = {}
        
        # Default secure server configuration
        self.default_servers = {
            'ebon': {
                'host': '10.0.0.29',
                'port': 22,
                'username': 'ebon',
                'name': 'Ebon Server',
                'ssh_key_path': '~/.ssh/id_ed25519',
                'require_yubikey': True,
                'knock_sequence': [12345, 23456, 34567],
                'require_vpn': False
            }
        }
        
        print("🔐 NexusController Secure initialized")
        self.logger.log_event("application_start", {"version": "secure", "yubikey_available": YUBIKEY_AVAILABLE})
    
    def setup_first_run(self):
        """Initial secure setup"""
        print("\n🚀 First-time setup for NexusController Secure")
        print("="*50)
        
        # Create master password
        while True:
            password1 = getpass.getpass("🔑 Create master password: ")
            password2 = getpass.getpass("🔑 Confirm master password: ")
            
            if password1 == password2:
                if len(password1) < 8:
                    print("❌ Password must be at least 8 characters")
                    continue
                self.config_password = password1
                break
            else:
                print("❌ Passwords don't match")
        
        # YubiKey setup
        if YUBIKEY_AVAILABLE and self.yubikey_auth.client:
            setup_yubikey = input("🔐 Setup YubiKey authentication? (y/N): ").lower() == 'y'
            if setup_yubikey:
                try:
                    username = os.getenv("USER", "nexus_user")
                    credential_data = self.yubikey_auth.register_yubikey(username)
                    self.current_config['yubikey_credential'] = credential_data
                    print("✅ YubiKey registered successfully")
                except Exception as e:
                    print(f"❌ YubiKey setup failed: {e}")
        
        # SSH key setup
        ssh_key_path = Path.home() / '.ssh' / 'id_ed25519'
        if not ssh_key_path.exists():
            create_key = input("🔑 Generate new SSH key? (Y/n): ").lower() != 'n'
            if create_key:
                self.generate_ssh_key()
        
        # Save initial configuration
        self.current_config.update({
            'servers': self.default_servers,
            'security': {
                'require_yubikey': 'yubikey_credential' in self.current_config,
                'ssh_key_auth': True,
                'port_knocking': True,
                'audit_logging': True
            },
            'created_at': datetime.now().isoformat()
        })
        
        self.save_config()
        print("✅ Setup completed successfully!")
    
    def generate_ssh_key(self):
        """Generate SSH key pair"""
        try:
            ssh_dir = Path.home() / '.ssh'
            ssh_dir.mkdir(mode=0o700, exist_ok=True)
            
            key_path = ssh_dir / 'id_ed25519'
            
            cmd = [
                'ssh-keygen', '-t', 'ed25519', '-f', str(key_path),
                '-N', '', '-C', f'nexus@{socket.gethostname()}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                os.chmod(key_path, 0o600)
                os.chmod(f"{key_path}.pub", 0o644)
                print(f"✅ SSH key generated: {key_path}")
                
                # Display public key for server setup
                pub_key = (ssh_dir / 'id_ed25519.pub').read_text().strip()
                print(f"\n📋 Add this public key to your servers:")
                print(f"    {pub_key}")
                print("\n💡 Copy this to ~/.ssh/authorized_keys on your servers")
            else:
                print(f"❌ SSH key generation failed: {result.stderr}")
        except Exception as e:
            print(f"❌ SSH key generation error: {e}")
    
    def authenticate_user(self) -> bool:
        """Multi-factor authentication"""
        print("\n🔐 Authentication Required")
        print("-" * 30)
        
        # Step 1: Master password
        password = getpass.getpass("🔑 Master password: ")
        
        try:
            self.current_config = self.config.decrypt_config(password)
            self.config_password = password
            print("✅ Password verified")
        except ValueError:
            print("❌ Invalid password")
            self.logger.log_auth_attempt("", "password", False, "invalid_password")
            return False
        
        # Step 2: YubiKey (if configured)
        if self.current_config.get('security', {}).get('require_yubikey'):
            if 'yubikey_credential' in self.current_config:
                try:
                    username = self.current_config['yubikey_credential']['username']
                    if self.yubikey_auth.authenticate_yubikey(username, self.current_config['yubikey_credential']):
                        print("✅ YubiKey verified")
                    else:
                        print("❌ YubiKey authentication failed")
                        self.logger.log_auth_attempt(username, "yubikey", False, "authentication_failed")
                        return False
                except Exception as e:
                    print(f"❌ YubiKey error: {e}")
                    return False
            else:
                print("⚠️  YubiKey required but not configured")
                return False
        
        self.user_authenticated = True
        self.logger.log_auth_attempt(os.getenv("USER", "unknown"), "multi_factor", True, "successful_login")
        return True
    
    def save_config(self):
        """Save encrypted configuration"""
        if self.config_password:
            self.config.encrypt_config(self.current_config, self.config_password)
            print("💾 Configuration saved securely")
    
    def check_server_security(self, server_config: dict) -> bool:
        """Verify server security requirements"""
        print(f"🔍 Checking security for {server_config['name']}...")
        
        # VPN check
        if server_config.get('require_vpn', False):
            connected, status = self.vpn_manager.is_vpn_connected()
            if not connected:
                print(f"❌ VPN required but not connected: {status}")
                connect_vpn = input("🔗 Connect to VPN now? (y/N): ").lower() == 'y'
                if connect_vpn:
                    if not self.vpn_manager.connect_vpn():
                        return False
                else:
                    return False
        
        # SSH key check
        ssh_key_path = Path(server_config.get('ssh_key_path', '~/.ssh/id_ed25519')).expanduser()
        if not ssh_key_path.exists():
            print(f"❌ SSH key not found: {ssh_key_path}")
            return False
        
        print("✅ Security checks passed")
        return True
    
    def secure_ssh_connect(self, server_id: str):
        """Secure SSH connection with all protections"""
        if not self.user_authenticated:
            print("❌ Authentication required")
            return
        
        server_config = self.current_config.get('servers', {}).get(server_id)
        if not server_config:
            print(f"❌ Server '{server_id}' not configured")
            return
        
        print(f"🔗 Connecting to {server_config['name']}...")
        
        # Security checks
        if not self.check_server_security(server_config):
            return
        
        # Connection with retry and port knocking
        host = server_config['host']
        port = server_config['port']
        knock_sequence = server_config.get('knock_sequence')
        
        if not self.secure_connection.connect_with_retry(host, port, knock_sequence):
            return
        
        # SSH connection
        try:
            ssh_key_path = Path(server_config.get('ssh_key_path', '~/.ssh/id_ed25519')).expanduser()
            username = server_config['username']
            
            ssh_cmd = [
                'ssh',
                '-i', str(ssh_key_path),
                '-o', 'StrictHostKeyChecking=yes',
                '-o', 'UserKnownHostsFile=~/.ssh/known_hosts',
                '-o', f'ConnectTimeout={int(self.secure_connection.connection_timeout)}',
                f'{username}@{host}'
            ]
            
            self.logger.log_connection(f"{username}@{host}", "ssh", True, "secure_connection_initiated")
            print(f"🚀 Launching secure SSH session...")
            
            subprocess.run(ssh_cmd)
            
        except KeyboardInterrupt:
            print("\n📡 SSH session ended")
        except Exception as e:
            print(f"❌ SSH connection failed: {e}")
            self.logger.log_connection(f"{username}@{host}", "ssh", False, str(e))
    
    def show_security_status(self):
        """Display comprehensive security status"""
        print("\n🛡️  Security Status")
        print("=" * 40)
        
        # Authentication status
        auth_emoji = "🟢" if self.user_authenticated else "🔴"
        print(f"{auth_emoji} Authentication: {'VERIFIED' if self.user_authenticated else 'REQUIRED'}")
        
        # YubiKey status
        if YUBIKEY_AVAILABLE and self.yubikey_auth.client:
            yubikey_emoji = "🟢"
            yubikey_status = "CONNECTED"
        else:
            yubikey_emoji = "🟡"
            yubikey_status = "NOT AVAILABLE"
        print(f"{yubikey_emoji} YubiKey: {yubikey_status}")
        
        # VPN status
        vpn_connected, vpn_status = self.vpn_manager.is_vpn_connected()
        vpn_emoji = "🟢" if vpn_connected else "🔴"
        print(f"{vpn_emoji} VPN: {vpn_status}")
        
        # SSH keys
        ssh_key_path = Path.home() / '.ssh' / 'id_ed25519'
        ssh_emoji = "🟢" if ssh_key_path.exists() else "🔴"
        ssh_status = "CONFIGURED" if ssh_key_path.exists() else "MISSING"
        print(f"{ssh_emoji} SSH Key: {ssh_status}")
        
        # Configuration
        config_emoji = "🟢" if self.current_config else "🔴"
        config_status = "ENCRYPTED" if self.current_config else "NOT LOADED"
        print(f"{config_emoji} Config: {config_status}")
        
        # Server status
        if self.user_authenticated and 'servers' in self.current_config:
            print(f"\n📡 Server Status:")
            for server_id, server_config in self.current_config['servers'].items():
                connected, latency = self.secure_connection.test_connection(
                    server_config['host'], server_config['port'], timeout=3.0
                )
                status_emoji = "🟢" if connected else "🔴"
                status_text = f"ONLINE ({latency:.2f}s)" if connected else "OFFLINE"
                print(f"  {status_emoji} {server_config['name']}: {status_text}")
    
    def security_menu(self):
        """Security management menu"""
        while True:
            print("\n🔐 Security Management")
            print("-" * 30)
            print("1. 🔑 Change Master Password")
            print("2. 🔐 Setup/Re-register YubiKey")
            print("3. 🌐 VPN Management")
            print("4. 🔑 Generate New SSH Key")
            print("5. 📋 View Audit Logs")
            print("6. ⚙️  Security Settings")
            print("7. 🔙 Back to Main Menu")
            
            choice = input("\n🎯 Select option (1-7): ").strip()
            
            if choice == '1':
                self.change_master_password()
            elif choice == '2':
                self.setup_yubikey()
            elif choice == '3':
                self.vpn_menu()
            elif choice == '4':
                self.generate_ssh_key()
            elif choice == '5':
                self.view_audit_logs()
            elif choice == '6':
                self.security_settings()
            elif choice == '7':
                break
            else:
                print("❌ Invalid choice")
    
    def change_master_password(self):
        """Change master password"""
        if not self.user_authenticated:
            print("❌ Authentication required")
            return
        
        old_password = getpass.getpass("🔑 Current password: ")
        if old_password != self.config_password:
            print("❌ Invalid current password")
            return
        
        while True:
            new_password1 = getpass.getpass("🔑 New password: ")
            new_password2 = getpass.getpass("🔑 Confirm new password: ")
            
            if new_password1 == new_password2:
                if len(new_password1) < 8:
                    print("❌ Password must be at least 8 characters")
                    continue
                
                self.config_password = new_password1
                self.save_config()
                print("✅ Master password changed successfully")
                self.logger.log_event("password_change", {"success": True})
                break
            else:
                print("❌ Passwords don't match")
    
    def setup_yubikey(self):
        """Setup or re-register YubiKey"""
        if not YUBIKEY_AVAILABLE:
            print("❌ YubiKey libraries not available")
            return
        
        if not self.yubikey_auth.client:
            print("❌ No YubiKey device found")
            return
        
        try:
            username = os.getenv("USER", "nexus_user")
            credential_data = self.yubikey_auth.register_yubikey(username)
            self.current_config['yubikey_credential'] = credential_data
            self.current_config.setdefault('security', {})['require_yubikey'] = True
            self.save_config()
            print("✅ YubiKey registered successfully")
        except Exception as e:
            print(f"❌ YubiKey setup failed: {e}")
    
    def vpn_menu(self):
        """VPN management submenu"""
        while True:
            print("\n🌐 VPN Management")
            print("-" * 20)
            print("1. 📊 Check VPN Status")
            print("2. 🔗 Connect WireGuard")
            print("3. 🔗 Connect OpenVPN")
            print("4. 🔌 Disconnect VPN")
            print("5. 🔙 Back")
            
            choice = input("\n🎯 Select option (1-5): ").strip()
            
            if choice == '1':
                connected, status = self.vpn_manager.is_vpn_connected()
                emoji = "🟢" if connected else "🔴"
                print(f"{emoji} VPN Status: {status}")
            elif choice == '2':
                self.vpn_manager.connect_vpn('wireguard')
            elif choice == '3':
                self.vpn_manager.connect_vpn('openvpn')
            elif choice == '4':
                try:
                    subprocess.run(['sudo', 'wg-quick', 'down', 'nexus'], check=True)
                    print("✅ VPN disconnected")
                except:
                    print("❌ Failed to disconnect VPN")
            elif choice == '5':
                break
            else:
                print("❌ Invalid choice")
    
    def view_audit_logs(self):
        """View recent audit logs"""
        log_file = self.logger.log_dir / f"nexus_{datetime.now().strftime('%Y%m%d')}.log"
        
        if not log_file.exists():
            print("📝 No logs found for today")
            return
        
        print(f"\n📋 Recent Activity (last 20 entries):")
        print("-" * 50)
        
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-20:]:
                    print(line.strip())
        except Exception as e:
            print(f"❌ Error reading logs: {e}")
    
    def security_settings(self):
        """Configure security settings"""
        if not self.user_authenticated:
            print("❌ Authentication required")
            return
        
        settings = self.current_config.setdefault('security', {})
        
        print("\n⚙️  Security Settings")
        print("-" * 25)
        print(f"1. Require YubiKey: {'✅' if settings.get('require_yubikey', False) else '❌'}")
        print(f"2. SSH Key Auth: {'✅' if settings.get('ssh_key_auth', True) else '❌'}")
        print(f"3. Port Knocking: {'✅' if settings.get('port_knocking', True) else '❌'}")
        print(f"4. Audit Logging: {'✅' if settings.get('audit_logging', True) else '❌'}")
        
        choice = input("\n🎯 Toggle setting (1-4) or press Enter to continue: ").strip()
        
        if choice == '1':
            settings['require_yubikey'] = not settings.get('require_yubikey', False)
        elif choice == '2':
            settings['ssh_key_auth'] = not settings.get('ssh_key_auth', True)
        elif choice == '3':
            settings['port_knocking'] = not settings.get('port_knocking', True)
        elif choice == '4':
            settings['audit_logging'] = not settings.get('audit_logging', True)
        
        if choice in ['1', '2', '3', '4']:
            self.save_config()
            print("✅ Settings updated")
    
    def main_menu(self):
        """Main application menu"""
        while True:
            print("\n🌐 NexusController Secure")
            print("=" * 35)
            
            if not self.user_authenticated:
                print("🔐 Authentication required to continue")
                if not self.authenticate_user():
                    continue
            
            print("1. 🔗 Secure SSH Connect")
            print("2. 🌐 Open Web Interface")
            print("3. 📊 Security Status")
            print("4. 🔐 Security Management")
            print("5. ⚙️  Server Configuration")
            print("6. 📋 View Logs")
            print("7. 🚪 Exit")
            
            choice = input("\n🎯 Select option (1-7): ").strip()
            
            if choice == '1':
                if 'servers' in self.current_config:
                    server_list = list(self.current_config['servers'].keys())
                    if len(server_list) == 1:
                        self.secure_ssh_connect(server_list[0])
                    else:
                        print("\n📡 Available servers:")
                        for i, server_id in enumerate(server_list, 1):
                            server_name = self.current_config['servers'][server_id]['name']
                            print(f"  {i}. {server_name}")
                        
                        try:
                            server_choice = int(input("Select server: ")) - 1
                            if 0 <= server_choice < len(server_list):
                                self.secure_ssh_connect(server_list[server_choice])
                            else:
                                print("❌ Invalid selection")
                        except ValueError:
                            print("❌ Invalid input")
                else:
                    print("❌ No servers configured")
            
            elif choice == '2':
                if 'servers' in self.current_config:
                    # Simple web interface opening (can be enhanced with security)
                    import webbrowser
                    server_config = list(self.current_config['servers'].values())[0]
                    url = f"http://{server_config['host']}"
                    print(f"🌐 Opening {url}")
                    webbrowser.open(url)
                else:
                    print("❌ No servers configured")
            
            elif choice == '3':
                self.show_security_status()
            
            elif choice == '4':
                self.security_menu()
            
            elif choice == '5':
                print("⚙️  Server configuration not implemented in this demo")
            
            elif choice == '6':
                self.view_audit_logs()
            
            elif choice == '7':
                print("👋 Goodbye!")
                self.logger.log_event("application_exit", {"user": os.getenv("USER", "unknown")})
                break
            
            else:
                print("❌ Invalid choice")
    
    def run(self):
        """Main application entry point"""
        try:
            # Check if first run
            if not self.config.config_path.exists():
                self.setup_first_run()
            
            # Start main menu
            self.main_menu()
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
        except Exception as e:
            print(f"❌ Application error: {e}")
            self.logger.log_event("application_error", {"error": str(e)})

def main():
    """Application entry point"""
    print("🔐 NexusController Secure - Enterprise Security Suite")
    print("=" * 55)
    
    app = NexusSecure()
    app.run()

if __name__ == '__main__':
    main()