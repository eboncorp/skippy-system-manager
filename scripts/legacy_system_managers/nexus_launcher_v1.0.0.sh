#!/bin/bash
# NexusController Launcher
# Central Command Hub for Local and Remote Systems

# Colors
CYAN='\033[0;36m'
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

# ASCII Art Banner
echo -e "${CYAN}"
echo "    _   __                      ______            __             ____         "
echo "   / | / /__  _  ____  _______/ ____/___  ____  / /__________  / / /__  _____"
echo "  /  |/ / _ \\| |/_/ / / / ___/ /   / __ \\/ __ \\/ __/ ___/ __ \\/ / / _ \\/ ___/"
echo " / /|  /  __/>  </ /_/ (__  ) /___/ /_/ / / / / /_/ /  / /_/ / / /  __/ /    "
echo "/_/ |_/\\___/_/|_|\\__,_/____/\\____/\\____/_/ /_/\\__/_/   \\____/_/_/\\___/_/     "
echo -e "${NC}"
echo -e "${BLUE}Central Command Hub v1.0${NC}"
echo

# Check dependencies
echo -e "${CYAN}[NEXUS] Initializing subsystems...${NC}"

# Check Python tkinter
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo -e "${BLUE}[>] Installing GUI framework...${NC}"
    sudo apt update && sudo apt install -y python3-tk
fi

# Check psutil
if ! python3 -c "import psutil" 2>/dev/null; then
    echo -e "${BLUE}[>] Installing system monitor...${NC}"
    python3 -m pip install --user psutil || sudo apt install -y python3-psutil
fi

# Check paramiko
if ! python3 -c "import paramiko" 2>/dev/null; then
    echo -e "${BLUE}[>] Installing SSH subsystem...${NC}"
    python3 -m pip install --user paramiko || sudo apt install -y python3-paramiko
fi

# Create config directory
mkdir -p ~/.config/nexus-controller

# Go to app directory
cd "$(dirname "$0")"

# Launch NexusController
echo -e "${GREEN}[NEXUS] All systems operational. Launching...${NC}"
python3 nexus_control_center.py