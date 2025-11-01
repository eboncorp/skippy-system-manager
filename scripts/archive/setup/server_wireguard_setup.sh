#!/bin/bash
# WireGuard VPN Server Setup for HP Z4 G4 "ebon"
# Run on server as: sudo bash server_wireguard_setup.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔒 WireGuard VPN Server Setup${NC}"
echo "=============================="
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Please run as root: sudo bash $0${NC}"
    exit 1
fi

# Get server IP
SERVER_IP=$(ip route get 8.8.8.8 | grep -oP 'src \K\S+')
echo -e "${YELLOW}📍 Server IP detected: $SERVER_IP${NC}"

# Install WireGuard
echo -e "${YELLOW}📦 Installing WireGuard...${NC}"
apt update
apt install -y wireguard wireguard-tools

# Create WireGuard directory
mkdir -p /etc/wireguard
chmod 700 /etc/wireguard
cd /etc/wireguard

# Generate server keys
echo -e "${YELLOW}🔑 Generating server keys...${NC}"
wg genkey | tee server_private.key | wg pubkey > server_public.key
chmod 600 server_private.key
chmod 644 server_public.key

# Create WireGuard server configuration
echo -e "${YELLOW}⚙️ Creating server configuration...${NC}"
cat > /etc/wireguard/wg0.conf << EOF
[Interface]
PrivateKey = $(cat server_private.key)
Address = 10.9.0.1/24
ListenPort = 51820
SaveConfig = true

# Enable IP forwarding
PostUp = echo 1 > /proc/sys/net/ipv4/ip_forward
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT
PostUp = iptables -A FORWARD -o wg0 -j ACCEPT
PostUp = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT
PostDown = iptables -D FORWARD -o wg0 -j ACCEPT
PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# Client: Dave's Laptop
[Peer]
PublicKey = LAPTOP_PUBLIC_KEY_HERE
AllowedIPs = 10.9.0.2/32
EOF

# Enable IP forwarding permanently
echo 'net.ipv4.ip_forward = 1' >> /etc/sysctl.conf
sysctl -p

# Configure firewall for WireGuard
echo -e "${YELLOW}🔥 Configuring firewall...${NC}"
ufw allow 51820/udp comment "WireGuard VPN"
ufw allow from 10.9.0.0/24 comment "WireGuard clients"

# Enable and start WireGuard
echo -e "${YELLOW}🚀 Starting WireGuard service...${NC}"
systemctl enable wg-quick@wg0
systemctl start wg-quick@wg0

# Create client management scripts
echo -e "${YELLOW}📝 Creating management scripts...${NC}"

# Add client script
cat > /usr/local/bin/add-vpn-client.sh << 'EOF'
#!/bin/bash
# Add a new VPN client

if [ $# -ne 3 ]; then
    echo "Usage: $0 <client_name> <client_public_key> <client_ip>"
    echo "Example: $0 laptop AbC123... 10.9.0.2"
    exit 1
fi

CLIENT_NAME=$1
CLIENT_PUBLIC_KEY=$2
CLIENT_IP=$3

# Add peer to WireGuard config
wg set wg0 peer $CLIENT_PUBLIC_KEY allowed-ips $CLIENT_IP/32

# Save configuration
wg-quick save wg0

echo "✅ Client $CLIENT_NAME added with IP $CLIENT_IP"
EOF

chmod +x /usr/local/bin/add-vpn-client.sh

# Remove client script
cat > /usr/local/bin/remove-vpn-client.sh << 'EOF'
#!/bin/bash
# Remove a VPN client

if [ $# -ne 1 ]; then
    echo "Usage: $0 <client_public_key>"
    exit 1
fi

CLIENT_PUBLIC_KEY=$1

# Remove peer from WireGuard
wg set wg0 peer $CLIENT_PUBLIC_KEY remove

# Save configuration
wg-quick save wg0

echo "✅ Client removed"
EOF

chmod +x /usr/local/bin/remove-vpn-client.sh

# Status monitoring script
cat > /usr/local/bin/vpn-status.sh << 'EOF'
#!/bin/bash
# VPN status monitoring

echo "=== WireGuard VPN Status ==="
echo
echo "Interface Status:"
wg show
echo
echo "Connected Clients:"
wg show wg0 peers
echo
echo "Traffic Statistics:"
wg show wg0 transfer
echo
echo "Firewall Status:"
ufw status | grep -E "(51820|10.9.0)"
echo
EOF

chmod +x /usr/local/bin/vpn-status.sh

echo -e "${GREEN}✅ WireGuard VPN Server Setup Complete!${NC}"
echo
echo -e "${YELLOW}📋 Configuration Summary:${NC}"
echo "- VPN Network: 10.9.0.0/24"
echo "- Server IP: 10.9.0.1"
echo "- Listen Port: 51820"
echo "- Server Public Key: $(cat server_public.key)"
echo
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "1. Update laptop client config with server public key"
echo "2. Add laptop public key to server using:"
echo "   sudo /usr/local/bin/add-vpn-client.sh laptop LAPTOP_KEY 10.9.0.2"
echo "3. Test connection from laptop"
echo "4. Monitor with: sudo /usr/local/bin/vpn-status.sh"
echo
echo -e "${GREEN}🔑 Server Public Key (copy this):${NC}"
cat server_public.key
echo