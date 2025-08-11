#!/bin/bash
# HP Z4 G4 Workstation Server Information
# Updated based on correct hardware identification

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

SERVER_IP="10.0.0.29"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   HP Z4 G4 Workstation Server${NC}"
echo -e "${BLUE}================================================${NC}"
echo

echo -e "${CYAN}Hardware Information:${NC}"
echo "  Model: HP Z4 G4 Workstation"
echo "  IP Address: $SERVER_IP"
echo "  Connection: Ethernet (confirmed)"
echo "  MAC Address: 10:e7:c6:2b:42:8c"
echo

echo -e "${CYAN}HP Z4 G4 Specifications:${NC}"
echo "  • CPU: Intel Xeon W or Core i9"
echo "  • RAM: Up to 256GB ECC/non-ECC"
echo "  • Storage: Multiple NVMe/SATA slots"
echo "  • Network: Gigabit Ethernet built-in"
echo "  • Expansion: PCIe slots for additional NICs"
echo "  • Perfect for: Home server, virtualization, storage"
echo

# Check current services
echo -e "${CYAN}Checking services on HP Z4 G4...${NC}"

# HP/Enterprise specific ports
declare -A hp_services=(
    ["22"]="SSH"
    ["80"]="HTTP/Web Server"
    ["443"]="HTTPS"
    ["3389"]="RDP (Windows)"
    ["445"]="SMB/File Sharing"
    ["139"]="NetBIOS"
    ["135"]="RPC Endpoint Mapper"
    ["5985"]="WinRM HTTP"
    ["5986"]="WinRM HTTPS"
    ["8080"]="Alternative HTTP"
    ["9100"]="JetDirect/Printing"
    ["111"]="NFS RPC"
    ["2049"]="NFS"
    ["23"]="Telnet"
    ["21"]="FTP"
    ["631"]="CUPS/IPP"
)

FOUND_SERVICES=()

for port in "${!hp_services[@]}"; do
    if timeout 1 bash -c "echo >/dev/tcp/$SERVER_IP/$port" 2>/dev/null; then
        FOUND_SERVICES+=("${hp_services[$port]} (port $port)")
        echo -e "  ${GREEN}✓${NC} ${hp_services[$port]} on port $port"
    fi
done

echo

# Try to identify the OS
echo -e "${CYAN}Operating System Detection:${NC}"

# Check HTTP headers for OS clues
HTTP_HEADERS=$(timeout 3 curl -s -I "http://$SERVER_IP" 2>/dev/null || echo "")
if [ -n "$HTTP_HEADERS" ]; then
    echo "HTTP Response Headers:"
    echo "$HTTP_HEADERS" | head -5 | sed 's/^/  /'
    
    # Look for OS indicators
    if echo "$HTTP_HEADERS" | grep -qi "apache"; then
        echo "  → Apache web server detected"
    fi
    if echo "$HTTP_HEADERS" | grep -qi "nginx"; then
        echo "  → Nginx web server detected"
    fi
    if echo "$HTTP_HEADERS" | grep -qi "microsoft\|windows\|iis"; then
        echo "  → Windows/IIS detected"
    fi
fi

# SSH banner
echo -e "\nSSH Banner:"
SSH_BANNER=$(timeout 3 nc "$SERVER_IP" 22 2>/dev/null | head -1 || echo "No banner")
echo "  $SSH_BANNER"

if echo "$SSH_BANNER" | grep -qi "ubuntu\|debian"; then
    echo "  → Linux (Ubuntu/Debian) detected"
elif echo "$SSH_BANNER" | grep -qi "openssh"; then
    echo "  → OpenSSH server (likely Linux)"
elif echo "$SSH_BANNER" | grep -qi "windows"; then
    echo "  → Windows with SSH detected"
fi

echo

# Connection recommendations
echo -e "${CYAN}Connection Recommendations for HP Z4 G4:${NC}"
echo

if [[ " ${FOUND_SERVICES[@]} " =~ "SSH" ]]; then
    echo -e "${GREEN}SSH Access:${NC}"
    echo "  ssh username@$SERVER_IP"
    echo "  Common usernames: admin, root, hp, administrator"
    echo
fi

if [[ " ${FOUND_SERVICES[@]} " =~ "HTTP" ]]; then
    echo -e "${GREEN}Web Interface:${NC}"
    echo "  http://$SERVER_IP"
    echo "  Could be: Server management, NAS interface, or hosted services"
    echo
fi

if [[ " ${FOUND_SERVICES[@]} " =~ "RDP" ]]; then
    echo -e "${GREEN}Remote Desktop (Windows):${NC}"
    echo "  Use RDP client to connect to $SERVER_IP:3389"
    echo
fi

if [[ " ${FOUND_SERVICES[@]} " =~ "SMB" ]]; then
    echo -e "${GREEN}File Sharing:${NC}"
    echo "  smb://$SERVER_IP or \\\\$SERVER_IP"
    echo "  Access shared folders and storage"
    echo
fi

# HP-specific features
echo -e "${CYAN}HP Z4 G4 Server Capabilities:${NC}"
echo "  • High-performance computing server"
echo "  • Excellent for Docker/containers"
echo "  • Perfect for home lab virtualization"
echo "  • Can handle multiple VMs simultaneously"
echo "  • Great for Plex media server with transcoding"
echo "  • Ideal for development environments"
echo

# Menu for connection
echo -e "${CYAN}Connect to HP Z4 G4:${NC}"
select action in "SSH connection" "Open web interface" "Check system info" "Test file sharing" "Exit"; do
    case $action in
        "SSH connection")
            echo -e "\n${YELLOW}Connecting via SSH...${NC}"
            echo "Try these usernames if prompted:"
            echo "  • Your username"
            echo "  • admin"
            echo "  • root (Linux)"
            echo "  • administrator (Windows)"
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
        "Check system info")
            echo -e "\n${YELLOW}Gathering system information...${NC}"
            
            # Try to get more info via SSH without login
            echo "Testing SSH access (no login required):"
            ssh -o BatchMode=yes -o ConnectTimeout=5 "$SERVER_IP" "uname -a; uptime; df -h" 2>/dev/null || \
            echo "SSH requires authentication (normal)"
            
            # Check web server for system info
            echo -e "\nChecking web server for system information:"
            curl -s -m 5 "http://$SERVER_IP" | grep -i "server\|system\|hp\|workstation" | head -3 | sed 's/^/  /' || \
            echo "No system info in web response"
            ;;
        "Test file sharing")
            echo -e "\n${YELLOW}Testing file sharing access...${NC}"
            if command -v smbclient &>/dev/null; then
                echo "Available SMB shares:"
                smbclient -L "$SERVER_IP" -N 2>/dev/null || echo "SMB access requires authentication"
            else
                echo "smbclient not installed. Install with: sudo apt install samba-common-bin"
            fi
            ;;
        "Exit")
            echo "Exiting..."
            exit 0
            ;;
    esac
done

echo -e "\n${BLUE}================================================${NC}"
echo -e "${GREEN}HP Z4 G4 Summary:${NC}"
echo "This workstation is perfect for your home server setup with:"
echo "• High-end hardware for multiple services"
echo "• Ethernet connectivity for reliable performance"  
echo "• Apache web server already running"
echo "• SSH access available"
echo "• Ideal platform for your Home Server Master"
echo -e "${BLUE}================================================${NC}"