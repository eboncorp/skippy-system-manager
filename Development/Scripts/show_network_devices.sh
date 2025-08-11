#!/bin/bash
# Show all devices on the network in a formatted view

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   Active Devices on Your Network${NC}"
echo -e "${BLUE}================================================${NC}"
echo

# Get network info
PRIMARY_IP=$(ip -4 route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' || hostname -I 2>/dev/null | awk '{print $1}')
echo -e "${CYAN}Your IP:${NC} $PRIMARY_IP ($(hostname))"
echo -e "${CYAN}Gateway:${NC} $(ip route | grep default | awk '{print $3}' | head -1)"
echo

# Show active devices from ARP/neighbor table
echo -e "${GREEN}Active Devices:${NC}"
echo -e "IP Address      MAC Address         Hostname/Description"
echo -e "--------------- ------------------- ------------------------------------"

# Get neighbor table and format it
ip neigh show | grep REACHABLE | grep -v fe80 | sort -t . -k 4 -n | while read line; do
    IP=$(echo $line | awk '{print $1}')
    MAC=$(echo $line | awk '{print $5}')
    
    # Try to resolve hostname
    HOSTNAME=$(timeout 1 getent hosts $IP 2>/dev/null | awk '{print $2}' || echo "")
    
    # Identify device type by MAC prefix
    MAC_PREFIX=$(echo $MAC | cut -d: -f1-3 | tr '[:lower:]' '[:upper:]')
    VENDOR=""
    
    case $MAC_PREFIX in
        "BC:A5:11") VENDOR="(Gigaset/Router)" ;;
        "94:3A:91") VENDOR="(Device)" ;;
        "BE:22:43") VENDOR="(Device)" ;;
        "64:16:66") VENDOR="(Device)" ;;
        "D6:09:DA") VENDOR="(Device)" ;;
        "2C:CC:44") VENDOR="(Sony)" ;;
        "2A:7B:1E") VENDOR="(Device)" ;;
        "38:1B:9E") VENDOR="(Device)" ;;
        "00:80:92") VENDOR="(Silex Technology)" ;;
        "10:E7:C6") VENDOR="(Apple)" ;;
        *) VENDOR="" ;;
    esac
    
    # Special identification for known IPs
    DESCRIPTION=""
    case $IP in
        "10.0.0.1") DESCRIPTION="Router/Gateway" ;;
        "10.0.0.25") DESCRIPTION="This device ($(hostname))" ;;
        *) DESCRIPTION="$HOSTNAME $VENDOR" ;;
    esac
    
    # Color code based on device type
    if [ "$IP" = "$PRIMARY_IP" ]; then
        echo -e "${CYAN}$IP${NC}  $MAC  ${CYAN}$DESCRIPTION${NC}"
    elif [ "$IP" = "10.0.0.1" ]; then
        echo -e "${YELLOW}$IP${NC}  $MAC  ${YELLOW}$DESCRIPTION${NC}"
    else
        printf "%-15s  %-17s  %s\n" "$IP" "$MAC" "$DESCRIPTION"
    fi
done

echo
echo -e "${CYAN}Device Count:${NC} $(ip neigh show | grep REACHABLE | grep -v fe80 | wc -l) active devices"
echo

# Quick network statistics
echo -e "${CYAN}Network Usage:${NC}"
if command -v ss &> /dev/null; then
    CONNECTIONS=$(ss -tun | tail -n +2 | wc -l)
    echo "  Active connections: $CONNECTIONS"
fi

# Show services running on this machine
echo
echo -e "${CYAN}Services on this machine:${NC}"
if command -v ss &> /dev/null; then
    ss -tlnp 2>/dev/null | grep LISTEN | grep -v "127.0.0.1" | awk '{print "  Port " $4}' | sort -u
else
    netstat -tlnp 2>/dev/null | grep LISTEN | grep -v "127.0.0.1" | awk '{print "  Port " $4}' | sort -u
fi

echo
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}Tips:${NC}"
echo "• To scan for more devices: ping -b ${PRIMARY_IP%.*}.255"
echo "• To get device details: nmap -A <IP-address>"
echo "• For continuous monitoring: watch -n 5 $0"
echo -e "${BLUE}================================================${NC}"