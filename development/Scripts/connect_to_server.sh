#!/bin/bash
# Connect to Ethernet server at 10.0.0.29
# Apple device with SSH and HTTP services

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

SERVER_IP="10.0.0.29"
SERVER_MAC="10:e7:c6:2b:42:8c"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   Ethernet Server Connection Tool${NC}"
echo -e "${BLUE}================================================${NC}"
echo

echo -e "${CYAN}Server Information:${NC}"
echo "  IP Address: $SERVER_IP"
echo "  MAC Address: $SERVER_MAC (Apple device)"
echo "  Connection: Ethernet (confirmed)"
echo "  Services: SSH (port 22), HTTP (port 80)"
echo

# Check connectivity
echo -e "${CYAN}Checking connectivity...${NC}"
if ping -c 2 -W 1 "$SERVER_IP" &>/dev/null; then
    PING_TIME=$(ping -c 1 -W 1 "$SERVER_IP" 2>/dev/null | grep "time=" | cut -d'=' -f4)
    echo -e "${GREEN}✓ Server is online${NC} (ping: $PING_TIME)"
else
    echo -e "${RED}✗ Server is not responding to ping${NC}"
    exit 1
fi

# Scan for additional services
echo -e "\n${CYAN}Scanning for services...${NC}"

# Common Apple/Mac services
declare -A services=(
    ["22"]="SSH"
    ["80"]="HTTP"
    ["443"]="HTTPS"
    ["548"]="AFP (Apple File Protocol)"
    ["5900"]="VNC/Screen Sharing"
    ["3283"]="Apple Remote Desktop"
    ["88"]="Kerberos"
    ["445"]="SMB/File Sharing"
    ["631"]="IPP/CUPS (Printing)"
    ["3689"]="iTunes/Music Sharing"
    ["5353"]="mDNS/Bonjour"
)

FOUND_SERVICES=()

for port in "${!services[@]}"; do
    if timeout 1 bash -c "echo >/dev/tcp/$SERVER_IP/$port" 2>/dev/null; then
        FOUND_SERVICES+=("${services[$port]} (port $port)")
        echo -e "  ${GREEN}✓${NC} ${services[$port]} on port $port"
    fi
done

# Try to get hostname via various methods
echo -e "\n${CYAN}Identifying server...${NC}"

# Method 1: Reverse DNS
HOSTNAME=$(timeout 2 getent hosts "$SERVER_IP" 2>/dev/null | awk '{print $2}' || echo "")
if [ -n "$HOSTNAME" ]; then
    echo "  Hostname (DNS): $HOSTNAME"
fi

# Method 2: Try to get hostname via HTTP
HTTP_RESP=$(timeout 2 curl -s -I "http://$SERVER_IP" 2>/dev/null | grep -i "server:" || echo "")
if [ -n "$HTTP_RESP" ]; then
    echo "  Web Server: $HTTP_RESP"
fi

# Method 3: Check mDNS
if command -v avahi-resolve &>/dev/null; then
    MDNS_NAME=$(timeout 2 avahi-resolve -a "$SERVER_IP" 2>/dev/null | awk '{print $2}' || echo "")
    if [ -n "$MDNS_NAME" ]; then
        echo "  mDNS Name: $MDNS_NAME"
    fi
fi

# Connection options
echo -e "\n${CYAN}Connection Options:${NC}"
echo

echo -e "${GREEN}1. SSH Connection:${NC}"
echo "   ssh user@$SERVER_IP"
echo "   ssh $SERVER_IP -l username"
echo

echo -e "${GREEN}2. Web Interface:${NC}"
echo "   http://$SERVER_IP"
if [[ " ${FOUND_SERVICES[@]} " =~ "HTTPS" ]]; then
    echo "   https://$SERVER_IP"
fi
echo

if [[ " ${FOUND_SERVICES[@]} " =~ "VNC" ]]; then
    echo -e "${GREEN}3. Screen Sharing/VNC:${NC}"
    echo "   vnc://$SERVER_IP"
    echo "   Or use a VNC client to connect to $SERVER_IP:5900"
    echo
fi

if [[ " ${FOUND_SERVICES[@]} " =~ "SMB" ]] || [[ " ${FOUND_SERVICES[@]} " =~ "AFP" ]]; then
    echo -e "${GREEN}4. File Sharing:${NC}"
    if [[ " ${FOUND_SERVICES[@]} " =~ "SMB" ]]; then
        echo "   SMB: smb://$SERVER_IP"
    fi
    if [[ " ${FOUND_SERVICES[@]} " =~ "AFP" ]]; then
        echo "   AFP: afp://$SERVER_IP"
    fi
    echo
fi

# Quick connection menu
echo -e "${CYAN}Quick Connect:${NC}"
select action in "SSH to server" "Open web interface" "Scan for users" "Test SSH access" "Exit"; do
    case $action in
        "SSH to server")
            echo -e "\n${YELLOW}Attempting SSH connection...${NC}"
            echo "If prompted for username, try: admin, root, or your Mac username"
            ssh "$SERVER_IP"
            break
            ;;
        "Open web interface")
            echo -e "\n${YELLOW}Opening web interface...${NC}"
            if command -v xdg-open &>/dev/null; then
                xdg-open "http://$SERVER_IP" 2>/dev/null &
            else
                echo "Please open: http://$SERVER_IP"
            fi
            break
            ;;
        "Scan for users")
            echo -e "\n${YELLOW}Attempting to enumerate users...${NC}"
            # Try SSH banner
            echo "SSH Banner:"
            timeout 2 nc -v "$SERVER_IP" 22 2>&1 | head -5 || echo "No banner"
            
            # Try finger if available
            if timeout 1 bash -c "echo >/dev/tcp/$SERVER_IP/79" 2>/dev/null; then
                echo -e "\nFinger service detected, trying to list users..."
                echo "" | nc "$SERVER_IP" 79 2>/dev/null | head -10
            fi
            ;;
        "Test SSH access")
            echo -e "\n${YELLOW}Testing SSH access...${NC}"
            ssh -o BatchMode=yes -o ConnectTimeout=5 "$SERVER_IP" exit 2>&1 || echo -e "\n${YELLOW}SSH requires authentication. This is normal.${NC}"
            echo -e "\nTry these common Mac usernames:"
            echo "  • admin"
            echo "  • administrator" 
            echo "  • Your first name (lowercase)"
            echo "  • First letter of first name + last name"
            ;;
        "Exit")
            echo "Exiting..."
            exit 0
            ;;
    esac
done

echo -e "\n${BLUE}================================================${NC}"
echo -e "${CYAN}Tips:${NC}"
echo "• This appears to be a Mac/Apple device based on the MAC address"
echo "• If it's a Mac Mini or Mac Studio, it might be a server"
echo "• Check for Time Machine backups at: afp://$SERVER_IP or smb://$SERVER_IP"
echo "• Mac SSH is usually enabled in: System Preferences → Sharing → Remote Login"
echo -e "${BLUE}================================================${NC}"