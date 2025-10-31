#!/bin/bash
# Find devices connected via Ethernet on the network
# This requires checking at the router/switch level

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   Ethernet Device Discovery${NC}"
echo -e "${BLUE}================================================${NC}"
echo

# Method 1: Check router web interfaces
check_router_interfaces() {
    echo -e "${CYAN}Method 1: Router Web Interfaces${NC}"
    echo "Your network has multiple routers/access points:"
    echo "  • 10.0.0.1 - Main gateway"
    echo "  • 10.0.0.4 - Gigaset device (HTTP/HTTPS available)"
    echo "  • 10.0.0.5 - Gigaset device (HTTP/HTTPS available)"
    echo
    echo "Try accessing these web interfaces to view connected devices:"
    echo "  http://10.0.0.1"
    echo "  http://10.0.0.4"
    echo "  http://10.0.0.5"
    echo
}

# Method 2: MAC address analysis
analyze_mac_addresses() {
    echo -e "${CYAN}Method 2: MAC Address Analysis${NC}"
    echo "Checking MAC addresses for patterns..."
    echo
    
    # Get all active devices
    ip neigh show | grep -E "REACHABLE|STALE" | grep -v fe80 | while read line; do
        IP=$(echo $line | awk '{print $1}')
        MAC=$(echo $line | awk '{print $5}')
        IFACE=$(echo $line | awk '{print $3}')
        
        # Skip if no MAC
        if [ "$MAC" = "lladdr" ] || [ -z "$MAC" ]; then
            continue
        fi
        
        # Analyze connection type by various factors
        CONNECTION="Unknown"
        
        # Check if it's a router/switch (multiple Gigaset devices suggest wired backbone)
        case $MAC in
            bc:a5:11:*)
                CONNECTION="Likely Ethernet (Router/AP)"
                ;;
            00:80:92:*)
                CONNECTION="Likely Ethernet (Network Device)"
                ;;
            *)
                # For other devices, we can't be certain without router info
                CONNECTION="Unknown (check router)"
                ;;
        esac
        
        printf "%-15s %-17s %s\n" "$IP" "$MAC" "$CONNECTION"
    done
    echo
}

# Method 3: Port scan for typical wired devices
scan_for_wired_services() {
    echo -e "${CYAN}Method 3: Scanning for Typical Wired Services${NC}"
    echo "Devices with these services are often connected via Ethernet:"
    echo
    
    # Services typically on wired connections
    declare -A wired_services=(
        ["445"]="SMB/File Server"
        ["3389"]="Windows Remote Desktop"
        ["5900"]="VNC Server"
        ["9100"]="Printer"
        ["80"]="Web Server (possible)"
        ["443"]="Secure Web (possible)"
        ["22"]="SSH (possible)"
    )
    
    SUBNET=$(ip -4 route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' | cut -d. -f1-3)
    
    echo "Scanning for services (this may take a moment)..."
    
    for ip in $(seq 1 254); do
        TARGET="$SUBNET.$ip"
        
        # Quick ping check first
        if ping -c 1 -W 0.5 "$TARGET" &>/dev/null; then
            for port in "${!wired_services[@]}"; do
                if timeout 0.5 bash -c "echo >/dev/tcp/$TARGET/$port" 2>/dev/null; then
                    echo -e "${GREEN}✓${NC} $TARGET - Port $port open (${wired_services[$port]})"
                fi
            done
        fi
    done
    echo
}

# Method 4: SNMP query (if available)
check_snmp() {
    echo -e "${CYAN}Method 4: SNMP Query${NC}"
    
    if command -v snmpwalk &> /dev/null; then
        echo "Attempting SNMP query on router..."
        # Try common community strings
        for community in public private; do
            echo "Trying community: $community"
            snmpwalk -v 2c -c $community 10.0.0.1 1.3.6.1.2.1.4.22.1.2 2>/dev/null | grep -E "INTEGER: [0-9]+" | head -5
        done
    else
        echo -e "${YELLOW}snmpwalk not installed. Install with: sudo apt install snmp${NC}"
    fi
    echo
}

# Method 5: Check for Ethernet-specific characteristics
check_ethernet_characteristics() {
    echo -e "${CYAN}Method 5: Ethernet Device Characteristics${NC}"
    echo "Analyzing network for Ethernet-typical patterns..."
    echo
    
    # Look for devices responding very quickly (low latency = possibly wired)
    echo "Testing latency (wired devices typically < 1ms):"
    
    ip neigh show | grep -E "REACHABLE|STALE" | grep -v fe80 | awk '{print $1}' | while read IP; do
        # Run 3 pings and get average time
        AVG_TIME=$(ping -c 3 -W 1 -i 0.2 "$IP" 2>/dev/null | grep "rtt" | cut -d'/' -f5)
        
        if [ -n "$AVG_TIME" ]; then
            # Remove 'ms' and convert to float for comparison
            TIME_VAL=$(echo "$AVG_TIME" | sed 's/[^0-9.]//g')
            
            if (( $(echo "$TIME_VAL < 2.0" | bc -l 2>/dev/null || echo 0) )); then
                echo -e "  ${GREEN}$IP${NC} - ${TIME_VAL}ms (possibly wired)"
            else
                echo -e "  $IP - ${TIME_VAL}ms"
            fi
        fi
    done
    echo
}

# Main execution
main() {
    check_router_interfaces
    analyze_mac_addresses
    scan_for_wired_services
    check_snmp
    check_ethernet_characteristics
    
    echo -e "${BLUE}================================================${NC}"
    echo -e "${GREEN}Recommendations:${NC}"
    echo "1. Access your router's web interface for definitive answers:"
    echo "   - Look for 'Connected Devices' or 'DHCP Clients' section"
    echo "   - Check for 'Connection Type' or 'Interface' column"
    echo
    echo "2. Devices likely to be on Ethernet:"
    echo "   - Routers/Access Points (10.0.0.1, 10.0.0.4, 10.0.0.5)"
    echo "   - Network devices (10.0.0.16 - Silex Technology)"
    echo "   - Any device with consistent <1ms ping times"
    echo "   - Devices running server services (SMB, RDP, etc.)"
    echo
    echo "3. For definitive identification, you need:"
    echo "   - Router admin access"
    echo "   - Managed switch with web interface"
    echo "   - Physical inspection of network cables"
    echo -e "${BLUE}================================================${NC}"
}

# Run main
main "$@"