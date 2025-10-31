#!/bin/bash
# YubiKey 5 Preparation Script
# Run with: sudo bash yubikey_preparation.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔑 YubiKey 5 Preparation Setup${NC}"
echo "==============================="
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Please run as root: sudo bash $0${NC}"
    exit 1
fi

# Install YubiKey packages
echo -e "${YELLOW}📦 Installing YubiKey packages...${NC}"
apt update
apt install -y \
    yubikey-manager \
    yubikey-personalization \
    yubikey-personalization-gui \
    libpam-yubico \
    libpam-u2f \
    pcscd \
    scdaemon \
    gnupg2 \
    gnupg-agent \
    pinentry-curses \
    pinentry-gtk2

# Install additional FIDO2/WebAuthn support
apt install -y \
    libfido2-1 \
    libfido2-dev \
    libfido2-doc \
    fido2-tools

# Start and enable PC/SC daemon
systemctl enable pcscd
systemctl start pcscd

# Add user to necessary groups
echo -e "${YELLOW}👥 Adding user to required groups...${NC}"
usermod -a -G plugdev dave
usermod -a -G dialout dave

# Create udev rules for YubiKey
echo -e "${YELLOW}⚙️ Creating udev rules...${NC}"
cat > /etc/udev/rules.d/70-yubikey.rules << 'EOF'
# YubiKey 5 Series
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="1050", ATTRS{idProduct}=="0407", TAG+="uaccess", GROUP="plugdev", MODE="0664"

# YubiKey FIDO
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="1050", ATTRS{idProduct}=="0120", TAG+="uaccess", GROUP="plugdev", MODE="0664"

# YubiKey CCID
SUBSYSTEM=="usb", ATTRS{idVendor}=="1050", ATTRS{idProduct}=="0407", TAG+="uaccess", GROUP="plugdev", MODE="0664"
EOF

# Reload udev rules
udevadm control --reload-rules
udevadm trigger

# Configure PAM for YubiKey FIDO2
echo -e "${YELLOW}🔐 Configuring PAM for YubiKey...${NC}"

# Backup original PAM configurations
cp /etc/pam.d/sudo /etc/pam.d/sudo.backup
cp /etc/pam.d/login /etc/pam.d/login.backup
cp /etc/pam.d/sshd /etc/pam.d/sshd.backup

# Create YubiKey SSH configuration template
mkdir -p /home/dave/.ssh
cat > /home/dave/.ssh/yubikey_setup.md << 'EOF'
# YubiKey SSH Setup Instructions

## When your YubiKey arrives:

### 1. Generate SSH key on YubiKey:
```bash
ssh-keygen -t ecdsa-sk -f ~/.ssh/yubikey_ecdsa
# OR for Ed25519:
ssh-keygen -t ed25519-sk -f ~/.ssh/yubikey_ed25519
```

### 2. Add to SSH config:
```bash
echo -e "\n# YubiKey SSH Configuration" >> ~/.ssh/config
echo "Host ebon 10.0.0.29" >> ~/.ssh/config
echo "    HostName 10.0.0.29" >> ~/.ssh/config
echo "    User ebon" >> ~/.ssh/config
echo "    IdentityFile ~/.ssh/yubikey_ecdsa" >> ~/.ssh/config
echo "    IdentitiesOnly yes" >> ~/.ssh/config
```

### 3. Copy public key to server:
```bash
ssh-copy-id -i ~/.ssh/yubikey_ecdsa.pub ebon@10.0.0.29
```

### 4. Test YubiKey SSH:
```bash
ssh -i ~/.ssh/yubikey_ecdsa ebon@10.0.0.29
```

### 5. Configure GPG (optional):
```bash
gpg --card-edit
# Follow prompts to set up GPG keys
```
EOF

chown dave:dave /home/dave/.ssh/yubikey_setup.md

# Create YubiKey testing script
cat > /usr/local/bin/test-yubikey.sh << 'EOF'
#!/bin/bash
# YubiKey functionality test script

echo "=== YubiKey Functionality Test ==="
echo

echo "1. Checking for YubiKey device..."
lsusb | grep -i yubi || echo "❌ No YubiKey detected"

echo
echo "2. YubiKey Manager status..."
ykman info 2>/dev/null || echo "❌ YubiKey not accessible via ykman"

echo
echo "3. FIDO2 functionality..."
fido2-token -L 2>/dev/null || echo "❌ No FIDO2 tokens detected"

echo
echo "4. PC/SC daemon status..."
systemctl is-active pcscd

echo
echo "5. User group memberships..."
groups dave | grep -E "(plugdev|dialout)" || echo "⚠️ User not in required groups"

echo
echo "=== Test Complete ==="
EOF

chmod +x /usr/local/bin/test-yubikey.sh

# Create YubiKey backup and security script
cat > /home/dave/yubikey_security_checklist.md << 'EOF'
# YubiKey Security Checklist

## When you receive your YubiKey 5:

### Initial Setup:
- [ ] Set strong PIN (6-8 digits minimum)
- [ ] Set PUK (Personal Unblocking Key)
- [ ] Enable touch requirement for operations
- [ ] Set up FIDO2 PIN

### SSH Configuration:
- [ ] Generate resident SSH key on YubiKey
- [ ] Add public key to home server
- [ ] Test SSH authentication with touch
- [ ] Remove old password-based SSH keys

### GPG Configuration:
- [ ] Generate GPG master key offline
- [ ] Move GPG subkeys to YubiKey
- [ ] Configure git signing
- [ ] Test email encryption/signing

### 2FA Setup:
- [ ] Enable 2FA for all crypto exchanges
- [ ] Set up TOTP for critical services
- [ ] Use WebAuthn where supported
- [ ] Document backup codes securely

### Backup Strategy:
- [ ] Purchase second YubiKey as backup
- [ ] Store backup YubiKey in secure location
- [ ] Keep backup codes in encrypted storage
- [ ] Test backup key functionality

### Security Practices:
- [ ] Never leave YubiKey unattended
- [ ] Use different keys for different purposes
- [ ] Regular security audits
- [ ] Monitor for unauthorized access attempts

## Emergency Procedures:

### If YubiKey is lost/stolen:
1. Immediately disable all 2FA tied to the key
2. Change all passwords for affected accounts
3. Revoke SSH keys from servers
4. Activate backup YubiKey
5. Generate new GPG keys if compromised

### If YubiKey stops working:
1. Test with different USB ports/computers
2. Check for firmware updates
3. Use backup YubiKey for access
4. Contact Yubico support if under warranty
EOF

chown dave:dave /home/dave/yubikey_security_checklist.md

# Create advanced SSH configuration for YubiKey
cat > /home/dave/.ssh/config_yubikey_template << 'EOF'
# YubiKey SSH Configuration Template
# Copy to ~/.ssh/config when YubiKey is set up

Host ebon-yubikey
    HostName 10.0.0.29
    User ebon
    Port 22
    IdentityFile ~/.ssh/yubikey_ecdsa
    IdentitiesOnly yes
    PubkeyAuthentication yes
    PasswordAuthentication no
    ChallengeResponseAuthentication no
    # Require YubiKey touch for every connection
    AddKeysToAgent no
    VerifyHostKeyDNS yes
    StrictHostKeyChecking yes

Host *
    # Security defaults
    Protocol 2
    Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
    MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com
    KexAlgorithms curve25519-sha256@libssh.org,diffie-hellman-group16-sha512
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive no
    # Disable unused authentication methods
    GSSAPIAuthentication no
    HostbasedAuthentication no
EOF

chown dave:dave /home/dave/.ssh/config_yubikey_template

echo -e "${GREEN}✅ YubiKey preparation complete!${NC}"
echo
echo -e "${YELLOW}📋 What's been prepared:${NC}"
echo "- YubiKey management tools installed"
echo "- FIDO2/WebAuthn support configured"
echo "- Udev rules for device access"
echo "- PAM modules for authentication"
echo "- SSH configuration templates"
echo "- Security checklist created"
echo
echo -e "${YELLOW}📝 When your YubiKey arrives:${NC}"
echo "1. Run: sudo /usr/local/bin/test-yubikey.sh"
echo "2. Follow: ~/yubikey_security_checklist.md"
echo "3. Configure SSH: ~/.ssh/yubikey_setup.md"
echo "4. Test functionality with your home server"
echo
echo -e "${YELLOW}📁 Files created:${NC}"
echo "- /home/dave/.ssh/yubikey_setup.md"
echo "- /home/dave/yubikey_security_checklist.md"
echo "- /home/dave/.ssh/config_yubikey_template"
echo "- /usr/local/bin/test-yubikey.sh"
echo
echo -e "${GREEN}🔑 Ready for YubiKey 5!${NC}"