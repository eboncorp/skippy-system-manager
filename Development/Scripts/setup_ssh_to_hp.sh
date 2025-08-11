#!/bin/bash
# Setup SSH access to HP Z4 G4 (ebon-eth)

set -euo pipefail

TARGET="10.0.0.29"
USERNAME="ebon"

echo "🔧 Setting up SSH access to HP Z4 G4 (ebon-eth)"
echo "================================================"
echo
echo "Target: $USERNAME@$TARGET"
echo

# Check if we have SSH keys
if [ ! -f ~/.ssh/id_ed25519.pub ] && [ ! -f ~/.ssh/id_rsa.pub ]; then
    echo "❌ No SSH public keys found"
    echo "Generating new SSH key..."
    ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N "" -C "dave@$(hostname)"
    echo "✅ SSH key generated"
fi

# Show public key
echo "📋 Your SSH public key:"
if [ -f ~/.ssh/id_ed25519.pub ]; then
    cat ~/.ssh/id_ed25519.pub
    KEY_FILE="~/.ssh/id_ed25519.pub"
elif [ -f ~/.ssh/id_rsa.pub ]; then
    cat ~/.ssh/id_rsa.pub
    KEY_FILE="~/.ssh/id_rsa.pub"
fi

echo
echo "🔑 To set up passwordless SSH access:"
echo "1. Copy the SSH key above"
echo "2. Connect to the HP server manually:"
echo "   ssh $USERNAME@$TARGET"
echo "3. Once logged in, run these commands:"
echo "   mkdir -p ~/.ssh"
echo "   echo 'PASTE_YOUR_PUBLIC_KEY_HERE' >> ~/.ssh/authorized_keys"
echo "   chmod 700 ~/.ssh"
echo "   chmod 600 ~/.ssh/authorized_keys"
echo
echo "Or use this one-liner to copy the key:"
echo "ssh-copy-id -i $KEY_FILE $USERNAME@$TARGET"
echo
echo "🧪 Testing current SSH access..."

# Try SSH connection
if ssh -o BatchMode=yes -o ConnectTimeout=5 "$USERNAME@$TARGET" "echo 'SSH key authentication working!'" 2>/dev/null; then
    echo "✅ SSH key authentication successful!"
    echo
    echo "🔍 Getting system information..."
    ssh "$USERNAME@$TARGET" "
        echo '=== System Info ==='
        whoami
        hostname
        uname -a
        echo
        echo '=== Resources ==='
        free -h
        df -h /
        echo
        echo '=== Services ==='
        systemctl is-active apache2 nginx docker 2>/dev/null || true
        echo
        echo '=== What\\'s running on port 80 ==='
        sudo netstat -tlnp | grep :80 || ss -tlnp | grep :80
    "
else
    echo "❌ SSH key authentication not set up yet"
    echo
    echo "🔧 Manual setup required:"
    echo "1. Run: ssh-copy-id $USERNAME@$TARGET"
    echo "2. Enter password when prompted"
    echo "3. Run this script again to test"
fi