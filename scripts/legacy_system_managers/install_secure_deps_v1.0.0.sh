#!/bin/bash
# NexusController Secure - Dependency Installation
# Install all required packages for enterprise security features

echo "🔐 Installing NexusController Secure Dependencies"
echo "================================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root for system packages
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}❌ Don't run as root. Script will use sudo when needed.${NC}"
   exit 1
fi

echo -e "${BLUE}📦 Updating package repositories...${NC}"
sudo apt update

echo -e "${BLUE}📦 Installing system dependencies...${NC}"

# Core security packages
SYSTEM_PACKAGES=(
    "python3-pip"           # Python package manager
    "python3-dev"           # Python development headers
    "libffi-dev"            # Required for cryptography
    "libssl-dev"            # OpenSSL development
    "libudev-dev"           # Required for FIDO2/YubiKey
    "libhidapi-dev"         # HID API for hardware tokens
    "openssh-client"        # SSH client
    "wireguard"             # WireGuard VPN
    "openvpn"               # OpenVPN client
    "iptables"              # Firewall for port knocking
    "fail2ban"              # Intrusion prevention
    "ufw"                   # Uncomplicated Firewall
)

for package in "${SYSTEM_PACKAGES[@]}"; do
    echo -e "${BLUE}  Installing $package...${NC}"
    sudo apt install -y "$package"
done

echo -e "${BLUE}📦 Installing Python security libraries...${NC}"

# Python security packages
PYTHON_PACKAGES=(
    "cryptography>=3.4.8"          # Encryption/decryption
    "paramiko>=2.7.2"              # SSH connections
    "fido2>=1.1.0"                 # YubiKey FIDO2/WebAuthn
    "requests>=2.25.1"             # HTTP client
    "pynacl>=1.4.0"                # Modern cryptography
    "bcrypt>=3.2.0"                # Password hashing
    "pyotp>=2.6.0"                 # TOTP/HOTP support
    "qrcode>=7.3.1"                # QR code generation
    "python-gnupg>=0.4.8"          # GPG integration
    "psutil>=5.8.0"                # System monitoring
)

for package in "${PYTHON_PACKAGES[@]}"; do
    echo -e "${BLUE}  Installing Python package: $package...${NC}"
    python3 -m pip install --user "$package"
done

echo -e "${BLUE}🔧 Setting up security configurations...${NC}"

# Create secure directories
echo -e "${BLUE}  Creating secure directories...${NC}"
mkdir -p ~/.nexus/{logs,config,keys,backup} 2>/dev/null
chmod 700 ~/.nexus ~/.nexus/*

# SSH directory setup
if [ ! -d ~/.ssh ]; then
    echo -e "${BLUE}  Creating SSH directory...${NC}"
    mkdir -p ~/.ssh
    chmod 700 ~/.ssh
fi

# Create SSH config if it doesn't exist
if [ ! -f ~/.ssh/config ]; then
    echo -e "${BLUE}  Creating SSH config template...${NC}"
    cat > ~/.ssh/config << 'EOF'
# NexusController SSH Configuration
Host *
    StrictHostKeyChecking yes
    UserKnownHostsFile ~/.ssh/known_hosts
    ConnectTimeout 10
    ServerAliveInterval 60
    ServerAliveCountMax 3
    
# Ebon server configuration
Host ebon
    HostName 10.0.0.29
    User ebon
    Port 22
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
EOF
    chmod 600 ~/.ssh/config
fi

# UFW firewall setup
echo -e "${BLUE}🔥 Configuring firewall...${NC}"
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow ssh

# Allow local network (adjust as needed)
sudo ufw allow from 10.0.0.0/8
sudo ufw allow from 192.168.0.0/16
sudo ufw allow from 172.16.0.0/12

# Enable firewall
sudo ufw --force enable

# Fail2ban configuration
echo -e "${BLUE}🛡️  Configuring intrusion prevention...${NC}"
if [ -f /etc/fail2ban/jail.conf ]; then
    sudo systemctl enable fail2ban
    sudo systemctl start fail2ban
fi

# Create WireGuard directory
echo -e "${BLUE}🌐 Setting up VPN directories...${NC}"
sudo mkdir -p /etc/wireguard
sudo chmod 700 /etc/wireguard

# Create example WireGuard config
if [ ! -f /etc/wireguard/nexus.conf ]; then
    echo -e "${YELLOW}⚠️  Creating example WireGuard config...${NC}"
    sudo tee /etc/wireguard/nexus.conf > /dev/null << 'EOF'
# NexusController VPN Configuration
# Replace with your actual VPN settings
[Interface]
PrivateKey = YOUR_PRIVATE_KEY_HERE
Address = 10.100.0.2/24
DNS = 1.1.1.1, 8.8.8.8

[Peer]
PublicKey = YOUR_SERVER_PUBLIC_KEY_HERE
Endpoint = your-vpn-server.com:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
EOF
    sudo chmod 600 /etc/wireguard/nexus.conf
    echo -e "${YELLOW}📝 Edit /etc/wireguard/nexus.conf with your VPN settings${NC}"
fi

# Set up systemd service for NexusController
echo -e "${BLUE}⚙️  Creating systemd service...${NC}"
sudo tee /etc/systemd/system/nexus-secure.service > /dev/null << EOF
[Unit]
Description=NexusController Secure
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(which python3) $(pwd)/nexus_secure.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload

# Create backup script
echo -e "${BLUE}💾 Creating backup script...${NC}"
cat > ~/.nexus/backup.sh << 'EOF'
#!/bin/bash
# NexusController Secure Backup Script

BACKUP_DIR="$HOME/.nexus/backup"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/nexus_backup_$DATE.tar.gz"

echo "🔄 Creating NexusController backup..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create backup
tar -czf "$BACKUP_FILE" \
    ~/.nexus/config.enc \
    ~/.nexus/logs/ \
    ~/.ssh/id_ed25519* \
    ~/.ssh/config \
    ~/.ssh/known_hosts \
    2>/dev/null

echo "✅ Backup created: $BACKUP_FILE"

# Keep only last 10 backups
cd "$BACKUP_DIR" && ls -t nexus_backup_*.tar.gz | tail -n +11 | xargs -r rm

echo "🧹 Old backups cleaned up"
EOF

chmod +x ~/.nexus/backup.sh

# Create daily backup cron job
echo -e "${BLUE}⏰ Setting up daily backups...${NC}"
(crontab -l 2>/dev/null; echo "0 2 * * * $HOME/.nexus/backup.sh") | crontab -

# Security hardening script
echo -e "${BLUE}🔒 Creating security hardening script...${NC}"
cat > ~/.nexus/harden.sh << 'EOF'
#!/bin/bash
# Security Hardening for NexusController

echo "🔒 Applying security hardening..."

# Secure file permissions
find ~/.nexus -type f -exec chmod 600 {} \;
find ~/.nexus -type d -exec chmod 700 {} \;

# SSH key permissions
chmod 600 ~/.ssh/id_* 2>/dev/null
chmod 644 ~/.ssh/*.pub 2>/dev/null
chmod 600 ~/.ssh/config 2>/dev/null
chmod 644 ~/.ssh/known_hosts 2>/dev/null

# Update system
sudo apt update && sudo apt upgrade -y

# Update Python packages
python3 -m pip install --user --upgrade pip
python3 -m pip install --user --upgrade cryptography paramiko fido2

echo "✅ Security hardening completed"
EOF

chmod +x ~/.nexus/harden.sh

# YubiKey udev rules
echo -e "${BLUE}🔐 Setting up YubiKey udev rules...${NC}"
sudo tee /etc/udev/rules.d/70-yubikey.rules > /dev/null << 'EOF'
# YubiKey rules for NexusController
SUBSYSTEM=="usb", ATTRS{idVendor}=="1050", ATTRS{idProduct}=="0010|0110|0111|0114|0116|0401|0403|0405|0407|0410", GROUP="plugdev", MODE="0664"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="1050", ATTRS{idProduct}=="0010|0110|0111|0114|0116|0401|0403|0405|0407|0410", GROUP="plugdev", MODE="0664"
EOF

sudo udevadm control --reload-rules
sudo udevadm trigger

# Add user to plugdev group for YubiKey access
sudo usermod -a -G plugdev $USER

echo -e "${GREEN}✅ Installation completed successfully!${NC}"
echo
echo -e "${YELLOW}📋 Post-installation notes:${NC}"
echo -e "${YELLOW}  1. Log out and back in for group changes to take effect${NC}"
echo -e "${YELLOW}  2. Edit /etc/wireguard/nexus.conf with your VPN settings${NC}"
echo -e "${YELLOW}  3. Generate SSH keys: ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519${NC}"
echo -e "${YELLOW}  4. Copy public key to your servers${NC}"
echo -e "${YELLOW}  5. Test YubiKey: python3 -c 'from fido2.hid import CtapHidDevice; print(list(CtapHidDevice.list_devices()))'${NC}"
echo
echo -e "${GREEN}🚀 Ready to run: python3 nexus_secure.py${NC}"