#!/bin/bash
#
# SSH Key Migration Helper for Skippy System Manager
# Version: 1.0.0
# Purpose: Migrate from password authentication to SSH key authentication
# Usage: ./migrate_ssh_keys.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKIPPY_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MCP_ENV_FILE="$SKIPPY_ROOT/mcp-servers/general-server/.env"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  SSH Key Migration Helper for Skippy System Manager  ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to print success message
success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print error message
error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to print warning message
warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to print info message
info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if .env file exists
if [ ! -f "$MCP_ENV_FILE" ]; then
    error ".env file not found at: $MCP_ENV_FILE"
    info "Creating .env from .env.example..."
    if [ -f "$MCP_ENV_FILE.example" ]; then
        cp "$MCP_ENV_FILE.example" "$MCP_ENV_FILE"
        chmod 600 "$MCP_ENV_FILE"
        success "Created .env file"
    else
        error "No .env.example file found either!"
        exit 1
    fi
fi

# Load current configuration
if [ -f "$MCP_ENV_FILE" ]; then
    source "$MCP_ENV_FILE"
fi

# Check if already using SSH keys
if [ -n "${SSH_KEY_PATH:-}" ] && [ -f "${SSH_KEY_PATH}" ]; then
    success "SSH key authentication is already configured!"
    info "SSH_KEY_PATH=$SSH_KEY_PATH"
    echo ""
    read -p "Do you want to reconfigure? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "Exiting without changes."
        exit 0
    fi
fi

echo ""
echo -e "${YELLOW}This script will help you migrate from password authentication to SSH key authentication.${NC}"
echo ""

# Step 1: Get remote server info
echo -e "${BLUE}Step 1: Remote Server Configuration${NC}"
echo "────────────────────────────────────"
info "Current EBON_HOST: ${EBON_HOST:-not set}"
read -p "Remote server (e.g., ebon@10.0.0.29) [${EBON_HOST:-}]: " REMOTE_HOST
REMOTE_HOST="${REMOTE_HOST:-${EBON_HOST:-}}"

if [ -z "$REMOTE_HOST" ]; then
    error "Remote host is required!"
    exit 1
fi

# Extract user and host
REMOTE_USER=$(echo "$REMOTE_HOST" | cut -d'@' -f1)
REMOTE_IP=$(echo "$REMOTE_HOST" | cut -d'@' -f2)

success "Remote server: $REMOTE_HOST"
echo ""

# Step 2: Check for existing SSH keys
echo -e "${BLUE}Step 2: SSH Key Setup${NC}"
echo "───────────────────────"

DEFAULT_KEY="$HOME/.ssh/skippy_ed25519"
info "Checking for existing SSH keys..."

if [ -f "$DEFAULT_KEY" ]; then
    success "Found existing key: $DEFAULT_KEY"
    read -p "Use this key? (Y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        DEFAULT_KEY=""
    fi
fi

if [ -z "$DEFAULT_KEY" ] || [ ! -f "$DEFAULT_KEY" ]; then
    warning "No suitable SSH key found."
    read -p "Generate a new SSH key? (Y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        info "Generating new ED25519 SSH key..."
        ssh-keygen -t ed25519 -C "skippy@system" -f "$DEFAULT_KEY" -N ""
        if [ $? -eq 0 ]; then
            success "SSH key generated: $DEFAULT_KEY"
        else
            error "Failed to generate SSH key"
            exit 1
        fi
    else
        read -p "Enter path to existing SSH private key: " CUSTOM_KEY
        if [ -f "$CUSTOM_KEY" ]; then
            DEFAULT_KEY="$CUSTOM_KEY"
            success "Using existing key: $DEFAULT_KEY"
        else
            error "Key file not found: $CUSTOM_KEY"
            exit 1
        fi
    fi
fi

SSH_PUBLIC_KEY="${DEFAULT_KEY}.pub"

echo ""

# Step 3: Copy key to remote server
echo -e "${BLUE}Step 3: Copy Key to Remote Server${NC}"
echo "────────────────────────────────────"

info "Copying SSH key to remote server..."
info "You may be prompted for the remote server password."
echo ""

if ssh-copy-id -i "$SSH_PUBLIC_KEY" "$REMOTE_HOST" 2>&1; then
    success "SSH key copied to remote server"
else
    error "Failed to copy SSH key"
    warning "You can manually copy it with:"
    echo "  ssh-copy-id -i $SSH_PUBLIC_KEY $REMOTE_HOST"
    exit 1
fi

echo ""

# Step 4: Test SSH connection
echo -e "${BLUE}Step 4: Test Connection${NC}"
echo "───────────────────────"

info "Testing SSH connection with key..."
if ssh -i "$DEFAULT_KEY" -o StrictHostKeyChecking=accept-new -o PasswordAuthentication=no "$REMOTE_HOST" "echo 'Connection successful'" 2>&1; then
    success "SSH key authentication works!"
else
    error "SSH key authentication failed"
    warning "Please check:"
    echo "  1. SSH key was copied correctly"
    echo "  2. Remote server allows key authentication"
    echo "  3. File permissions on remote ~/.ssh directory (700)"
    echo "  4. File permissions on remote ~/.ssh/authorized_keys (600)"
    exit 1
fi

echo ""

# Step 5: Update .env file
echo -e "${BLUE}Step 5: Update Configuration${NC}"
echo "────────────────────────────"

info "Updating .env file..."

# Backup existing .env
cp "$MCP_ENV_FILE" "${MCP_ENV_FILE}.backup"
success "Created backup: ${MCP_ENV_FILE}.backup"

# Update or add SSH_KEY_PATH
if grep -q "^SSH_KEY_PATH=" "$MCP_ENV_FILE"; then
    sed -i "s|^SSH_KEY_PATH=.*|SSH_KEY_PATH=$DEFAULT_KEY|" "$MCP_ENV_FILE"
else
    echo "SSH_KEY_PATH=$DEFAULT_KEY" >> "$MCP_ENV_FILE"
fi

# Comment out EBON_PASSWORD if it exists
if grep -q "^EBON_PASSWORD=" "$MCP_ENV_FILE"; then
    sed -i "s|^EBON_PASSWORD=|# EBON_PASSWORD=|" "$MCP_ENV_FILE"
    success "Commented out EBON_PASSWORD (no longer needed)"
fi

success "Updated $MCP_ENV_FILE"
echo ""

# Step 6: Verify permissions
echo -e "${BLUE}Step 6: Security Check${NC}"
echo "──────────────────────"

# Set correct permissions on private key
chmod 600 "$DEFAULT_KEY"
success "Set permissions on private key (600)"

# Set correct permissions on .env file
chmod 600 "$MCP_ENV_FILE"
success "Set permissions on .env file (600)"

echo ""

# Summary
echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Migration Completed Successfully!          ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Summary:${NC}"
echo "─────────"
echo "  • SSH key: $DEFAULT_KEY"
echo "  • Remote server: $REMOTE_HOST"
echo "  • Configuration: $MCP_ENV_FILE"
echo "  • Backup: ${MCP_ENV_FILE}.backup"
echo ""
echo -e "${GREEN}Benefits of SSH Key Authentication:${NC}"
echo "  ✓ More secure than password authentication"
echo "  ✓ Password not visible in process list"
echo "  ✓ No password stored in environment variables"
echo "  ✓ Better automation support"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Restart any running MCP servers"
echo "  2. Test remote commands:"
echo "     ssh -i $DEFAULT_KEY $REMOTE_HOST 'hostname'"
echo "  3. Review security documentation: $SKIPPY_ROOT/SECURITY.md"
echo ""
echo -e "${YELLOW}Note: The old .env with password is backed up at:${NC}"
echo "      ${MCP_ENV_FILE}.backup"
echo ""
