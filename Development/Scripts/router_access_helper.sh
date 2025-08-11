#!/bin/bash
# Router Access Helper - Opens router interfaces and provides guidance

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   Router Access Helper${NC}"
echo -e "${BLUE}================================================${NC}"
echo

# Check which routers are available
echo -e "${CYAN}Checking router availability...${NC}"
echo

ROUTERS=(
    "10.0.0.1|Main Gateway"
    "10.0.0.4|Access Point 1"
    "10.0.0.5|Access Point 2"
)

AVAILABLE_ROUTERS=()

for router_info in "${ROUTERS[@]}"; do
    IFS='|' read -r IP DESC <<< "$router_info"
    
    if ping -c 1 -W 1 "$IP" &>/dev/null; then
        echo -e "${GREEN}✓${NC} $IP ($DESC) - Online"
        
        # Check HTTP/HTTPS
        if curl -s -m 2 "http://$IP" &>/dev/null; then
            echo "  → HTTP available"
            AVAILABLE_ROUTERS+=("http://$IP")
        fi
        
        if curl -s -m 2 -k "https://$IP" &>/dev/null; then
            echo "  → HTTPS available"
            AVAILABLE_ROUTERS+=("https://$IP")
        fi
    else
        echo -e "✗ $IP ($DESC) - Offline"
    fi
    echo
done

echo -e "${CYAN}Router Login Information:${NC}"
echo "Based on the server response (uhttpd), these appear to be OpenWrt/LEDE routers."
echo
echo -e "${YELLOW}Common default credentials for OpenWrt:${NC}"
echo "  • Username: root or admin"
echo "  • Password: admin, password, or blank"
echo
echo -e "${YELLOW}Common default credentials for Gigaset routers:${NC}"
echo "  • Username: admin"
echo "  • Password: admin, password, or check router label"
echo

# Function to open router interface
open_router() {
    local url=$1
    echo -e "${CYAN}Opening $url in your default browser...${NC}"
    
    # Try different methods to open browser
    if command -v xdg-open &> /dev/null; then
        xdg-open "$url" 2>/dev/null &
    elif command -v gnome-open &> /dev/null; then
        gnome-open "$url" 2>/dev/null &
    elif command -v firefox &> /dev/null; then
        firefox "$url" 2>/dev/null &
    elif command -v google-chrome &> /dev/null; then
        google-chrome "$url" 2>/dev/null &
    elif command -v sensible-browser &> /dev/null; then
        sensible-browser "$url" 2>/dev/null &
    else
        echo -e "${YELLOW}Could not open browser automatically.${NC}"
        echo "Please open manually: $url"
    fi
}

# Menu to select router
if [ ${#AVAILABLE_ROUTERS[@]} -eq 0 ]; then
    echo -e "${YELLOW}No routers responded to HTTP/HTTPS requests.${NC}"
    echo "Try accessing directly:"
    echo "  • http://10.0.0.1"
    echo "  • https://10.0.0.1"
    exit 1
fi

echo -e "${CYAN}Select a router to access:${NC}"
select router_url in "${AVAILABLE_ROUTERS[@]}" "Open all" "Exit"; do
    case $router_url in
        "Open all")
            for url in "${AVAILABLE_ROUTERS[@]}"; do
                open_router "$url"
                sleep 1
            done
            break
            ;;
        "Exit")
            echo "Exiting..."
            exit 0
            ;;
        *)
            if [ -n "$router_url" ]; then
                open_router "$router_url"
                break
            fi
            ;;
    esac
done

echo
echo -e "${CYAN}What to look for in the router interface:${NC}"
echo "1. Navigate to: Status → Overview or Connected Devices"
echo "2. Look for: DHCP Clients, Device List, or Network Map"
echo "3. Check for columns showing:"
echo "   • Interface (LAN/WLAN or Ethernet/WiFi)"
echo "   • Connection Type"
echo "   • Port Number (for switches)"
echo
echo -e "${GREEN}Identifying Ethernet devices:${NC}"
echo "• LAN or Ethernet = Wired connection"
echo "• WLAN or WiFi/Wireless = Wireless connection"
echo "• Port 1-4 = Physical Ethernet ports"
echo
echo -e "${YELLOW}If login fails:${NC}"
echo "1. Check the router's physical label for credentials"
echo "2. Try these common combinations:"
echo "   • admin / admin"
echo "   • admin / password"
echo "   • admin / (blank)"
echo "   • root / admin"
echo "3. Look for a password on the router's sticker"
echo
echo -e "${BLUE}================================================${NC}"