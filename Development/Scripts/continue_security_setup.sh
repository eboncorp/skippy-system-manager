#!/bin/bash
# Continue laptop security setup after SSH issue
# Run with: sudo bash continue_security_setup.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔧 Continuing Laptop Security Setup${NC}"
echo "===================================="
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Please run as root: sudo bash $0${NC}"
    exit 1
fi

# SSH Client Configuration (no server needed)
echo -e "${YELLOW}🔐 Configuring SSH client...${NC}"

# Create SSH client security config for user
sudo -u dave mkdir -p /home/dave/.ssh
cat > /home/dave/.ssh/config << 'EOF'
# Secure SSH Client Configuration

Host *
    # Security settings
    Protocol 2
    Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
    MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com
    KexAlgorithms curve25519-sha256@libssh.org,diffie-hellman-group16-sha512
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive no
    
    # Authentication
    PubkeyAuthentication yes
    PasswordAuthentication no
    ChallengeResponseAuthentication no
    GSSAPIAuthentication no
    HostbasedAuthentication no
    
    # Host key verification
    StrictHostKeyChecking ask
    VerifyHostKeyDNS yes
    
    # Connection settings
    ConnectTimeout 10
    ServerAliveInterval 60
EOF

# Set proper permissions
chown dave:dave /home/dave/.ssh/config
chmod 600 /home/dave/.ssh/config

echo -e "${GREEN}✅ SSH client configured${NC}"

# Enable audit daemon
echo -e "${YELLOW}📊 Configuring system auditing...${NC}"
systemctl enable auditd
systemctl start auditd

# Configure automatic security updates
echo -e "${YELLOW}🔄 Configuring automatic security updates...${NC}"
apt install -y unattended-upgrades

# Configure unattended upgrades for security updates only
cat > /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
};

Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF

# Enable automatic updates
echo 'APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";' > /etc/apt/apt.conf.d/10periodic

echo -e "${GREEN}✅ Automatic security updates configured${NC}"

# Create WireGuard directory structure
echo -e "${YELLOW}🔧 Preparing WireGuard configuration...${NC}"
mkdir -p /etc/wireguard
chmod 700 /etc/wireguard

# Generate WireGuard keys
cd /etc/wireguard
wg genkey | tee laptop_private.key | wg pubkey > laptop_public.key
chmod 600 laptop_private.key
chmod 644 laptop_public.key

echo -e "${GREEN}✅ WireGuard keys generated${NC}"

# Create WireGuard configuration template
cat > /etc/wireguard/home-server.conf << EOF
[Interface]
PrivateKey = $(cat /etc/wireguard/laptop_private.key)
Address = 10.9.0.2/24
DNS = 1.1.1.1, 1.0.0.1

[Peer]
# Home Server (HP Z4 G4 "ebon")
PublicKey = SERVER_PUBLIC_KEY_HERE
Endpoint = YOUR_HOME_IP:51820
AllowedIPs = 10.9.0.0/24, 192.168.30.0/24, 192.168.50.0/24
PersistentKeepalive = 25
EOF

echo -e "${GREEN}✅ WireGuard configuration template created${NC}"

# System security settings
echo -e "${YELLOW}⚙️ Applying system security settings...${NC}"

# Disable unnecessary services
systemctl disable bluetooth.service 2>/dev/null || true
systemctl disable cups.service 2>/dev/null || true

# Configure kernel security parameters
cat > /etc/sysctl.d/99-security.conf << 'EOF'
# Network security
net.ipv4.ip_forward = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.tcp_syncookies = 1

# IPv6 security
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# Process security
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
kernel.yama.ptrace_scope = 1
EOF

sysctl -p /etc/sysctl.d/99-security.conf

echo -e "${GREEN}✅ System security settings applied${NC}"

# Create security monitoring script
cat > /usr/local/bin/security-check.sh << 'EOF'
#!/bin/bash
# Daily security check script

echo "=== Security Status Report $(date) ==="
echo

echo "UFW Status:"
ufw status numbered
echo

echo "Fail2Ban Status:"
fail2ban-client status
echo

echo "Recent Authentication Failures:"
grep "authentication failure\|Failed password" /var/log/auth.log 2>/dev/null | tail -10 || echo "No auth failures found"
echo

echo "WireGuard Status:"
wg show 2>/dev/null || echo "WireGuard not connected"
echo

echo "System Updates Available:"
apt list --upgradable 2>/dev/null | wc -l
echo

echo "Listening Services:"
ss -tuln
echo
EOF

chmod +x /usr/local/bin/security-check.sh

# Create daily security check cron job
echo "0 9 * * * root /usr/local/bin/security-check.sh >> /var/log/security-check.log 2>&1" > /etc/cron.d/security-check

echo -e "${GREEN}✅ Security monitoring configured${NC}"

echo
echo -e "${GREEN}🎉 Laptop Security Hardening Complete!${NC}"
echo
echo -e "${YELLOW}📋 What was secured:${NC}"
echo "✅ Firewall: Restrictive rules (deny all except essential)"
echo "✅ Fail2ban: Automatic intrusion prevention"
echo "✅ SSH Client: Secure configuration"
echo "✅ WireGuard: VPN keys generated"
echo "✅ System: Kernel security parameters"
echo "✅ Updates: Automatic security patches"
echo "✅ Monitoring: Daily security checks"
echo
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Your laptop WireGuard public key is in: /etc/wireguard/laptop_public.key"
echo "2. Set up VPN server on your HP Z4 G4"
echo "3. Update /etc/wireguard/home-server.conf with server details"
echo "4. Test VPN connection: sudo wg-quick up home-server"
echo "5. Run security check: sudo /usr/local/bin/security-check.sh"
echo
echo -e "${YELLOW}⚠️ Important:${NC}"
echo "- Reboot recommended to apply all security settings"
echo "- Firewall is now restrictive - only VPN traffic allowed"
echo "- All outgoing connections require explicit firewall rules"
echo

# Display public key for server configuration
echo
echo -e "${GREEN}📋 Your Laptop's WireGuard Public Key (COPY THIS):${NC}"
echo "============================================="
cat /etc/wireguard/laptop_public.key
echo "============================================="
echo