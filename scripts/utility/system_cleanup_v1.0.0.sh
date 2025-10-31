#!/bin/bash
################################################################################
# Script: system_cleanup_v1.0.0.sh
# Purpose: Quick system cleanup - remove temp files, caches, etc.
# Version: 1.0.0
# Created: 2025-10-28
################################################################################

echo "=== System Cleanup ==="
echo ""

# Python caches
echo "[1/5] Cleaning Python caches..."
find /home/dave/skippy -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find /home/dave/skippy -name "*.pyc" -delete 2>/dev/null
echo "✅ Python caches cleaned"

# Temp files
echo "[2/5] Cleaning temp files..."
find /home/dave/skippy -name "*.tmp" -delete 2>/dev/null
find /home/dave/skippy -name ".~*" -delete 2>/dev/null
find /home/dave/skippy -name "*~" -delete 2>/dev/null
echo "✅ Temp files cleaned"

# Old logs (>30 days)
echo "[3/5] Cleaning old logs..."
find /home/dave/skippy -name "*.log" -mtime +30 -delete 2>/dev/null
echo "✅ Old logs cleaned"

# Empty directories
echo "[4/5] Removing empty directories..."
find /home/dave/skippy -type d -empty -delete 2>/dev/null
echo "✅ Empty directories removed"

# Duplicate reports older than 7 days
echo "[5/5] Cleaning old duplicate reports..."
find /tmp -name "duplicate_report_*.txt" -mtime +7 -delete 2>/dev/null
echo "✅ Old reports cleaned"

echo ""
echo "=== Cleanup Complete ==="
