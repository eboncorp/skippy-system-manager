# NexusController v2.0 - Enterprise Infrastructure Management

**Secure, modular, and scalable infrastructure management platform**

![Version](https://img.shields.io/badge/version-2.0-blue.svg)
![Security](https://img.shields.io/badge/security-hardened-green.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🚀 What's New in v2.0

### ✅ **Security Hardened**
- **Fixed SSH AutoAddPolicy vulnerability** - Now uses strict host key verification
- **Eliminated hardcoded credentials** - All sensitive data encrypted and configurable
- **Comprehensive input validation** - Prevents injection attacks and validates all inputs
- **Encrypted configuration management** - All configuration files encrypted at rest
- **Secure session management** - Automatic session timeouts and cleanup

### ✅ **Modular Architecture**
- **Separated concerns** - Core, GUI, security, and networking modules
- **Thread-safe operations** - Proper GUI threading and background task management  
- **Comprehensive error handling** - Graceful error recovery and detailed logging
- **Extensive test coverage** - Unit tests and integration tests included

### ✅ **Enterprise Features**
- **Advanced monitoring** - Real-time system metrics and alerting
- **Automated backups** - Encrypted backup and recovery system
- **Cloud integration** - Multi-cloud provider support framework
- **Professional logging** - Structured logging with rotation and levels

## 📋 Quick Start

### Prerequisites

```bash
# System requirements
sudo apt update
sudo apt install python3 python3-pip python3-venv python3-tk nmap ssh-keyscan tar openssl

# Verify Python version (3.8+ required)
python3 --version
```

### Installation

```bash
# Clone or download NexusController v2.0
cd ~/Skippy/app-to-deploy/NexusController

# Make launcher executable
chmod +x nexus_launcher.sh

# Launch with automatic setup
./nexus_launcher.sh
```

The launcher will automatically:
- ✅ Check system requirements
- ✅ Create Python virtual environment  
- ✅ Install dependencies
- ✅ Setup secure directories
- ✅ Validate configuration
- ✅ Launch the application

## 🖥️ Usage

### GUI Mode (Default)
```bash
./nexus_launcher.sh          # Launch GUI
./nexus_launcher.sh gui      # Explicit GUI mode
```

### CLI Mode
```bash
./nexus_launcher.sh cli      # Command-line interface
```

### System Maintenance
```bash
./nexus_launcher.sh check    # Run system checks
./nexus_launcher.sh install  # Install/update dependencies
```

## 🏗️ Architecture

### Core Components

```
NexusController v2.0/
├── nexus_controller_v2.py    # Core backend logic
├── nexus_gui.py              # Modern GUI interface  
├── nexus_launcher.sh         # Smart launcher script
├── test_nexus.py             # Comprehensive test suite
├── requirements.txt          # Python dependencies
└── README_v2.md             # This documentation
```

### Directory Structure

```
~/.nexus/                     # Configuration directory
├── config/                   # Encrypted configuration files
├── keys/                     # SSH keys and certificates
├── logs/                     # Application logs
└── backups/                  # Automated backups
```

### Security Model

- **Encryption at Rest**: All sensitive configuration encrypted with Fernet
- **SSH Security**: Strict host key verification, no AutoAddPolicy
- **Input Validation**: All network ranges, IPs, and file paths validated
- **Secure Permissions**: 700 permissions on sensitive directories
- **Session Management**: Automatic timeout and cleanup of connections

## 🔧 Configuration

### Network Settings
```json
{
  "network": {
    "default_range": "10.0.0.0/24",
    "scan_timeout": 120,
    "scan_rate_limit": 10
  }
}
```

### Security Settings
```json
{
  "security": {
    "ssh_timeout": 30,
    "session_timeout": 3600,
    "max_retries": 3
  }
}
```

### UI Settings
```json
{
  "ui": {
    "theme": "dark",
    "geometry": "1200x800"
  }
}
```

## 🌐 Network Discovery

### Features
- **Secure nmap integration** - Rate-limited network scanning
- **Device identification** - Automatic hostname and vendor detection
- **Server recognition** - Identifies servers by hostname patterns
- **Real-time monitoring** - Auto-refresh capability with configurable intervals

### Usage
1. Enter network range (e.g., `10.0.0.0/24`)
2. Click "Scan Network" 
3. View discovered devices in the tree view
4. Right-click devices for connection options

## 🔐 SSH Management

### Security Features
- **Host key verification** - Automatic ssh-keyscan integration
- **Multiple authentication** - Support for keys and passwords
- **Connection caching** - Efficient connection reuse
- **Session monitoring** - Track active connections and usage

### Connection Process
1. Select device from network scan
2. Choose "Connect" from context menu
3. Configure authentication (key file or password)
4. Secure connection established with host verification

## 📊 System Monitoring

### Metrics Collected
- **CPU Usage** - Real-time CPU utilization and frequency
- **Memory Usage** - RAM usage and availability
- **Disk Usage** - Storage usage for all mounted filesystems
- **Network I/O** - Bytes sent/received and error counts
- **Process Information** - Running processes and system load

### Alerting System
- **Configurable thresholds** - CPU, memory, disk, and network limits
- **Real-time alerts** - Immediate notification of threshold breaches
- **Alert history** - Persistent alert log with timestamps
- **Visual indicators** - Color-coded status display

## 💾 Backup Management

### Automated Backups
- **Encrypted storage** - All backups encrypted with master key
- **Incremental backups** - Efficient storage with compression
- **Backup verification** - Integrity checking and validation
- **Cloud sync ready** - Integration with cloud storage providers

### Backup Types
- **Configuration backup** - Settings and preferences
- **Key backup** - SSH keys and certificates (encrypted)
- **Full system backup** - Complete application state
- **Selective restore** - Choose specific components to restore

## ☁️ Cloud Integration

### Supported Providers (Framework)
- **Google Drive** - File storage and synchronization
- **GitHub** - Repository management and deployment
- **AWS** - Infrastructure as a Service
- **Azure** - Microsoft cloud services
- **Multi-cloud** - Unified management interface

### Security
- **Encrypted credentials** - All API keys and tokens encrypted
- **OAuth integration** - Secure authentication flows
- **Access control** - Fine-grained permission management

## 🧪 Testing

### Run Test Suite
```bash
# Run all tests
python3 test_nexus.py

# Run specific test class
python3 -m unittest test_nexus.TestSecurityManager

# Run with verbose output
python3 test_nexus.py -v
```

### Test Coverage
- **Unit Tests** - Individual component testing
- **Integration Tests** - Component interaction testing
- **Security Tests** - Vulnerability and encryption testing
- **Thread Safety Tests** - Concurrent operation testing

## 🐛 Troubleshooting

### Common Issues

#### GUI Won't Start
```bash
# Check X11 display
echo $DISPLAY

# Install GUI dependencies
sudo apt install python3-tk

# Run system check
./nexus_launcher.sh check
```

#### Network Scan Fails
```bash
# Install nmap
sudo apt install nmap

# Check network permissions
sudo nmap -sn 10.0.0.0/24
```

#### SSH Connection Issues
```bash
# Check SSH service
systemctl status ssh

# Verify host key
ssh-keyscan -H hostname

# Check firewall
sudo ufw status
```

### Log Files
- **Application logs**: `~/.nexus/logs/nexus_YYYYMMDD.log`
- **Launcher logs**: `~/.nexus/logs/launcher.log`
- **GUI logs**: Integrated with application logs

## 🔒 Security Considerations

### Best Practices
1. **Regular updates** - Keep dependencies updated
2. **Key rotation** - Rotate SSH keys periodically  
3. **Access control** - Limit network access appropriately
4. **Backup security** - Encrypt and secure backup storage
5. **Audit logs** - Review logs regularly for anomalies

### Security Checklist
- [ ] SSH host keys verified
- [ ] Configuration files encrypted
- [ ] Sensitive directories have 700 permissions
- [ ] Regular security updates applied
- [ ] Backup encryption verified
- [ ] Network access restricted

## 📈 Performance

### Optimizations
- **Asynchronous operations** - Non-blocking network operations
- **Connection pooling** - Efficient SSH connection reuse
- **Rate limiting** - Prevents network flooding
- **Memory management** - Automatic cleanup and garbage collection

### Resource Usage
- **Memory**: ~50-100MB typical usage
- **CPU**: Low impact during normal operation
- **Network**: Configurable scan rate limiting
- **Storage**: ~10MB for application, variable for logs/backups

## 🤝 Contributing

### Development Setup
```bash
# Install development dependencies
pip3 install pytest pytest-cov black flake8 mypy

# Run code formatting
black nexus_controller_v2.py nexus_gui.py

# Run linting
flake8 *.py

# Run type checking
mypy nexus_controller_v2.py
```

### Code Standards
- **PEP 8** - Python style guide compliance
- **Type hints** - Full type annotation
- **Docstrings** - Comprehensive documentation
- **Security** - Security-first development approach

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

### Getting Help
- **Documentation**: This README and inline code comments
- **Logs**: Check `~/.nexus/logs/` for detailed error information
- **Testing**: Run test suite to verify installation
- **Issues**: Report bugs and request features via project repository

### Community
- **Discussions**: Join community discussions
- **Contributions**: Pull requests welcome
- **Security**: Report security issues privately

---

**NexusController v2.0** - *Secure Infrastructure Management Made Simple*

Built with 💙 for enterprise infrastructure teams