#!/bin/bash
# Claude Code Startup Hook
# This script runs automatically when Claude Code starts

# Start downloads watcher daemon if not already running
if ! /home/dave/skippy/scripts/monitoring/downloads_watcher_v1.0.0.py --status 2>/dev/null | grep -q "Running"; then
    /home/dave/skippy/scripts/monitoring/downloads_watcher_v1.0.0.py --daemon &>/dev/null
fi
