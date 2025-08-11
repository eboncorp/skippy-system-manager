#!/bin/bash
# Laptop Security Hardening Script
# Run with: sudo bash laptop_security_setup.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔒 Laptop Security Hardening Setup${NC}"
echo "===================================="
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Please run as root: sudo bash $0${NC}"
    exit 1
fi

# Update system packages
echo -e "${YELLOW}📦 Updating system packages...${NC}"
apt update && apt upgrade -y

# Install security packages
echo -e "${YELLOW}🛡️ Installing security packages...${NC}"
apt install -y \
    ufw \
    fail2ban \
    wireguard \
    wireguard-tools \
    resolvconf \
    rkhunter \
    chkrootkit \
    lynis \
    auditd \
    apparmor \
    apparmor-utils

# Configure UFW Firewall
echo -e "${YELLOW}🔥 Configuring UFW firewall...${NC}"

# Reset UFW to defaults
ufw --force reset

# Set default policies
ufw default deny incoming
ufw default deny outgoing
ufw default deny forward

# Allow loopback
ufw allow in on lo
ufw allow out on lo

# Allow essential outgoing connections
ufw allow out 53/udp comment "DNS"
ufw allow out 80/tcp comment "HTTP"
ufw allow out 443/tcp comment "HTTPS" 
ufw allow out 123/udp comment "NTP"

# Allow SSH (current session protection)
ufw allow out 22/tcp comment "SSH outgoing"
ufw allow in 22/tcp comment "SSH incoming"

# Allow WireGuard port (will be configured later)
ufw allow 51820/udp comment "WireGuard VPN"

# Allow local network access (temporary - will be restricted after VPN setup)
ufw allow out to 10.0.0.0/24 comment "Local network (temporary)"

# Enable UFW
ufw --force enable

echo -e "${GREEN}✅ UFW firewall configured${NC}"

# Configure Fail2Ban
echo -e "${YELLOW}🚫 Configuring Fail2Ban...${NC}"

# Create custom jail configuration
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
# Ban hosts for 24 hours
bantime = 86400

# Find time window (10 minutes)
findtime = 600

# Number of failures before ban
maxretry = 3

# Backend for monitoring
backend = auto

# Destination email for notifications
destemail = root@localhost

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 86400
findtime = 600

[ufw]
enabled = true
port = all
filter = ufw
logpath = /var/log/ufw.log
maxretry = 5
bantime = 3600
EOF

# Restart and enable fail2ban
systemctl enable fail2ban
systemctl restart fail2ban

echo -e "${GREEN}✅ Fail2Ban configured${NC}"

# SSH Hardening
echo -e "${YELLOW}🔐 Hardening SSH configuration...${NC}"

# Backup original SSH config
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# Create hardened SSH config
cat > /etc/ssh/sshd_config << 'EOF'
# Hardened SSH Configuration for Laptop

# Network
Port 22
Protocol 2
ListenAddress 0.0.0.0

# Authentication
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
PermitEmptyPasswords no
ChallengeResponseAuthentication no
UsePAM yes

# Security settings
X11Forwarding no
AllowTcpForwarding no
AllowAgentForwarding no
PermitTunnel no
GatewayPorts no
PermitUserEnvironment no

# Connection limits
MaxAuthTries 3
MaxSessions 2
MaxStartups 2
LoginGraceTime 30

# Logging
SyslogFacility AUTH
LogLevel INFO

# Ciphers and algorithms (secure only)
KexAlgorithms curve25519-sha256@libssh.org,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512,diffie-hellman-group14-sha256
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr
MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com,hmac-sha2-256,hmac-sha2-512

# Additional security
ClientAliveInterval 300
ClientAliveCountMax 2
Compression no
TCPKeepAlive no
AllowUsers dave

# Banner
Banner /etc/ssh/banner
EOF

# Create SSH banner
cat > /etc/ssh/banner << 'EOF'
***************************************************************************
                            AUTHORIZED ACCESS ONLY
                           
This system is for authorized users only. All activity is monitored and
logged. Unauthorized access is prohibited and may result in criminal
prosecution.
***************************************************************************
EOF

# Restart SSH service
systemctl restart sshd

echo -e "${GREEN}✅ SSH hardened${NC}"

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
cat > /etc/wireguard/home-server.conf << 'EOF'
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
grep "authentication failure\|Failed password" /var/log/auth.log | tail -10
echo

echo "WireGuard Status:"
wg show
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
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Your laptop WireGuard public key is in: /etc/wireguard/laptop_public.key"
echo "2. Configure your home server with this public key"
echo "3. Update /etc/wireguard/home-server.conf with your server's public key"
echo "4. Test VPN connection: sudo wg-quick up home-server"
echo "5. Run daily security check: sudo /usr/local/bin/security-check.sh"
echo
echo -e "${YELLOW}⚠️ Important:${NC}"
echo "- Reboot recommended to apply all security settings"
echo "- SSH password authentication is now DISABLED"
echo "- Ensure you have SSH key access before disconnecting"
echo "- VPN must be configured before restricting local network access"

# Display public key for server configuration
echo
echo -e "${GREEN}📋 Your Laptop's WireGuard Public Key:${NC}"
cat /etc/wireguard/laptop_public.key
echo