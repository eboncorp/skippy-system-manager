# HP Z4 G4 Server Installation Guide

## Overview
Fresh installation of Ubuntu Server on HP Z4 G4 for dedicated home server use.

## Hardware: HP Z4 G4 Workstation
- **CPU**: Intel Xeon W or Core i9
- **RAM**: Up to 256GB (excellent for virtualization)
- **Storage**: Multiple NVMe/SATA bays
- **Network**: Gigabit Ethernet built-in
- **Perfect for**: Home server, Docker, virtualization, storage

## Installation Steps

### 1. Download Ubuntu Server
**Recommended**: Ubuntu Server 22.04 LTS (Long Term Support)

Download from: https://ubuntu.com/download/server
- File: `ubuntu-22.04.3-live-server-amd64.iso`
- Size: ~1.4GB
- LTS = 5 years of support

### 2. Create Bootable USB
**Requirements**: 4GB+ USB drive

**Method 1 - Using Rufus (Windows)**:
1. Download Rufus from rufus.ie
2. Insert USB drive
3. Select Ubuntu Server ISO
4. Click "Start"

**Method 2 - Using dd (Linux)**:
```bash
# Find USB device
lsblk

# Create bootable USB (replace /dev/sdX with your USB)
sudo dd if=ubuntu-22.04.3-live-server-amd64.iso of=/dev/sdX bs=4M status=progress
sudo sync
```

**Method 3 - Using Startup Disk Creator (Ubuntu)**:
```bash
sudo apt install usb-creator-gtk
usb-creator-gtk
```

### 3. HP Z4 G4 BIOS Setup
1. **Boot from USB**:
   - Press F9 during startup for boot menu
   - Or F10 for BIOS settings
   - Enable "Legacy Boot" if needed
   - Disable Secure Boot temporarily

2. **BIOS Recommendations**:
   - Enable virtualization (VT-x/VT-d)
   - Set boot priority: USB first
   - Enable Wake-on-LAN
   - Set power recovery to "Previous state"

### 4. Ubuntu Server Installation

#### Initial Setup
1. **Language**: English
2. **Keyboard**: Your layout
3. **Installation Type**: Ubuntu Server
4. **Network**: 
   - Use Ethernet (more reliable than WiFi)
   - Static IP: 10.0.0.29 (or let DHCP assign)
   - Gateway: 10.0.0.1
   - DNS: 8.8.8.8, 1.1.1.1

#### Disk Setup
**Recommended for HP Z4 G4**:
- **Option 1 - Simple**: Use entire disk with LVM
- **Option 2 - Advanced**: Custom partitioning
  ```
  /boot     1GB     ext4
  /         50GB    ext4
  /home     50GB    ext4
  /var      30GB    ext4  (for logs/docker)
  swap      16GB    swap
  /data     Rest    ext4  (for storage/containers)
  ```

#### User Setup
```
Your name: Your Full Name
Your server's name: ebon-eth
Pick a username: ebon
Choose a password: [secure password]
```

#### SSH Setup
- ✅ **Install OpenSSH server** (IMPORTANT!)
- ✅ **Import SSH identity** (if you have GitHub/Launchpad)
- Or set up keys later

#### Software Selection
**Recommended packages**:
- OpenSSH server ✅
- Docker (optional, can install later)

### 5. Post-Installation Configuration

#### First Boot Commands
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git htop vim ufw tree

# Configure firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 8080  # For Home Server Master web UI

# Set timezone
sudo timedatectl set-timezone America/New_York  # or your timezone

# Check system info
hostnamectl
free -h
df -h
ip addr show
```

#### SSH Key Setup (from Skippy)
```bash
# From your current machine (Skippy)
ssh-copy-id ebon@10.0.0.29

# Test connection
ssh ebon@10.0.0.29
```

### 6. Server Optimization for HP Z4 G4

#### Performance Tuning
```bash
# Install additional monitoring tools
sudo apt install -y iotop nethogs ncdu

# Optional: Install container platform
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ebon

# Set up automatic updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

#### Network Configuration
```bash
# Set static IP (if needed)
sudo nano /etc/netplan/00-installer-config.yaml

# Example static IP config:
network:
  ethernets:
    enp1s0:  # Your ethernet interface
      dhcp4: false
      addresses:
        - 10.0.0.29/24
      gateway4: 10.0.0.1
      nameservers:
        addresses: [8.8.8.8, 1.1.1.1]
  version: 2

# Apply network config
sudo netplan apply
```

### 7. Install Home Server Master

#### Transfer Installation Files
```bash
# From Skippy, copy installer to new server
scp home_server_installer.sh ebon@10.0.0.29:/tmp/
scp -r Skippy/* ebon@10.0.0.29:/tmp/home-server-files/

# Connect to server
ssh ebon@10.0.0.29

# Run installer
cd /tmp
chmod +x home_server_installer.sh
./home_server_installer.sh
```

### 8. Verification Steps

#### System Check
```bash
# Verify installation
ssh ebon@10.0.0.29 "
  echo '=== System Info ==='
  uname -a
  free -h
  df -h
  
  echo '=== Network ==='
  ip addr show
  ss -tlnp | grep :22
  
  echo '=== Services ==='
  systemctl status ssh
  systemctl status docker || echo 'Docker not installed'
"
```

## Benefits of Fresh Installation

✅ **Clean system** - No old configurations or conflicts  
✅ **Latest packages** - Up-to-date security and features  
✅ **Optimized for server** - No desktop overhead  
✅ **Known credentials** - Full control of access  
✅ **Proper SSH setup** - Secure remote management  
✅ **Perfect for Home Server Master** - Ideal platform  

## Next Steps After Installation

1. **Install Home Server Master** on clean Ubuntu Server
2. **Configure Ethereum node** (if desired)
3. **Set up storage/backup systems**
4. **Configure monitoring and alerts**
5. **Set up container services** (Docker/Portainer)

The HP Z4 G4 with Ubuntu Server will be an excellent foundation for your complete home server setup!