#!/bin/bash
# Unified System Manager v3.0 Launcher

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Starting Unified System Manager v3.0...${NC}"

# Install required packages if missing
echo "Checking dependencies..."

# Check Python tkinter
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "Installing tkinter..."
    sudo apt update && sudo apt install -y python3-tk
fi

# Check psutil
if ! python3 -c "import psutil" 2>/dev/null; then
    echo "Installing psutil..."
    python3 -m pip install --user psutil || sudo apt install -y python3-psutil
fi

# Check paramiko
if ! python3 -c "import paramiko" 2>/dev/null; then
    echo "Installing paramiko for SSH support..."
    python3 -m pip install --user paramiko || sudo apt install -y python3-paramiko
fi

# Create config directory
mkdir -p ~/.config/unified-system-manager

# Go to app directory
cd "$(dirname "$0")"

# Run the new version
echo -e "${GREEN}Launching application...${NC}"
python3 unified_system_manager_v3.py