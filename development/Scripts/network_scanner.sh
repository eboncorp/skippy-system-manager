#!/bin/bash
# Network Scanner - Find all devices on your local network
# Uses multiple methods for comprehensive discovery

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   Network Device Scanner${NC}"
echo -e "${BLUE}================================================${NC}"
echo

# Get network information
get_network_info() {
    echo -e "${CYAN}Network Configuration:${NC}"
    
    # Get primary network interface and subnet
    PRIMARY_IP=$(ip -4 route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' || hostname -I 2>/dev/null | awk '{print $1}')
    INTERFACE=$(ip -4 route get 1.1.1.1 2>/dev/null | grep -oP 'dev \K\S+' || echo "unknown")
    
    # Calculate subnet
    if [ -n "$PRIMARY_IP" ]; then
        SUBNET=$(echo $PRIMARY_IP | cut -d. -f1-3)
        SUBNET_CIDR="${SUBNET}.0/24"
        
        echo "  Primary IP: $PRIMARY_IP"
        echo "  Interface: $INTERFACE"
        echo "  Subnet: $SUBNET_CIDR"
        
        # Get gateway
        GATEWAY=$(ip route | grep default | awk '{print $3}' | head -1)
        echo "  Gateway: ${GATEWAY:-Unknown}"
    else
        echo -e "${RED}Could not determine network configuration${NC}"
        exit 1
    fi
    echo
}

# Method 1: ARP table scan
scan_arp_table() {
    echo -e "${CYAN}Method 1: ARP Table (recently connected devices)${NC}"
    
    # Show current ARP table
    if command -v arp &> /dev/null; then
        echo -e "${GREEN}Devices in ARP cache:${NC}"
        arp -n | grep -v incomplete | tail -n +2 | while read line; do
            IP=$(echo $line | awk '{print $1}')
            MAC=$(echo $line | awk '{print $3}')
            IFACE=$(echo $line | awk '{print $5}')
            
            # Try to resolve hostname
            HOSTNAME=$(timeout 1 getent hosts $IP 2>/dev/null | awk '{print $2}' || echo "")
            
            printf "  %-15s  %-17s  %-10s  %s\n" "$IP" "$MAC" "$IFACE" "$HOSTNAME"
        done
    else
        echo -e "${YELLOW}arp command not available${NC}"
    fi
    echo
}

# Method 2: Ping sweep
ping_sweep() {
    echo -e "${CYAN}Method 2: Ping Sweep (active discovery)${NC}"
    echo "Pinging subnet $SUBNET_CIDR (this may take a moment)..."
    
    # Create a function to ping in parallel
    ping_host() {
        local ip=$1
        if ping -c 1 -W 1 $ip &>/dev/null; then
            MAC=$(arp -n $ip 2>/dev/null | tail -1 | awk '{print $3}')
            if [ "$MAC" != "no" ] && [ -n "$MAC" ]; then
                HOSTNAME=$(timeout 1 getent hosts $ip 2>/dev/null | awk '{print $2}' || echo "")
                printf "  ${GREEN}✓${NC} %-15s  %-17s  %s\n" "$ip" "$MAC" "$HOSTNAME"
            fi
        fi
    }
    
    # Export function for parallel execution
    export -f ping_host
    export GREEN NC
    
    # Ping all hosts in parallel
    for i in {1..254}; do
        echo -ne "\r  Scanning: $i/254"
        ping_host "$SUBNET.$i" &
        
        # Limit parallel processes
        if [ $(jobs -r | wc -l) -ge 50 ]; then
            wait -n
        fi
    done
    
    # Wait for all background jobs
    wait
    echo -e "\r  Scan complete!        "
    echo
}

# Method 3: nmap scan (if available)
nmap_scan() {
    if command -v nmap &> /dev/null; then
        echo -e "${CYAN}Method 3: Nmap Scan (comprehensive)${NC}"
        echo "Running nmap scan on $SUBNET_CIDR..."
        
        # Try to run nmap (might need sudo for some features)
        if [ "$EUID" -eq 0 ]; then
            # Running as root - can do OS detection
            nmap -sn -O $SUBNET_CIDR 2>/dev/null | grep -E "Nmap scan report|MAC Address|Running:" | sed 's/^/  /'
        else
            # Running as regular user
            nmap -sn $SUBNET_CIDR 2>/dev/null | grep -E "Nmap scan report|MAC Address" | sed 's/^/  /'
            echo -e "\n  ${YELLOW}Note: Run with sudo for OS detection${NC}"
        fi
    else
        echo -e "${CYAN}Method 3: Nmap Scan${NC}"
        echo -e "${YELLOW}nmap not installed. Install with: sudo apt install nmap${NC}"
    fi
    echo
}

# Method 4: arp-scan (if available)
arp_scan() {
    if command -v arp-scan &> /dev/null; then
        echo -e "${CYAN}Method 4: ARP-Scan (layer 2 discovery)${NC}"
        
        if [ "$EUID" -eq 0 ]; then
            arp-scan --local --interface=$INTERFACE 2>/dev/null | grep -E "^[0-9]" | while read line; do
                IP=$(echo $line | awk '{print $1}')
                MAC=$(echo $line | awk '{print $2}')
                VENDOR=$(echo $line | cut -d' ' -f3-)
                printf "  %-15s  %-17s  %s\n" "$IP" "$MAC" "$VENDOR"
            done
        else
            echo -e "${YELLOW}arp-scan requires sudo. Run: sudo arp-scan --local${NC}"
        fi
    else
        echo -e "${CYAN}Method 4: ARP-Scan${NC}"
        echo -e "${YELLOW}arp-scan not installed. Install with: sudo apt install arp-scan${NC}"
    fi
    echo
}

# Method 5: Avahi/mDNS discovery
mdns_scan() {
    echo -e "${CYAN}Method 5: mDNS/Avahi Discovery${NC}"
    
    if command -v avahi-browse &> /dev/null; then
        echo "Discovering mDNS services (5 second scan)..."
        timeout 5 avahi-browse -art 2>/dev/null | grep -E "hostname|address|port" | grep -v ":" | sort -u | sed 's/^/  /' || true
    else
        echo -e "${YELLOW}avahi-browse not installed. Install with: sudo apt install avahi-utils${NC}"
    fi
    echo
}

# Method 6: NetBIOS scan (Windows machines)
netbios_scan() {
    echo -e "${CYAN}Method 6: NetBIOS Discovery (Windows/Samba)${NC}"
    
    if command -v nbtscan &> /dev/null; then
        nbtscan -r $SUBNET_CIDR 2>/dev/null | grep -v "^Doing" | sed 's/^/  /'
    elif command -v nmblookup &> /dev/null; then
        echo "Scanning for NetBIOS names..."
        for i in {1..254}; do
            nmblookup -A "$SUBNET.$i" 2>/dev/null | grep -E "<00>|<20>" | head -1 | sed "s/^/  $SUBNET.$i: /"
        done
    else
        echo -e "${YELLOW}nbtscan not installed. Install with: sudo apt install nbtscan${NC}"
    fi
    echo
}

# Summary function
show_summary() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${GREEN}Scan Complete!${NC}"
    echo
    echo -e "${CYAN}To get more detailed information:${NC}"
    echo "1. Install additional tools:"
    echo "   sudo apt install nmap arp-scan nbtscan avahi-utils"
    echo
    echo "2. Run with sudo for better results:"
    echo "   sudo $0"
    echo
    echo "3. Check specific device:"
    echo "   nmap -A <IP-address>    # Detailed scan"
    echo "   arp -a <IP-address>     # MAC address"
    echo
    echo -e "${CYAN}Common device types by MAC prefix:${NC}"
    echo "  • Raspberry Pi: B8:27:EB, DC:A6:32, E4:5F:01"
    echo "  • Apple: Various starting with 00:03:93, 00:05:02, etc."
    echo "  • Samsung: Various starting with 00:00:F0, 00:02:78, etc."
    echo -e "${BLUE}================================================${NC}"
}

# Main execution
main() {
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then 
        echo -e "${YELLOW}Running as root - full scan capabilities${NC}\n"
    else
        echo -e "${YELLOW}Running as user - some features may be limited${NC}\n"
    fi
    
    # Get network information
    get_network_info
    
    # Run all scan methods
    scan_arp_table
    ping_sweep
    nmap_scan
    arp_scan
    mdns_scan
    netbios_scan
    
    # Show summary
    show_summary
}

# Run main function
main "$@"