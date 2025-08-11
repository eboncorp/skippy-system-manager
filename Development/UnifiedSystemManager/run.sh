#!/bin/bash
# Fixed Unified System Manager Launcher

# Install tkinter if missing
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "Installing tkinter..."
    sudo apt update && sudo apt install -y python3-tk
fi

# Go to app directory
cd "/home/dave/UnifiedSystemManager"

# Run the application directly with system Python
python3 unified_system_manager.py
