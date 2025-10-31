# NexusController Secure - Enterprise Security Suite

🔐 **Comprehensive security management platform with YubiKey 5 FIDO2/WebAuthn support**

## 🚀 Quick Start

1. **Install Dependencies**:
   ```bash
   ./install_secure_deps.sh
   ```

2. **Log out and back in** (for group permissions)

3. **Run NexusController Secure**:
   ```bash
   python3 nexus_secure.py
   ```

## 🔐 Security Features

### 🔑 **Multi-Factor Authentication**
- **Master Password**: AES-256 encrypted configuration
- **YubiKey 5 FIDO2/WebAuthn**: Hardware token authentication
- **SSH Key Authentication**: Ed25519 cryptographic keys
- **Session Management**: Automatic timeouts and cleanup

### 🛡️ **Network Security**
- **VPN Integration**: WireGuard and OpenVPN support
- **Port Knocking**: Hide services behind knock sequences  
- **Firewall Management**: UFW/iptables integration
- **Fail2ban**: Automatic intrusion prevention
- **Connection Retry**: Exponential backoff with circuit breakers

### 📝 **Audit & Monitoring**
- **Comprehensive Logging**: All actions logged with timestamps
- **Security Events**: Authentication attempts, connections, failures
- **Log Rotation**: Automatic cleanup and archival
- **Real-time Monitoring**: Connection status and latency tracking

### 🔧 **Configuration Security**
- **Encrypted Storage**: PBKDF2 + AES-256 configuration encryption
- **Secure Permissions**: 600/700 file system permissions
- **Environment Variables**: Sensitive data externalization
- **Backup System**: Automated daily encrypted backups

## 🔐 YubiKey 5 Setup

### **Supported Features**
- **FIDO2/WebAuthn**: Modern passwordless authentication
- **Resident Keys**: Touch-to-authenticate workflow
- **Multiple Protocols**: FIDO2, U2F compatibility
- **Hardware Security**: Tamper-resistant cryptographic operations

### **Setup Process**
1. Insert YubiKey 5 device
2. Run first-time setup in NexusController
3. Touch YubiKey when prompted to register
4. YubiKey required for all subsequent authentications

### **Verification**
```bash
# Test YubiKey detection
python3 -c "from fido2.hid import CtapHidDevice; print(list(CtapHidDevice.list_devices()))"
```

## 🌐 VPN Configuration

### **WireGuard Setup**
1. Edit `/etc/wireguard/nexus.conf`:
   ```ini
   [Interface]
   PrivateKey = YOUR_PRIVATE_KEY
   Address = 10.100.0.2/24
   DNS = 1.1.1.1
   
   [Peer]
   PublicKey = SERVER_PUBLIC_KEY
   Endpoint = your-server.com:51820
   AllowedIPs = 0.0.0.0/0
   ```

2. Generate keys:
   ```bash
   wg genkey | tee privatekey | wg pubkey > publickey
   ```

### **OpenVPN Setup**
1. Place config in `/etc/openvpn/nexus.ovpn`
2. Ensure proper certificates and keys are included

## 🔧 SSH Security

### **Key Generation**
```bash
# Generate Ed25519 key pair
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -C "nexus@$(hostname)"

# Copy to servers
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@server
```

### **SSH Hardening**
- **Key-only authentication**: Passwords disabled
- **Strict host checking**: Prevents MITM attacks
- **Connection timeouts**: Automatic disconnection
- **Keep-alive**: Maintains stable connections

## 🚨 Port Knocking

### **Configuration**
```python
knock_sequence = [12345, 23456, 34567]  # Customize in config
```

### **How it Works**
1. Client knocks ports in sequence
2. Firewall temporarily opens SSH port
3. Connection established within window
4. Port automatically closes after timeout

## 📊 Monitoring & Logs

### **Log Locations**
- **Main logs**: `~/.nexus/logs/nexus_YYYYMMDD.log`
- **Audit trail**: All authentication and connection attempts
- **System events**: Application start/stop, errors

### **Log Analysis**
```bash
# View today's activity
tail -f ~/.nexus/logs/nexus_$(date +%Y%m%d).log

# Search for failed attempts
grep "success.*false" ~/.nexus/logs/nexus_*.log
```

## 🔒 Security Hardening

### **Daily Hardening**
```bash
# Run security hardening script
~/.nexus/harden.sh
```

### **Manual Hardening**
- **File Permissions**: 600 for configs, 700 for directories
- **System Updates**: Regular security patches
- **Dependency Updates**: Keep cryptographic libraries current
- **Key Rotation**: Regular SSH key regeneration

## 🔧 Configuration Management

### **Config Structure**
```json
{
  "servers": {
    "ebon": {
      "host": "10.0.0.29",
      "port": 22,
      "username": "ebon",
      "ssh_key_path": "~/.ssh/id_ed25519",
      "require_yubikey": true,
      "knock_sequence": [12345, 23456, 34567],
      "require_vpn": false
    }
  },
  "security": {
    "require_yubikey": true,
    "ssh_key_auth": true,
    "port_knocking": true,
    "audit_logging": true
  },
  "yubikey_credential": {
    "credential_id": "...",
    "public_key": "...",
    "username": "user"
  }
}
```

## 🛠️ Troubleshooting

### **YubiKey Issues**
```bash
# Check device detection
lsusb | grep Yubico

# Verify FIDO2 support
python3 -c "import fido2; print('FIDO2 available')"

# Reset YubiKey (WARNING: Destructive)
ykman fido reset
```

### **VPN Issues**
```bash
# Check WireGuard status
sudo wg show

# Test VPN connectivity
ping 10.100.0.1

# Check routing
ip route | grep wg
```

### **SSH Issues**
```bash
# Test SSH connection
ssh -i ~/.ssh/id_ed25519 -vvv user@host

# Check SSH agent
ssh-add -l

# Verify key permissions
ls -la ~/.ssh/
```

## 📋 Command Reference

### **Main Menu Options**
1. **🔗 Secure SSH Connect**: Multi-factor authenticated SSH
2. **🌐 Open Web Interface**: Browser with security checks
3. **📊 Security Status**: Comprehensive security overview
4. **🔐 Security Management**: YubiKey, VPN, keys management
5. **⚙️ Server Configuration**: Add/modify server settings
6. **📋 View Logs**: Audit trail and security events

### **Security Menu Options**
1. **🔑 Change Master Password**: Update encryption password
2. **🔐 Setup/Re-register YubiKey**: YubiKey management
3. **🌐 VPN Management**: Connect/disconnect VPN
4. **🔑 Generate New SSH Key**: Key generation and rotation
5. **📋 View Audit Logs**: Security event analysis
6. **⚙️ Security Settings**: Toggle security features

## 🚀 Advanced Usage

### **Automated Deployment**
```bash
# Deploy to multiple servers
for server in server1 server2 server3; do
    scp nexus_secure.py $server:~/
    ssh $server "python3 nexus_secure.py setup"
done
```

### **Integration with CI/CD**
```bash
# Use in automated scripts
echo "password" | python3 nexus_secure.py --batch --command="status"
```

### **Custom Security Modules**
- Extend `YubiKeyAuth` class for additional token types
- Add custom `PortKnocker` sequences
- Implement additional VPN providers
- Create custom audit log analyzers

## 🔐 Security Best Practices

1. **🔑 Use unique YubiKey for each environment**
2. **🌐 Always use VPN for external connections**  
3. **📝 Monitor audit logs regularly**
4. **🔄 Rotate SSH keys monthly**
5. **💾 Backup configurations securely**
6. **🔒 Keep dependencies updated**
7. **🚨 Test disaster recovery procedures**

## 📞 Support

For security issues or advanced configuration:
- **Logs**: Check `~/.nexus/logs/` for detailed error information
- **Debug**: Run with `python3 nexus_secure.py --debug`
- **Backup**: Configurations automatically backed up daily

---

**⚠️ Security Notice**: This is an enterprise-grade security platform. Handle credentials and configurations with appropriate security measures.