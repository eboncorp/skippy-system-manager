#!/bin/bash
# Setup mDNS/Avahi for easy network discovery
# This allows accessing the server as hostname.local

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Setting up mDNS for easy network discovery${NC}"

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${RED}Please run without sudo. Script will ask for password when needed.${NC}"
   exit 1
fi

# Install avahi if not present
if ! command -v avahi-daemon &> /dev/null; then
    echo -e "${YELLOW}Installing Avahi mDNS service...${NC}"
    sudo apt-get update
    sudo apt-get install -y avahi-daemon avahi-utils libnss-mdns
else
    echo -e "${GREEN}✓ Avahi is already installed${NC}"
fi

# Create custom service file for home server
echo -e "${BLUE}Creating mDNS service advertisement...${NC}"

sudo tee /etc/avahi/services/home-server.service > /dev/null << EOF
<?xml version="1.0" standalone='no'?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name>Home Server Master</name>
  <service>
    <type>_http._tcp</type>
    <port>8080</port>
    <txt-record>path=/</txt-record>
    <txt-record>version=1.0.0</txt-record>
  </service>
  <service>
    <type>_home-server._tcp</type>
    <port>8080</port>
    <txt-record>version=1.0.0</txt-record>
    <txt-record>platform=linux</txt-record>
  </service>
</service-group>
EOF

# Ensure avahi is running
echo -e "${BLUE}Starting Avahi service...${NC}"
sudo systemctl enable avahi-daemon
sudo systemctl restart avahi-daemon

# Wait for service to start
sleep 2

# Test mDNS resolution
echo -e "\n${BLUE}Testing mDNS resolution...${NC}"
HOSTNAME=$(hostname)

echo -e "${GREEN}Your server will be accessible as:${NC}"
echo "  • http://${HOSTNAME}.local:8080"
echo "  • ${HOSTNAME}.local"

# Show discovered services
echo -e "\n${BLUE}Broadcasting services:${NC}"
avahi-browse -art | grep -E "(${HOSTNAME}|Home Server)" || echo "Services still propagating..."

# Create helper script for other machines
cat > /tmp/find_home_server.sh << 'EOF'
#!/bin/bash
# Run this on other machines to find the home server

echo "Searching for Home Server on the network..."

# Method 1: Avahi browse
if command -v avahi-browse &> /dev/null; then
    echo "Using Avahi to find services..."
    avahi-browse -rt _home-server._tcp 2>/dev/null | grep -E "(address|port|hostname)" | head -6
else
    echo "Avahi not installed. Install with: sudo apt install avahi-utils"
fi

# Method 2: DNS-SD (macOS/Windows)
if command -v dns-sd &> /dev/null; then
    echo "Using DNS-SD to find services..."
    timeout 5 dns-sd -B _home-server._tcp || true
fi

# Method 3: Direct mDNS query
echo -e "\nTrying direct hostname resolution..."
for suffix in ".local" ".home" ".lan" ""; do
    if ping -c 1 -W 1 "$(hostname)${suffix}" &>/dev/null; then
        echo "Found at: $(hostname)${suffix}"
        host "$(hostname)${suffix}" 2>/dev/null || true
    fi
done
EOF

chmod +x /tmp/find_home_server.sh

echo -e "\n${GREEN}✓ mDNS setup complete!${NC}"
echo -e "\n${BLUE}How to access your server:${NC}"
echo "1. From any device on the same network, use:"
echo "   http://${HOSTNAME}.local:8080"
echo ""
echo "2. To find the server from another Linux machine:"
echo "   avahi-browse -rt _home-server._tcp"
echo "   or"
echo "   avahi-resolve -n ${HOSTNAME}.local"
echo ""
echo "3. From macOS:"
echo "   dns-sd -B _home-server._tcp"
echo "   or just use: http://${HOSTNAME}.local:8080"
echo ""
echo "4. From Windows (with Bonjour installed):"
echo "   The server should appear in network discovery"
echo "   or use: http://${HOSTNAME}.local:8080"
echo ""
echo -e "${YELLOW}Note: mDNS may take 1-2 minutes to propagate on the network${NC}"
echo -e "\n${GREEN}Discovery script saved to: /tmp/find_home_server.sh${NC}"