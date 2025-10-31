#!/bin/bash
# Connect to the fresh Ubuntu Server installation

SERVER="ebon@10.0.0.29"

echo "🚀 Connecting to Fresh Ubuntu Server"
echo "===================================="
echo
echo "Server: $SERVER"
echo "Enter the password you set during Ubuntu installation"
echo

# Option 1: Copy SSH key
echo "1. Setting up SSH key authentication..."
if ssh-copy-id "$SERVER"; then
    echo "✅ SSH key copied successfully!"
    echo
    
    echo "2. Testing SSH connection..."
    if ssh "$SERVER" "echo '✅ SSH key authentication working!'"; then
        echo
        echo "3. Running initial server setup..."
        ssh "$SERVER" "
            echo '📦 Updating packages...'
            sudo apt update && sudo apt upgrade -y
            
            echo '🔧 Installing essential tools...'
            sudo apt install -y curl wget git htop vim ufw tree ncdu docker.io
            
            echo '🔥 Configuring firewall...'
            sudo ufw enable --force
            sudo ufw allow ssh
            sudo ufw allow 8080
            sudo ufw allow 80
            sudo ufw allow 443
            
            echo '👥 Adding user to docker group...'
            sudo usermod -aG docker \$USER
            
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
            echo '✅ Server ready for Home Server Master installation!'
        "
        
        echo
        echo "🏠 Ready to install Home Server Master!"
        echo "Run these commands:"
        echo "  scp -r ~/Skippy/* $SERVER:/tmp/home-server/"
        echo "  ssh $SERVER"
        echo "  cd /tmp/home-server && ./home_server_installer.sh"
        
    else
        echo "❌ SSH connection failed"
    fi
else
    echo "❌ SSH key copy failed"
    echo "You can connect manually with: ssh $SERVER"
fi