#!/bin/bash

# Epson Perfection V39 Scanner Installation and Network Setup Script
# This script installs and configures the Epson V39 scanner for both local and network access

set -e

# Configuration
SCANNER_NAME="Epson Perfection V39"
SCANNER_MODEL="V39"
NETWORK_NAME="epson-v39-scanner"
SANED_PORT=6566

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="/tmp/epson_v39_install_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages
log_message() {
    echo -e "$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Function to check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_message "${RED}This script must be run as root or with sudo${NC}"
        exit 1
    fi
}

# Function to print banner
print_banner() {
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║        Epson Perfection V39 Scanner Installation         ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo -e "${GREEN}Installing:${NC} $SCANNER_NAME"
    echo -e "${GREEN}Network Name:${NC} $NETWORK_NAME"
    echo -e "${GREEN}Port:${NC} $SANED_PORT"
    echo -e "${GREEN}Log File:${NC} $LOG_FILE"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
}

# Function to install base SANE packages
install_sane_base() {
    log_message "${CYAN}Installing SANE base packages...${NC}"

    apt-get update
    apt-get install -y \
        sane \
        sane-utils \
        libsane1 \
        libsane-common \
        xsane \
        simple-scan \
        imagemagick \
        tesseract-ocr \
        poppler-utils

    log_message "${GREEN}✓ SANE base packages installed${NC}"
}

# Function to download and install Epson drivers
install_epson_drivers() {
    log_message "${CYAN}Downloading and installing Epson drivers...${NC}"

    # Create temporary directory for downloads
    TEMP_DIR="/tmp/epson_driver_install"
    mkdir -p "$TEMP_DIR"
    cd "$TEMP_DIR"

    # Download Image Scan! for Linux (iscan) - supports V39
    # Note: URLs may change, these are typical locations
    ISCAN_BASE_URL="http://support.epson.net/linux/src/scanner/iscan"

    # Install dependencies
    apt-get install -y \
        libltdl7 \
        libusb-1.0-0 \
        libgimp2.0 \
        libjpeg-turbo8 \
        libpng16-16t64 \
        libtiff6 \
        libxml2 \
        libgtk2.0-0t64

    # Download and install iscan packages
    # For Ubuntu 22.04/24.04 (64-bit)
    log_message "${CYAN}Downloading iscan packages...${NC}"

    # Option 1: Try to download from Epson directly
    wget -q "http://download.ebz.epson.net/dsc/du/02/DriverDownloadInfo.do?LG2=EN&CN2=&DSCMI=155617&DSCCHK=e0b84f0e82c4f2cf93e2c0b5e2501e8c1154e48d" -O epson_download.html 2>/dev/null || true

    # Option 2: Use alternative sources or manual download instructions
    if [ ! -f "iscan_2.30.4-2_amd64.deb" ]; then
        log_message "${YELLOW}Attempting alternative download method...${NC}"

        # Try direct links
        wget -q "http://support.epson.net/linux/src/scanner/iscan/iscan_2.30.4-2_amd64.deb" 2>/dev/null || \
        wget -q "https://download2.ebz.epson.net/iscan/general/deb/x64/iscan_2.30.4-2_amd64.deb" 2>/dev/null || true
    fi

    # Install imagescan (alternative scanner software)
    log_message "${CYAN}Installing imagescan (alternative)...${NC}"
    apt-get install -y imagescan || true

    # Install epsonscan2 if available
    add-apt-repository ppa:sane-project/sane-release -y 2>/dev/null || true
    apt-get update
    apt-get install -y epsonscan2 2>/dev/null || true

    # Install downloaded packages if they exist
    if ls *.deb 1> /dev/null 2>&1; then
        log_message "${CYAN}Installing downloaded Epson packages...${NC}"
        dpkg -i *.deb 2>/dev/null || apt-get -f install -y
    fi

    # Clean up
    cd /
    rm -rf "$TEMP_DIR"

    log_message "${GREEN}✓ Epson drivers installation completed${NC}"
}

# Function to configure SANE for Epson V39
configure_sane_epson() {
    log_message "${CYAN}Configuring SANE for Epson V39...${NC}"

    # Backup original configuration
    cp /etc/sane.d/epson2.conf /etc/sane.d/epson2.conf.backup.$(date +%Y%m%d) 2>/dev/null || true
    cp /etc/sane.d/epson.conf /etc/sane.d/epson.conf.backup.$(date +%Y%m%d) 2>/dev/null || true

    # Configure epson2 backend (recommended for V39)
    cat > /etc/sane.d/epson2.conf << 'EOF'
# Epson backend configuration file for Perfection V39

# USB scanner
usb

# Network scanner (if shared from another host)
# net autodiscovery

# Specific USB ID for Epson V39 (if needed)
# usb 0x04b8 0x013d
# Epson V39II
usb 0x04b8 0x013f

# Enable all available options
option no_focus
option enable_infrared
EOF

    # Enable epson and epson2 backends
    if ! grep -q "^epson2" /etc/sane.d/dll.conf; then
        echo "epson2" >> /etc/sane.d/dll.conf
    fi
    if ! grep -q "^epson" /etc/sane.d/dll.conf; then
        echo "epson" >> /etc/sane.d/dll.conf
    fi

    # Add USB permissions for scanner
    cat > /etc/udev/rules.d/99-epson-scanner.rules << 'EOF'
# Epson Perfection V39
ATTRS{idVendor}=="04b8", ATTRS{idProduct}=="013d", MODE="0666", GROUP="scanner", ENV{libsane_matched}="yes"
# Epson Perfection V39II
ATTRS{idVendor}=="04b8", ATTRS{idProduct}=="013f", MODE="0666", GROUP="scanner", ENV{libsane_matched}="yes"
# General Epson scanners
ATTRS{idVendor}=="04b8", MODE="0666", GROUP="scanner", ENV{libsane_matched}="yes"
EOF

    # Reload udev rules
    udevadm control --reload-rules
    udevadm trigger

    log_message "${GREEN}✓ SANE configuration completed${NC}"
}

# Function to configure network sharing
configure_network_sharing() {
    log_message "${CYAN}Configuring network scanner sharing...${NC}"

    # Install saned (SANE network daemon)
    apt-get install -y sane-utils xinetd

    # Configure saned
    # 1. Set up saned user
    if ! id -u saned > /dev/null 2>&1; then
        useradd -r -s /bin/false -d /var/lib/saned saned
    fi

    # Add saned to scanner group
    usermod -a -G scanner saned
    usermod -a -G lp saned

    # 2. Configure allowed hosts
    cat > /etc/sane.d/saned.conf << 'EOF'
# saned.conf -- configuration for saned network scanner daemon

# Allow access from local network
localhost
127.0.0.1
::1
10.0.0.0/8
192.168.0.0/16
172.16.0.0/12

# Specific allowed hosts (add your network IPs here)
# 192.168.1.0/24
EOF

    # 3. Configure xinetd for saned
    cat > /etc/xinetd.d/sane-port << EOF
service sane-port
{
    socket_type = stream
    server = /usr/sbin/saned
    protocol = tcp
    user = saned
    group = scanner
    wait = no
    disable = no
    port = $SANED_PORT
}
EOF

    # 4. Enable saned in /etc/default/saned
    sed -i 's/^RUN=no/RUN=yes/' /etc/default/saned 2>/dev/null || \
    echo "RUN=yes" > /etc/default/saned

    # 5. Configure systemd service
    cat > /etc/systemd/system/saned.service << 'EOF'
[Unit]
Description=SANE network scanner daemon
After=network.target

[Service]
Type=simple
User=saned
Group=scanner
ExecStart=/usr/sbin/saned -a
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    # 6. Configure saned socket
    cat > /etc/systemd/system/saned.socket << EOF
[Unit]
Description=SANE network scanner daemon socket

[Socket]
ListenStream=$SANED_PORT
Accept=yes
MaxConnections=1

[Install]
WantedBy=sockets.target
EOF

    # Reload systemd and enable services
    systemctl daemon-reload
    systemctl enable saned.socket
    systemctl enable saned.service

    # Configure firewall if UFW is active
    if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
        log_message "${CYAN}Configuring firewall rules...${NC}"
        ufw allow $SANED_PORT/tcp comment 'SANE network scanner'
    fi

    log_message "${GREEN}✓ Network sharing configuration completed${NC}"
}

# Function to create scanner utilities
create_scanner_utilities() {
    log_message "${CYAN}Creating scanner utility scripts...${NC}"

    # Create test scanner script
    cat > /usr/local/bin/test-epson-scanner << 'EOF'
#!/bin/bash

echo "Testing Epson V39 Scanner..."
echo "=========================="
echo

echo "1. Checking USB connection:"
lsusb | grep -i epson || echo "   No Epson device found on USB"
echo

echo "2. Checking SANE detection:"
scanimage -L
echo

echo "3. Available scanner backends:"
scanimage --list-devices
echo

echo "4. Testing scan (press Ctrl+C to cancel):"
echo "   Place a document on the scanner and press Enter to test scan..."
read -r
scanimage --device-name=auto --format=png --output-file=/tmp/test_scan.png --progress
if [ -f /tmp/test_scan.png ]; then
    echo "   Test scan successful! File saved to /tmp/test_scan.png"
    ls -lh /tmp/test_scan.png
else
    echo "   Test scan failed."
fi
EOF
    chmod +x /usr/local/bin/test-epson-scanner

    # Create network scanner client setup script
    cat > /usr/local/bin/setup-network-scanner-client << 'EOF'
#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <scanner-server-ip>"
    echo "Example: $0 192.168.1.100"
    exit 1
fi

SERVER_IP=$1

echo "Setting up network scanner client for server: $SERVER_IP"

# Add server to net.conf
if ! grep -q "$SERVER_IP" /etc/sane.d/net.conf; then
    echo "$SERVER_IP" >> /etc/sane.d/net.conf
    echo "Added $SERVER_IP to /etc/sane.d/net.conf"
fi

# Enable net backend
if ! grep -q "^net" /etc/sane.d/dll.conf; then
    echo "net" >> /etc/sane.d/dll.conf
    echo "Enabled net backend"
fi

echo "Testing network scanner connection..."
scanimage -L

echo "Network scanner client setup complete!"
EOF
    chmod +x /usr/local/bin/setup-network-scanner-client

    # Create simple scan script
    cat > /usr/local/bin/epson-scan << 'EOF'
#!/bin/bash

# Simple scanning script for Epson V39

OUTPUT_DIR="${HOME}/ScannedDocuments"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="${OUTPUT_DIR}/scan_${TIMESTAMP}"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Parse arguments
RESOLUTION=${1:-300}
FORMAT=${2:-pdf}
MODE=${3:-Color}

echo "Scanning with Epson V39..."
echo "Resolution: $RESOLUTION DPI"
echo "Format: $FORMAT"
echo "Mode: $MODE"
echo "Output: ${OUTPUT_FILE}.${FORMAT}"

# Perform scan
if [ "$FORMAT" = "pdf" ]; then
    scanimage --resolution "$RESOLUTION" --mode "$MODE" --format=png | \
    convert - "${OUTPUT_FILE}.pdf"
else
    scanimage --resolution "$RESOLUTION" --mode "$MODE" \
    --format="$FORMAT" > "${OUTPUT_FILE}.${FORMAT}"
fi

if [ $? -eq 0 ]; then
    echo "Scan completed successfully!"
    echo "File saved to: ${OUTPUT_FILE}.${FORMAT}"
    ls -lh "${OUTPUT_FILE}.${FORMAT}"
else
    echo "Scan failed!"
    exit 1
fi
EOF
    chmod +x /usr/local/bin/epson-scan

    log_message "${GREEN}✓ Scanner utilities created${NC}"
}

# Function to start services
start_services() {
    log_message "${CYAN}Starting scanner services...${NC}"

    # Restart udev
    systemctl restart udev

    # Start saned services
    systemctl restart xinetd 2>/dev/null || true
    systemctl start saned.socket
    systemctl start saned.service

    # Check service status
    if systemctl is-active --quiet saned.socket; then
        log_message "${GREEN}✓ saned.socket is running${NC}"
    else
        log_message "${YELLOW}⚠ saned.socket is not running${NC}"
    fi

    if systemctl is-active --quiet saned.service; then
        log_message "${GREEN}✓ saned.service is running${NC}"
    else
        log_message "${YELLOW}⚠ saned.service is not running${NC}"
    fi
}

# Function to display post-installation instructions
display_instructions() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Installation Complete!${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

    echo -e "${CYAN}Next Steps:${NC}"
    echo -e "1. ${YELLOW}Connect your Epson V39 scanner via USB${NC}"
    echo -e "2. ${YELLOW}Test the scanner:${NC}"
    echo -e "   ${GREEN}sudo test-epson-scanner${NC}"
    echo
    echo -e "3. ${YELLOW}For network access from other computers:${NC}"
    echo -e "   On client machines, run:"
    echo -e "   ${GREEN}sudo setup-network-scanner-client $(hostname -I | awk '{print $1}')${NC}"
    echo
    echo -e "${CYAN}Available Commands:${NC}"
    echo -e "  ${GREEN}test-epson-scanner${NC} - Test scanner connection"
    echo -e "  ${GREEN}epson-scan [resolution] [format] [mode]${NC} - Quick scan"
    echo -e "  ${GREEN}scanimage -L${NC} - List available scanners"
    echo -e "  ${GREEN}simple-scan${NC} - GUI scanning application"
    echo -e "  ${GREEN}xsane${NC} - Advanced GUI scanning application"
    echo
    echo -e "${CYAN}Network Scanner Port:${NC} $SANED_PORT"
    echo -e "${CYAN}Log File:${NC} $LOG_FILE"
    echo
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
}

# Main installation flow
main() {
    check_root
    print_banner

    log_message "${CYAN}Starting installation...${NC}"

    install_sane_base
    install_epson_drivers
    configure_sane_epson
    configure_network_sharing
    create_scanner_utilities
    start_services

    display_instructions

    log_message "${GREEN}Installation completed successfully!${NC}"
}

# Run main function
main "$@"