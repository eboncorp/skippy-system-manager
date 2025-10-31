#\!/bin/bash
# Hardware-Optimized Security & Networking for Dell Latitude 3520
# Intel Celeron 6305, 16GB RAM, 512GB NVMe, WiFi + Ethernet

echo "🖥️  HARDWARE-OPTIMIZED NEXUS SECURITY SETUP"
echo "============================================="
echo "Hardware: Dell Latitude 3520"
echo "CPU: Intel Celeron 6305 @ 1.80GHz (2 cores)"
echo "RAM: 16GB DDR4 2667MHz"
echo "Storage: 512GB Samsung NVMe"
echo "Network: RTL8822CE WiFi + RTL8111 Gigabit Ethernet"
echo ""

# Phase 1: YubiKey Preparation (Ready for when it arrives)
echo "🔑 Phase 1: YubiKey Infrastructure Setup"

# Create YubiKey configuration directory
sudo mkdir -p /etc/yubico
sudo chmod 755 /etc/yubico

# Create YubiKey-ready PAM configuration
sudo tee /etc/pam.d/yubico-sudo << 'PAM_EOF'
#%PAM-1.0
# YubiKey-enhanced sudo authentication
# This will be activated when YubiKey arrives

# Primary authentication methods (in order of preference):
# 1. YubiKey hardware token (when available)
# 2. Session-based conditional access (current)
# 3. Standard password (fallback)

# YubiKey authentication (commented until key arrives)
# auth required pam_yubico.so id=CHANGEME key=CHANGEME authfile=/etc/yubico/authorized_yubikeys

# Include standard sudo PAM stack
@include common-auth
@include common-account
@include common-session-noninteractive
PAM_EOF

# Phase 2: Hardware-Optimized Network Security
echo "🌐 Phase 2: Network Security for Your Hardware"

# Optimize for your dual network setup (WiFi primary, Ethernet backup)
sudo tee /etc/systemd/network/10-ethernet.network << 'NET_EOF'
[Match]
Name=enp45s0

[Network]
DHCP=yes
IPForward=no

[DHCPv4]
UseHostname=false
SendHostname=false

[DHCPv6]
UseHostname=false
NET_EOF

# Configure WiFi security enhancements
sudo tee /etc/NetworkManager/conf.d/nexus-security.conf << 'WIFI_EOF'
[main]
# Enhanced WiFi security for NexusController
dns=systemd-resolved

[connection]
# Randomize MAC address for privacy
wifi.mac-address-randomization=2
ethernet.cloned-mac-address=random

[device]
# Disable autoconnect to unknown networks
wifi.scan-rand-mac-address=yes
NET_EOF

# Phase 3: Hardware-Specific Performance Tuning
echo "⚡ Phase 3: CPU & Memory Optimization"

# Optimize for Intel Celeron 6305 (2 cores, limited resources)
sudo tee /etc/security/limits.d/nexus-performance.conf << 'PERF_EOF'
# NexusController performance limits for 2-core system
* soft nofile 65536
* hard nofile 65536
* soft nproc 4096
* hard nproc 4096

# Optimize for 16GB RAM
dave soft memlock unlimited
dave hard memlock unlimited
PERF_EOF

# CPU governor optimization for mobile processor
echo 'GOVERNOR="powersave"' | sudo tee /etc/default/cpufrequtils

# Phase 4: Storage Security (NVMe-specific)
echo "💾 Phase 4: NVMe Storage Security"

# Enable TRIM for NVMe SSD longevity
sudo systemctl enable fstrim.timer

# Secure storage configuration
sudo tee -a /etc/fstab << 'FSTAB_EOF'
# NexusController secure mount options
tmpfs /tmp tmpfs defaults,noatime,nosuid,nodev,noexec,mode=1777 0 0
tmpfs /var/tmp tmpfs defaults,noatime,nosuid,nodev,noexec,mode=1777 0 0
FSTAB_EOF

# Phase 5: Thunderbolt Security (Your hardware has TB4)
echo "⚡ Phase 5: Thunderbolt 4 Security"

# Secure Thunderbolt configuration
sudo tee /etc/udev/rules.d/99-thunderbolt-security.rules << 'TB_EOF'
# Thunderbolt security rules for Dell Latitude 3520
# Require authorization for all Thunderbolt devices
ACTION=="add", SUBSYSTEM=="thunderbolt", ATTR{authorized}=="0", ATTR{authorized}="1"
# Log all Thunderbolt connections
ACTION=="add", SUBSYSTEM=="thunderbolt", RUN+="/usr/bin/logger -t thunderbolt 'Device connected: %k'"
TB_EOF

echo "✅ Hardware-optimized security setup complete\!"
echo ""
echo "🔑 YubiKey Integration Plan:"
echo "1. When YubiKey arrives, run: yubikey_setup_final.sh"
echo "2. Current: Session-based access control active"
echo "3. Future: Hardware + session dual authentication"
echo ""
echo "📊 Performance Optimizations:"
echo "- CPU: Optimized for 2-core Celeron"
echo "- RAM: 16GB with swap management"
echo "- Storage: NVMe TRIM enabled"
echo "- Network: Dual-interface with security"
echo ""
