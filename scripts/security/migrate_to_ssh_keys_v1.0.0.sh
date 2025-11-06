#!/bin/bash
# SSH Key Migration Helper
# Version: 1.0.0
# Purpose: Migrate from password authentication to SSH key-based auth
# Usage: ./migrate_to_ssh_keys_v1.0.0.sh

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SSH_KEY_PATH="${HOME}/.ssh/id_skippy_ed25519"
SSH_CONFIG="${HOME}/.ssh/config"

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}  SSH Key Migration Helper${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# Check if config.env exists
if [ ! -f "config.env" ]; then
    echo -e "${RED}Error: config.env not found${NC}"
    echo "Please run this script from the project root"
    exit 1
fi

# Load configuration
source config.env

# Validate EBON_HOST
if [ -z "${EBON_HOST:-}" ]; then
    echo -e "${RED}Error: EBON_HOST not set in config.env${NC}"
    exit 1
fi

# Parse host
if [[ "${EBON_HOST}" == *"@"* ]]; then
    SSH_USER="${EBON_HOST%@*}"
    SSH_HOST="${EBON_HOST#*@}"
else
    echo -e "${RED}Error: EBON_HOST must be in format user@host${NC}"
    exit 1
fi

echo -e "${BLUE}Current Configuration:${NC}"
echo "  User: ${SSH_USER}"
echo "  Host: ${SSH_HOST}"
echo "  Auth: Password (will migrate to SSH keys)"
echo ""

# Step 1: Check for existing SSH key
echo -e "${YELLOW}Step 1: Checking for existing SSH keys...${NC}"
if [ -f "${SSH_KEY_PATH}" ]; then
    echo -e "${GREEN}✓ SSH key already exists: ${SSH_KEY_PATH}${NC}"
    read -p "Use existing key? (y/n): " use_existing
    if [[ "${use_existing}" != "y" ]]; then
        SSH_KEY_PATH="${HOME}/.ssh/id_skippy_$(date +%Y%m%d)_ed25519"
        echo "Will create new key: ${SSH_KEY_PATH}"
    fi
else
    echo "No existing key found"
fi
echo ""

# Step 2: Generate SSH key if needed
if [ ! -f "${SSH_KEY_PATH}" ]; then
    echo -e "${YELLOW}Step 2: Generating new SSH key...${NC}"
    ssh-keygen -t ed25519 -f "${SSH_KEY_PATH}" -C "skippy@${SSH_HOST}" -N ""
    echo -e "${GREEN}✓ SSH key generated${NC}"
else
    echo -e "${YELLOW}Step 2: Using existing SSH key${NC}"
fi
echo ""

# Step 3: Copy key to remote server
echo -e "${YELLOW}Step 3: Copying key to remote server...${NC}"
echo "You will be prompted for your password"

if [ -n "${EBON_PASSWORD:-}" ]; then
    echo "Using password from config.env..."
    # Using sshpass if available
    if command -v sshpass >/dev/null 2>&1; then
        sshpass -p "${EBON_PASSWORD}" ssh-copy-id -i "${SSH_KEY_PATH}.pub" "${SSH_USER}@${SSH_HOST}"
    else
        echo -e "${YELLOW}Note: sshpass not installed, you'll need to enter password manually${NC}"
        ssh-copy-id -i "${SSH_KEY_PATH}.pub" "${SSH_USER}@${SSH_HOST}"
    fi
else
    ssh-copy-id -i "${SSH_KEY_PATH}.pub" "${SSH_USER}@${SSH_HOST}"
fi

echo -e "${GREEN}✓ Key copied to server${NC}"
echo ""

# Step 4: Test SSH connection
echo -e "${YELLOW}Step 4: Testing SSH connection...${NC}"
if ssh -i "${SSH_KEY_PATH}" -o PasswordAuthentication=no "${SSH_USER}@${SSH_HOST}" "echo 'SSH key authentication working!'" 2>/dev/null; then
    echo -e "${GREEN}✓ SSH key authentication successful!${NC}"
else
    echo -e "${RED}✗ SSH key authentication failed${NC}"
    echo "Please check the key was copied correctly"
    exit 1
fi
echo ""

# Step 5: Update SSH config
echo -e "${YELLOW}Step 5: Updating SSH config...${NC}"
mkdir -p "${HOME}/.ssh"
chmod 700 "${HOME}/.ssh"

if ! grep -q "Host ${SSH_HOST}" "${SSH_CONFIG}" 2>/dev/null; then
    cat >> "${SSH_CONFIG}" <<EOF

# Skippy System Manager
Host ${SSH_HOST}
    HostName ${SSH_HOST}
    User ${SSH_USER}
    IdentityFile ${SSH_KEY_PATH}
    IdentitiesOnly yes
EOF
    echo -e "${GREEN}✓ SSH config updated${NC}"
else
    echo -e "${YELLOW}⚠ SSH config entry already exists${NC}"
fi
echo ""

# Step 6: Update config.env
echo -e "${YELLOW}Step 6: Updating config.env...${NC}"

# Backup config.env
cp config.env config.env.backup

# Comment out EBON_PASSWORD
sed -i.bak 's/^export EBON_PASSWORD=/#export EBON_PASSWORD=/' config.env

# Add SSH_PRIVATE_KEY if not present
if ! grep -q "SSH_PRIVATE_KEY" config.env; then
    cat >> config.env <<EOF

# SSH Key Authentication (migrated from password)
export SSH_PRIVATE_KEY="${SSH_KEY_PATH}"
EOF
fi

echo -e "${GREEN}✓ config.env updated${NC}"
echo "  - EBON_PASSWORD commented out"
echo "  - SSH_PRIVATE_KEY added"
echo "  - Backup saved as config.env.backup"
echo ""

# Step 7: Final test
echo -e "${YELLOW}Step 7: Final verification...${NC}"
echo "Testing connection without password..."

if ssh -i "${SSH_KEY_PATH}" "${SSH_USER}@${SSH_HOST}" "echo 'Final test successful!'" 2>/dev/null; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${RED}✗ Final test failed${NC}"
    echo "Restoring backup..."
    mv config.env.backup config.env
    exit 1
fi
echo ""

# Summary
echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}  Migration Complete!${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""
echo -e "${GREEN}✓ SSH key authentication configured${NC}"
echo ""
echo "Next steps:"
echo "  1. Test Skippy scripts to ensure they work"
echo "  2. If everything works, delete config.env.backup"
echo "  3. Consider disabling password auth on server:"
echo "     sudo sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config"
echo "     sudo systemctl restart sshd"
echo ""
echo "Key files:"
echo "  Private key: ${SSH_KEY_PATH}"
echo "  Public key: ${SSH_KEY_PATH}.pub"
echo "  SSH config: ${SSH_CONFIG}"
echo ""
