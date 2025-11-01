#\!/usr/bin/env python3
"""
NexusController Media Server Launcher
Enhanced launcher with real monitoring capabilities
"""
import subprocess
import sys
import os

if __name__ == "__main__":
    print("Starting Enhanced NexusController with Real-time Monitoring...")
    # Launch the enhanced simple server
    os.execv(sys.executable, [sys.executable, "enhanced_simple_server.py"])
