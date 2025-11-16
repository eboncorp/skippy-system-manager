#!/bin/bash
#
# Google Drive Folder Cleanup Script v1.0.0
# Author: Claude Code
# Created: 2025-11-11
# Purpose: Identify and report duplicate/unclear folder names in Google Drive
#
# Usage: ./gdrive_folder_cleanup_v1.0.0.sh [--fix]
#

set -euo pipefail

# Configuration
MCP_SERVER_DIR="/home/dave/skippy/mcp-servers/general-server"
LOG_DIR="/home/dave/skippy/log/gdrive"
LOG_FILE="$LOG_DIR/folder_cleanup_$(date +%Y%m%d_%H%M%S).log"
FIX_MODE=false

# Parse arguments
if [[ "${1:-}" == "--fix" ]]; then
    FIX_MODE=true
    echo "FIX MODE - Will rename unclear folders"
fi

# Create log directory
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "==================================================================="
log "Google Drive Folder Cleanup Script v1.0.0"
log "==================================================================="
log ""

# Check if MCP server exists
if [[ ! -f "$MCP_SERVER_DIR/server.py" ]]; then
    log "ERROR: MCP server not found at $MCP_SERVER_DIR/server.py"
    exit 1
fi

# Activate virtual environment
log "Activating virtual environment..."
cd "$MCP_SERVER_DIR"
source .venv/bin/activate

# Run folder analysis script
log ""
log "Analyzing Google Drive folder structure..."
log ""

export FIX_MODE=$FIX_MODE

python3 -W ignore << 'PYEOF' 2>&1 | grep -v "file_cache" | tee -a "$LOG_FILE"
import sys
import os
sys.path.insert(0, '/home/dave/skippy/mcp-servers/general-server')
from server import gdrive_list_folder_contents, gdrive_rename_file, gdrive_get_folder_id_by_name
import json
from collections import defaultdict

FIX_MODE = os.environ.get('FIX_MODE', 'false') == 'true'

print("=" * 70)
print("GOOGLE DRIVE FOLDER CLEANUP ANALYSIS")
print("=" * 70)
print()

if FIX_MODE:
    print("🔧 FIX MODE - Will rename unclear folders")
    print()

# List root folder contents
result = gdrive_list_folder_contents("root", max_results=500)
data = json.loads(result)

if not data.get('success'):
    print("ERROR: Could not list root folder contents")
    sys.exit(1)

# Separate folders from files
all_items = data.get('files', [])
folders = [item for item in all_items if item.get('mimeType') == 'application/vnd.google-apps.folder']
files = [item for item in all_items if item.get('mimeType') != 'application/vnd.google-apps.folder']

print(f"📊 Root Directory Analysis:")
print(f"   • Total items: {len(all_items)}")
print(f"   • Folders: {len(folders)}")
print(f"   • Files: {len(files)}")
print()

# Group folders by name (case-insensitive) to find duplicates
folder_names = defaultdict(list)
for folder in folders:
    name_lower = folder['name'].lower()
    folder_names[name_lower].append(folder)

# Find duplicates
duplicates = {name: items for name, items in folder_names.items() if len(items) > 1}

if duplicates:
    print("⚠️  DUPLICATE FOLDER NAMES FOUND:")
    print()
    for name, items in duplicates.items():
        print(f"   📁 '{name}' - {len(items)} folders with this name:")
        for item in items:
            print(f"      - ID: {item['id']}")
            print(f"        Created: {item.get('createdTime', 'Unknown')}")
            # List how many items are in each
            contents = gdrive_list_folder_contents(item['id'], max_results=10)
            contents_data = json.loads(contents)
            count = contents_data.get('total_items', 0)
            print(f"        Contains: {count} items")
        print()
else:
    print("✅ No duplicate folder names found")
    print()

# Identify unclear/ambiguous folder names
unclear_patterns = [
    'untitled', 'new folder', 'temp', 'tmp', 'misc', 'stuff',
    'other', 'old', 'archive', 'backup', 'test'
]

unclear_folders = []
for folder in folders:
    name_lower = folder['name'].lower()
    if any(pattern in name_lower for pattern in unclear_patterns):
        unclear_folders.append(folder)

if unclear_folders:
    print("⚠️  UNCLEAR/AMBIGUOUS FOLDER NAMES:")
    print()
    for folder in unclear_folders:
        print(f"   📁 '{folder['name']}' (ID: {folder['id']})")
        # Show contents to help identify purpose
        contents = gdrive_list_folder_contents(folder['id'], max_results=5)
        contents_data = json.loads(contents)
        items = contents_data.get('files', [])
        if items:
            print(f"      Sample contents:")
            for item in items[:3]:
                print(f"      - {item['name']}")
        else:
            print(f"      Empty folder")
        print()
else:
    print("✅ No unclear folder names found")
    print()

# Report folders with numbers or unclear naming
print("📝 FOLDER NAMING RECOMMENDATIONS:")
print()

recommendations = []

# Folders with just numbers
for folder in folders:
    if folder['name'].strip().isdigit():
        recommendations.append({
            'folder': folder,
            'issue': 'Number-only name',
            'suggestion': 'Add descriptive name'
        })

# Folders with multiple spaces or special characters
import re
for folder in folders:
    if '  ' in folder['name'] or re.search(r'[^\w\s\-\(\)]', folder['name']):
        recommendations.append({
            'folder': folder,
            'issue': 'Contains special characters or multiple spaces',
            'suggestion': 'Clean up name formatting'
        })

if recommendations:
    for rec in recommendations:
        print(f"   📁 '{rec['folder']['name']}'")
        print(f"      Issue: {rec['issue']}")
        print(f"      Suggestion: {rec['suggestion']}")
        print(f"      ID: {rec['folder']['id']}")
        print()
else:
    print("   ✅ All folder names follow good conventions")
    print()

# Summary
print("=" * 70)
print("CLEANUP SUMMARY")
print("=" * 70)
print(f"   • Duplicate folder names: {len(duplicates)}")
print(f"   • Unclear folder names: {len(unclear_folders)}")
print(f"   • Naming recommendations: {len(recommendations)}")
print()

if FIX_MODE:
    print("Note: Automatic renaming not implemented yet.")
    print("Please review folder contents and rename manually as needed.")
    print()
else:
    print("Run with --fix flag to enable automatic cleanup (future feature)")
    print()

PYEOF

log ""
log "==================================================================="
log "Folder cleanup analysis complete"
log "Log saved to: $LOG_FILE"
log "==================================================================="

exit 0
