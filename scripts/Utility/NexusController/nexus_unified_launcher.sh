#!/bin/bash
# NexusController Unified Launcher
# Single point of entry for the complete infrastructure management system

# Colors for output
CYAN='\033[0;36m'
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ASCII Art Banner
echo -e "${CYAN}"
cat << "EOF"
 ███▄    █ ▓█████ ▒██   ██▒ █    ██   ██████ 
 ██ ▀█   █ ▓█   ▀ ▒▒ █ █ ▒░ ██  ▓██▒▒██    ▒ 
▓██  ▀█ ██▒▒███   ░░  █   ░▓██  ▒██░░ ▓██▄   
▓██▒  ▐▌██▒▒▓█  ▄  ░ █ █ ▒ ▓▓█  ░██░  ▒   ██▒
▒██░   ▓██░░▒████▒▒██▒ ▒██▒▒▒█████▓ ▒██████▒▒
░ ▒░   ▒ ▒ ░░ ▒░ ░▒▒ ░ ░▓ ░░▒▓▒ ▒ ▒ ▒ ▒▓▒ ▒ ░
░ ░░   ░ ▒░ ░ ░  ░░░   ░▒ ░░░▒░ ░ ░ ░ ░▒  ░ ░
   ░   ░ ░    ░    ░    ░   ░░░ ░ ░ ░  ░  ░  
         ░    ░  ░ ░    ░     ░           ░  
EOF
echo -e "${NC}"
echo -e "${BLUE}NexusController Unified v2.0 - Enterprise Infrastructure Management${NC}"
echo -e "${YELLOW}Integrated: Media Server • Home Automation • Cloud • Security • AI${NC}"
echo

# Check if running from correct directory
if [ ! -f "nexus_unified.py" ]; then
    echo -e "${RED}Error: Please run from NexusController directory${NC}"
    echo "cd ~/Skippy/app-to-deploy/NexusController && ./nexus_unified_launcher.sh"
    exit 1
fi

# Function to check and install dependencies
check_dependencies() {
    echo -e "${CYAN}[NEXUS] Checking system dependencies...${NC}"
    
    # Check Python packages
    python3 -c "import tkinter, paramiko, psutil, requests, cryptography" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}[>] Installing Python dependencies...${NC}"
        pip3 install --user paramiko psutil requests cryptography
    fi
    
    # Check for system tools
    for tool in nmap ssh-keyscan; do
        if ! command -v $tool &> /dev/null; then
            echo -e "${YELLOW}[>] Installing $tool...${NC}"
            sudo apt update && sudo apt install -y $tool
        fi
    done
}

# Function to setup Google Drive integration
setup_google_drive() {
    echo -e "${CYAN}[NEXUS] Setting up Google Drive integration...${NC}"
    
    GDRIVE_PATH="$HOME/GoogleDrive"
    GDRIVE_SCRIPT="$HOME/Skippy/app-to-deploy/gdrive_gui.py"
    
    if [ -f "$GDRIVE_SCRIPT" ]; then
        echo -e "${GREEN}[✓] Google Drive manager found${NC}"
        
        # Create mount point if it doesn't exist
        if [ ! -d "$GDRIVE_PATH" ]; then
            mkdir -p "$GDRIVE_PATH"
            echo -e "${GREEN}[✓] Google Drive mount point created${NC}"
        fi
        
        # Check if Google Drive is mounted
        if [ -z "$(ls -A $GDRIVE_PATH 2>/dev/null)" ]; then
            echo -e "${YELLOW}[!] Google Drive appears to be empty${NC}"
            echo -e "${BLUE}[i] You may need to mount Google Drive manually${NC}"
            echo -e "${BLUE}[i] Use: $GDRIVE_SCRIPT${NC}"
        else
            echo -e "${GREEN}[✓] Google Drive is accessible${NC}"
        fi
    else
        echo -e "${YELLOW}[!] Google Drive manager not found at expected location${NC}"
    fi
}

# Function to check server connectivity
check_servers() {
    echo -e "${CYAN}[NEXUS] Checking server connectivity...${NC}"
    
    # Known ebon servers
    servers=("10.0.0.25" "10.0.0.29")
    
    for server in "${servers[@]}"; do
        if ping -c 1 -W 1 "$server" &> /dev/null; then
            echo -e "${GREEN}[✓] Server $server is reachable${NC}"
            
            # Check for specific services
            if curl -s "http://$server:8096" &> /dev/null; then
                echo -e "${GREEN}  [✓] Jellyfin media server detected${NC}"
            fi
            
            if curl -s "http://$server:8123" &> /dev/null; then
                echo -e "${GREEN}  [✓] Home Assistant detected${NC}"
            fi
        else
            echo -e "${YELLOW}[!] Server $server is not reachable${NC}"
        fi
    done
}

# Function to create desktop shortcut
create_desktop_shortcut() {
    DESKTOP_FILE="$HOME/Desktop/NexusController.desktop"
    LAUNCHER_PATH="$(pwd)/nexus_unified_launcher.sh"
    
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=NexusController Unified
Comment=Enterprise Infrastructure Management System
Exec=$LAUNCHER_PATH
Icon=applications-system
Terminal=false
Categories=System;Network;
EOF
    
    chmod +x "$DESKTOP_FILE"
    echo -e "${GREEN}[✓] Desktop shortcut created${NC}"
}

# Function to setup configuration directory
setup_config() {
    echo -e "${CYAN}[NEXUS] Setting up configuration directory...${NC}"
    
    CONFIG_DIR="$HOME/.nexus"
    mkdir -p "$CONFIG_DIR"
    chmod 700 "$CONFIG_DIR"
    
    # Create default configurations if they don't exist
    if [ ! -f "$CONFIG_DIR/network_config.json" ]; then
        cp "/home/dave/.nexus/network_config.json" "$CONFIG_DIR/" 2>/dev/null || echo '{}' > "$CONFIG_DIR/network_config.json"
    fi
    
    if [ ! -f "$CONFIG_DIR/cloud_providers_config.json" ]; then
        cp "/home/dave/.nexus/cloud_providers_config.json" "$CONFIG_DIR/" 2>/dev/null || echo '{}' > "$CONFIG_DIR/cloud_providers_config.json"
    fi
    
    echo -e "${GREEN}[✓] Configuration directory ready${NC}"
}

# Function to check system resources
check_resources() {
    echo -e "${CYAN}[NEXUS] Checking system resources...${NC}"
    
    # Check available memory
    MEM_AVAILABLE=$(free -m | awk 'NR==2{printf "%.1f", $7/1024}')
    if (( $(echo "$MEM_AVAILABLE > 1.0" | bc -l) )); then
        echo -e "${GREEN}[✓] Memory: ${MEM_AVAILABLE}GB available${NC}"
    else
        echo -e "${YELLOW}[!] Memory: Only ${MEM_AVAILABLE}GB available${NC}"
    fi
    
    # Check disk space
    DISK_AVAILABLE=$(df -h ~ | awk 'NR==2 {print $4}')
    echo -e "${GREEN}[✓] Disk space: $DISK_AVAILABLE available${NC}"
    
    # Check network connectivity
    if ping -c 1 google.com &> /dev/null; then
        echo -e "${GREEN}[✓] Internet connectivity: Online${NC}"
    else
        echo -e "${YELLOW}[!] Internet connectivity: Limited${NC}"
    fi
}

# Function to display startup banner
show_startup_info() {
    echo
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  NexusController Unified - Ready for Launch${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo
    echo -e "${GREEN}Available Features:${NC}"
    echo -e "  🖥️  Multi-Server Management (SSH, Docker, Services)"
    echo -e "  ☁️  Cloud Integration (13 providers including Google Drive)"
    echo -e "  🎬 Media Server Control (Jellyfin, PhotoPrism)"
    echo -e "  🏠 Home Automation (Home Assistant, Zigbee2MQTT)"
    echo -e "  🔒 Enterprise Security (Encryption, VPN, YubiKey)"
    echo -e "  📊 AI-Powered Monitoring (Predictive Analytics)"
    echo -e "  💾 Automated Google Drive Backup"
    echo -e "  🔧 System Optimization & Cleanup"
    echo
    echo -e "${BLUE}Quick Access URLs:${NC}"
    echo -e "  Media Server:    ${CYAN}http://10.0.0.29:8096${NC}"
    echo -e "  Home Assistant:  ${CYAN}http://10.0.0.29:8123${NC}"
    echo -e "  Node-RED:        ${CYAN}http://10.0.0.29:1880${NC}"
    echo
    echo -e "${YELLOW}Starting NexusController GUI...${NC}"
    echo
}

# Main execution
main() {
    # Startup checks
    check_dependencies
    setup_config
    setup_google_drive
    check_servers
    check_resources
    
    # Create desktop shortcut if requested
    if [ "$1" = "--install" ]; then
        create_desktop_shortcut
        echo -e "${GREEN}[✓] Installation completed${NC}"
        exit 0
    fi
    
    # Show startup information
    show_startup_info
    
    # Launch the unified NexusController
    echo -e "${GREEN}[NEXUS] Launching NexusController Unified...${NC}"
    python3 nexus_unified.py
}

# Handle command line arguments
case "$1" in
    --install)
        echo -e "${CYAN}Installing NexusController Unified...${NC}"
        main --install
        ;;
    --help)
        echo "NexusController Unified Launcher"
        echo
        echo "Usage: $0 [OPTION]"
        echo
        echo "Options:"
        echo "  --install    Install desktop shortcut and setup system"
        echo "  --help       Show this help message"
        echo "  (no args)    Launch NexusController"
        echo
        exit 0
        ;;
    *)
        main
        ;;
esac