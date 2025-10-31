#!/bin/bash
# Server Network Information and Discovery Helper
# Shows all network information for the home server

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   Home Server Network Information${NC}"
echo -e "${BLUE}================================================${NC}"
echo

# Function to get all IP addresses
get_ip_addresses() {
    echo -e "${CYAN}Local IP Addresses:${NC}"
    
    # Method 1: Using ip command (most reliable)
    if command -v ip &> /dev/null; then
        echo -e "${GREEN}Primary IP addresses:${NC}"
        ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v '127.0.0.1' | while read ip; do
            interface=$(ip -4 addr show | grep -B2 "$ip" | head -1 | cut -d: -f2 | tr -d ' ')
            echo "  $ip (interface: $interface)"
        done
    fi
    
    # Method 2: Using hostname command
    if command -v hostname &> /dev/null; then
        echo -e "\n${GREEN}Hostname resolution:${NC}"
        echo "  Hostname: $(hostname)"
        echo "  FQDN: $(hostname -f 2>/dev/null || echo 'Not configured')"
        hostname -I &>/dev/null && echo "  All IPs: $(hostname -I)"
    fi
    
    # Method 3: Using ifconfig (if available)
    if command -v ifconfig &> /dev/null; then
        echo -e "\n${GREEN}Network interfaces (ifconfig):${NC}"
        ifconfig | grep -E "inet |UP" | grep -v "127.0.0.1" | sed 's/^/  /'
    fi
}

# Function to show services and ports
show_services() {
    echo -e "\n${CYAN}Active Services and Ports:${NC}"
    
    # Check if home server is running
    if pgrep -f "home_server_master.py" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Home Server Master is running${NC}"
        
        # Try to get port from config
        CONFIG_FILE="$HOME/.home-server/config/server.yaml"
        if [ -f "$CONFIG_FILE" ]; then
            PORT=$(grep "server_port:" "$CONFIG_FILE" 2>/dev/null | awk '{print $2}' || echo "8080")
            echo "  Web UI Port: $PORT"
        else
            echo "  Web UI Port: 8080 (default)"
            PORT=8080
        fi
    else
        echo -e "${YELLOW}⚠ Home Server Master is not running${NC}"
        PORT=8080
    fi
    
    # Show listening ports
    echo -e "\n${GREEN}Listening ports:${NC}"
    if command -v ss &> /dev/null; then
        ss -tlnp 2>/dev/null | grep LISTEN | grep -v "127.0.0.1" | awk '{print "  Port " $4}' | sort -u
    elif command -v netstat &> /dev/null; then
        netstat -tlnp 2>/dev/null | grep LISTEN | grep -v "127.0.0.1" | awk '{print "  Port " $4}' | sort -u
    fi
}

# Function to show access URLs
show_access_urls() {
    echo -e "\n${CYAN}Access URLs:${NC}"
    
    # Get primary IP
    PRIMARY_IP=$(ip -4 route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' || hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")
    
    # Get port from config or use default
    CONFIG_FILE="$HOME/.home-server/config/server.yaml"
    if [ -f "$CONFIG_FILE" ]; then
        PORT=$(grep "server_port:" "$CONFIG_FILE" 2>/dev/null | awk '{print $2}' || echo "8080")
    else
        PORT=8080
    fi
    
    echo -e "${GREEN}Web Interface:${NC}"
    echo "  Local: http://localhost:$PORT"
    echo "  Network: http://$PRIMARY_IP:$PORT"
    echo "  Hostname: http://$(hostname):$PORT"
    
    # Show all possible access URLs
    echo -e "\n${GREEN}All possible access URLs:${NC}"
    ip -4 addr show 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v '127.0.0.1' | while read ip; do
        echo "  http://$ip:$PORT"
    done
}

# Function to show discovery methods
show_discovery_methods() {
    echo -e "\n${CYAN}How to find this server from other devices:${NC}"
    
    echo -e "\n${GREEN}1. By hostname:${NC}"
    echo "   ping $(hostname).local"
    echo "   or browse to: http://$(hostname).local:$PORT"
    
    echo -e "\n${GREEN}2. By IP scanning (from another Linux machine):${NC}"
    PRIMARY_IP=$(ip -4 route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' || hostname -I 2>/dev/null | awk '{print $1}')
    SUBNET=$(echo $PRIMARY_IP | cut -d. -f1-3)
    echo "   nmap -sn $SUBNET.0/24"
    echo "   or"
    echo "   arp-scan --local"
    
    echo -e "\n${GREEN}3. From Windows:${NC}"
    echo "   arp -a"
    echo "   or"
    echo "   ping $(hostname)"
    
    echo -e "\n${GREEN}4. Using avahi/mDNS (if installed):${NC}"
    if command -v avahi-browse &> /dev/null; then
        echo "   avahi-browse -art | grep $(hostname)"
        echo -e "${GREEN}   ✓ Avahi is installed${NC}"
    else
        echo "   sudo apt install avahi-daemon avahi-utils"
        echo -e "${YELLOW}   ⚠ Avahi not installed${NC}"
    fi
}

# Function to create a beacon service
create_beacon() {
    echo -e "\n${CYAN}Network Beacon Setup:${NC}"
    
    BEACON_SCRIPT="$HOME/.home-server/network_beacon.py"
    
    cat > "$BEACON_SCRIPT" << 'EOF'
#!/usr/bin/env python3
"""Network beacon for home server discovery"""
import socket
import time
import json
import threading

def broadcast_presence():
    """Broadcast server presence on the network"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    hostname = socket.gethostname()
    
    # Get all IPs
    ips = []
    try:
        for info in socket.getaddrinfo(hostname, None):
            ip = info[4][0]
            if ip not in ips and not ip.startswith('127.'):
                ips.append(ip)
    except:
        pass
    
    message = json.dumps({
        'service': 'home-server-master',
        'hostname': hostname,
        'ips': ips,
        'port': 8080,
        'version': '1.0.0'
    })
    
    while True:
        try:
            sock.sendto(message.encode(), ('<broadcast>', 50000))
        except:
            pass
        time.sleep(30)  # Broadcast every 30 seconds

def listen_for_discovery():
    """Listen for discovery requests"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 50001))
    
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if data == b'DISCOVER_HOME_SERVER':
                response = json.dumps({
                    'service': 'home-server-master',
                    'hostname': socket.gethostname(),
                    'port': 8080
                })
                sock.sendto(response.encode(), addr)
        except:
            pass

if __name__ == '__main__':
    print("Starting network beacon...")
    t1 = threading.Thread(target=broadcast_presence, daemon=True)
    t2 = threading.Thread(target=listen_for_discovery, daemon=True)
    t1.start()
    t2.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nBeacon stopped")
EOF
    
    chmod +x "$BEACON_SCRIPT"
    echo -e "${GREEN}Network beacon created at: $BEACON_SCRIPT${NC}"
    echo "Run it with: python3 $BEACON_SCRIPT"
}

# Function to create discovery client
create_discovery_client() {
    echo -e "\n${CYAN}Creating discovery client:${NC}"
    
    CLIENT_SCRIPT="$HOME/.home-server/find_server.py"
    
    cat > "$CLIENT_SCRIPT" << 'EOF'
#!/usr/bin/env python3
"""Find home server on the network"""
import socket
import json
import time

def find_server():
    """Discover home server on the network"""
    print("Searching for home server on the network...")
    
    # Method 1: Listen for broadcasts
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', 50000))
    sock.settimeout(5)
    
    servers = {}
    start_time = time.time()
    
    while time.time() - start_time < 10:
        try:
            data, addr = sock.recvfrom(1024)
            info = json.loads(data.decode())
            if info.get('service') == 'home-server-master':
                servers[addr[0]] = info
                print(f"Found server at {addr[0]}: {info['hostname']}")
        except socket.timeout:
            continue
        except:
            pass
    
    # Method 2: Active discovery
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock2.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock2.settimeout(2)
    
    sock2.sendto(b'DISCOVER_HOME_SERVER', ('<broadcast>', 50001))
    
    try:
        data, addr = sock2.recvfrom(1024)
        info = json.loads(data.decode())
        if info.get('service') == 'home-server-master':
            servers[addr[0]] = info
            print(f"Found server at {addr[0]}: {info['hostname']}")
    except:
        pass
    
    if servers:
        print("\nHome servers found:")
        for ip, info in servers.items():
            print(f"  • {info['hostname']} at {ip}:{info.get('port', 8080)}")
            print(f"    Access URL: http://{ip}:{info.get('port', 8080)}")
    else:
        print("No home servers found on the network")

if __name__ == '__main__':
    find_server()
EOF
    
    chmod +x "$CLIENT_SCRIPT"
    echo -e "${GREEN}Discovery client created at: $CLIENT_SCRIPT${NC}"
    echo "Run from any machine on the network: python3 $CLIENT_SCRIPT"
}

# Main execution
echo -e "${YELLOW}System Information:${NC}"
echo "  Hostname: $(hostname)"
echo "  User: $USER"
echo "  OS: $(uname -s) $(uname -r)"

get_ip_addresses
show_services
show_access_urls
show_discovery_methods

# Offer to create helper scripts
echo -e "\n${CYAN}Additional Tools:${NC}"
read -p "Create network beacon for easier discovery? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    create_beacon
    create_discovery_client
fi

echo -e "\n${BLUE}================================================${NC}"
echo -e "${GREEN}Summary:${NC}"
PRIMARY_IP=$(ip -4 route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' || hostname -I 2>/dev/null | awk '{print $1}')
echo -e "Your server can be accessed at: ${GREEN}http://$PRIMARY_IP:$PORT${NC}"
echo -e "Or by hostname: ${GREEN}http://$(hostname).local:$PORT${NC}"
echo -e "${BLUE}================================================${NC}"