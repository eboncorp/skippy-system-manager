# NexusController Unified - Complete Infrastructure Management

Enterprise-grade unified system for managing distributed ebon servers, cloud services, media servers, home automation, and security infrastructure.

## Quick Start

```bash
cd ~/Skippy/app-to-deploy/NexusController
./nexus_unified_launcher.sh
```

## Features

- 🖥️ **Multi-Server Management** - SSH, Docker, Services
- ☁️ **Cloud Integration** - 13 providers including Google Drive  
- 🎬 **Media Server Control** - Jellyfin, PhotoPrism
- 🏠 **Home Automation** - Home Assistant, Zigbee2MQTT
- 🔒 **Enterprise Security** - Encryption, VPN, YubiKey support
- 📊 **AI-Powered Monitoring** - Predictive analytics
- 💾 **Automated Google Drive Backup** - Default backup provider
- 🔧 **System Optimization** - TidyTux integration

## Files

- `nexus_unified.py` - Main application (2000+ lines)
- `nexus_unified_launcher.sh` - Smart launcher with checks
- `gdrive_gui.py` - Google Drive management GUI
- `complete-tidytux.sh` - System cleanup script
- Configuration files from ~/.nexus directory

## System Requirements

- Python 3.8+
- tkinter, paramiko, psutil, requests, cryptography
- nmap, ssh-keyscan
- Ubuntu/Debian recommended

## Network Architecture

- Control Center: 10.0.0.25 (dave@Ebon - this laptop)
- Media Server: 10.0.0.29 (ebon@ebon)
- Future servers: ebon-* prefix

## Installation

```bash
# Install dependencies
pip3 install --user paramiko psutil requests cryptography

# Install system tools
sudo apt install nmap ssh-keyscan

# Run launcher
./nexus_unified_launcher.sh
```

## Production Ready

✅ Stable GUI with delayed initialization to prevent segfaults  
✅ Enterprise security with encrypted configuration  
✅ Google Drive integration as primary backup  
✅ Multi-server discovery and management  
✅ Comprehensive logging and monitoring  
✅ YubiKey 5 hardware security support  
✅ All components unified into single robust application  

Generated with 🤖 Claude Code