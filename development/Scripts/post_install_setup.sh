#!/bin/bash
# Post-installation setup script for HP Z4 G4 Ubuntu Server
# Run this after Ubuntu Server installation is complete

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SERVER_IP="10.0.0.29"
SERVER_USER="ebon"
SERVER_HOST="ebon-eth"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   HP Z4 G4 Post-Installation Setup${NC}"
echo -e "${BLUE}================================================${NC}"
echo

echo -e "${CYAN}This script will help you configure the freshly installed server${NC}"
echo "Target: $SERVER_USER@$SERVER_IP ($SERVER_HOST)"
echo

# Test connectivity
echo -e "${CYAN}Testing server connectivity...${NC}"
if ping -c 2 -W 1 "$SERVER_IP" &>/dev/null; then
    echo -e "${GREEN}✓ Server is reachable at $SERVER_IP${NC}"
else
    echo -e "${YELLOW}⚠ Server not reachable. Check if installation is complete.${NC}"
    exit 1
fi

# Test SSH
echo -e "${CYAN}Testing SSH access...${NC}"
if ssh -o ConnectTimeout=5 -o BatchMode=yes "$SERVER_USER@$SERVER_IP" "echo 'SSH working'" 2>/dev/null; then
    echo -e "${GREEN}✓ SSH key authentication working${NC}"
    SSH_READY=true
else
    echo -e "${YELLOW}⚠ SSH key authentication not set up yet${NC}"
    SSH_READY=false
fi

# SSH setup if needed
if [ "$SSH_READY" = false ]; then
    echo -e "\n${CYAN}Setting up SSH access...${NC}"
    echo "You'll need to enter the password you set during installation."
    
    if ssh-copy-id "$SERVER_USER@$SERVER_IP"; then
        echo -e "${GREEN}✓ SSH key copied successfully${NC}"
        SSH_READY=true
    else
        echo -e "${YELLOW}⚠ SSH key copy failed. You can set it up manually later.${NC}"
    fi
fi

# If SSH is working, run server setup
if [ "$SSH_READY" = true ]; then
    echo -e "\n${CYAN}Running initial server configuration...${NC}"
    
    ssh "$SERVER_USER@$SERVER_IP" "
        echo '🔄 Updating system packages...'
        sudo apt update -qq && sudo apt upgrade -y -qq
        
        echo '📦 Installing essential packages...'
        sudo apt install -y curl wget git htop vim ufw tree ncdu iotop nethogs
        
        echo '🔥 Configuring firewall...'
        sudo ufw --force enable
        sudo ufw allow ssh
        sudo ufw allow 8080
        sudo ufw allow 80
        sudo ufw allow 443
        
        echo '🕒 Setting timezone...'
        sudo timedatectl set-timezone America/New_York
        
        echo '🐳 Installing Docker...'
        curl -fsSL https://get.docker.com | sudo sh
        sudo usermod -aG docker $USER
        
        echo '📊 System information:'
        echo '===================='
        hostnamectl
        echo
        free -h
        echo
        df -h
        echo
        ip addr show | grep 'inet.*scope global'
        echo
        echo '✅ Server setup complete!'
    "
    
    echo -e "\n${GREEN}✅ Server configuration completed!${NC}"
else
    echo -e "\n${YELLOW}⚠ Skipping automatic configuration due to SSH issues${NC}"
fi

echo -e "\n${CYAN}Next steps:${NC}"
echo "1. SSH to server: ssh $SERVER_USER@$SERVER_IP"
echo "2. Copy Home Server Master files:"
echo "   scp -r ~/Skippy/* $SERVER_USER@$SERVER_IP:/tmp/home-server/"
echo "3. Install Home Server Master:"
echo "   ssh $SERVER_USER@$SERVER_IP 'cd /tmp/home-server && ./home_server_installer.sh'"

echo -e "\n${CYAN}Server URLs (after Home Server Master installation):${NC}"
echo "• SSH: ssh $SERVER_USER@$SERVER_IP"
echo "• Web UI: http://$SERVER_IP:8080"
echo "• Local: http://$SERVER_HOST.local:8080"

echo -e "\n${BLUE}================================================${NC}"