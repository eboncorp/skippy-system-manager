#!/bin/bash
# Security Hardening for NexusController

echo "🔒 Applying security hardening..."

# Secure file permissions
find ~/.nexus -type f -exec chmod 600 {} \;
find ~/.nexus -type d -exec chmod 700 {} \;

# SSH key permissions
chmod 600 ~/.ssh/id_* 2>/dev/null
chmod 644 ~/.ssh/*.pub 2>/dev/null
chmod 600 ~/.ssh/config 2>/dev/null
chmod 644 ~/.ssh/known_hosts 2>/dev/null

# Update system
sudo apt update && sudo apt upgrade -y

# Update Python packages
python3 -m pip install --user --upgrade pip
python3 -m pip install --user --upgrade cryptography paramiko fido2

echo "✅ Security hardening completed"
