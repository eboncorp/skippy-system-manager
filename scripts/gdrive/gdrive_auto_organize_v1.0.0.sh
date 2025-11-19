#!/bin/bash
#
# Google Drive Auto-Organize Script v1.0.0
# Author: Claude Code
# Created: 2025-11-11
# Purpose: Automatically organize Google Drive files using pattern-based rules
#
# Usage: ./gdrive_auto_organize_v1.0.0.sh [--dry-run]
#
# Cron: Add to crontab for automatic organization
#   Daily at 3 AM:    0 3 * * * /home/dave/skippy/development/scripts/scripts/gdrive/gdrive_auto_organize_v1.0.0.sh
#   Weekly on Sunday: 0 3 * * 0 /home/dave/skippy/development/scripts/scripts/gdrive/gdrive_auto_organize_v1.0.0.sh
#

set -euo pipefail

# Configuration
MCP_SERVER_DIR="/home/dave/skippy/mcp-servers/general-server"
LOG_DIR="/home/dave/skippy/log/gdrive"
LOG_FILE="$LOG_DIR/auto_organize_$(date +%Y%m%d_%H%M%S).log"
FOLDER_CACHE="/tmp/gdrive_organize_folders.json"
DRY_RUN=false

# Parse arguments
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "DRY RUN MODE - No files will be moved"
fi

# Create log directory
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "==================================================================="
log "Google Drive Auto-Organize Script v1.0.0"
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

# Check if folder cache exists, if not create it
if [[ ! -f "$FOLDER_CACHE" ]]; then
    log "WARNING: Folder cache not found, creating from common folders..."

    python3 -W ignore << 'PYEOF' 2>&1 | grep -v "file_cache" | tee -a "$LOG_FILE"
import sys
sys.path.insert(0, '/home/dave/skippy/mcp-servers/general-server')
from server import gdrive_get_folder_id_by_name
import json

folders = {}
common_folders = [
    'Documents', 'Downloads', 'Pictures', 'Technical', 'Financial',
    'Business', 'Campaign', 'Taxes', 'Transactions', 'Design', 'Personal'
]

print("Finding common folders...")
for name in common_folders:
    result = gdrive_get_folder_id_by_name(name, exact_match=True)
    data = json.loads(result)
    if data['found_count'] > 0:
        folders[name] = data['folders'][0]['id']
        print(f"  ✅ Found: {name}")

with open('/tmp/gdrive_organize_folders.json', 'w') as f:
    json.dump(folders, f, indent=2)

print(f"\nFolder cache created with {len(folders)} folders")
PYEOF
fi

# Run organization script
log ""
log "Starting organization process..."
log ""

export DRY_RUN=$DRY_RUN

python3 -W ignore << 'PYEOF' 2>&1 | grep -v "file_cache" | tee -a "$LOG_FILE"
import sys
import os
sys.path.insert(0, '/home/dave/skippy/mcp-servers/general-server')
from server import gdrive_organize_by_pattern
import json

DRY_RUN = os.environ.get('DRY_RUN', 'false') == 'true'

# Load folder IDs
try:
    with open('/tmp/gdrive_organize_folders.json', 'r') as f:
        folders = json.load(f)
except FileNotFoundError:
    print("ERROR: Folder cache not found")
    sys.exit(1)

print("=" * 70)
print("GOOGLE DRIVE AUTO-ORGANIZATION")
print("=" * 70)
print()

if DRY_RUN:
    print("🔍 DRY RUN MODE - No files will be moved")
    print()

results = {}
total_organized = 0

# Organization rules
organization_rules = [
    # PDFs to Downloads
    {
        'category': 'PDF Downloads',
        'patterns': [
            ("mimeType='application/pdf' and name contains 'invoice'", "Downloads", "Invoices"),
            ("mimeType='application/pdf' and name contains 'receipt'", "Downloads", "Receipts"),
            ("mimeType='application/pdf' and name contains 'statement'", "Financial", "Statements"),
        ]
    },

    # Images to Pictures
    {
        'category': 'Images',
        'patterns': [
            ("mimeType contains 'image' and not mimeType='image/svg+xml'", "Pictures", "Images"),
        ]
    },

    # Documents by type
    {
        'category': 'Text Documents',
        'patterns': [
            ("name contains '.docx' or name contains '.doc'", "Documents", "Word docs"),
            ("name contains '.txt'", "Documents", "Text files"),
        ]
    },

    # Spreadsheets
    {
        'category': 'Spreadsheets',
        'patterns': [
            ("name contains '.xlsx' or name contains '.xls'", "Financial", "Spreadsheets"),
            ("name contains '.csv'", "Financial", "CSV files"),
        ]
    },

    # Backups
    {
        'category': 'Backup Files',
        'patterns': [
            ("name contains 'backup' or name contains 'bak'", "Technical", "Backups"),
        ]
    },

    # Archives
    {
        'category': 'Archive Files',
        'patterns': [
            ("name contains '.zip' or name contains '.tar' or name contains '.gz'", "Technical", "Archives"),
        ]
    },
]

# Process each category
for rule in organization_rules:
    category = rule['category']
    print(f"\n📁 {category}")
    print("-" * 70)

    for pattern, folder, desc in rule['patterns']:
        if folder not in folders:
            print(f"   ⚠️  Folder '{folder}' not found, skipping {desc}")
            continue

        try:
            if DRY_RUN:
                # In dry run, set max_files to 0 to just count
                result = gdrive_organize_by_pattern(pattern, folders[folder], max_files=0)
            else:
                result = gdrive_organize_by_pattern(pattern, folders[folder], max_files=20)

            r = json.loads(result)
            if r['total_found'] > 0:
                if DRY_RUN:
                    print(f"   🔍 Would organize: {r['total_found']} {desc}")
                else:
                    print(f"   ✅ Organized: {r['successful_moves']}/{r['total_found']} {desc}")
                    total_organized += r['successful_moves']
                    results[desc] = r['successful_moves']
        except Exception as e:
            print(f"   ❌ Error with {desc}: {str(e)}")

print()
print("=" * 70)

if DRY_RUN:
    print("🔍 DRY RUN COMPLETE - No files were moved")
else:
    print("✅ AUTO-ORGANIZATION COMPLETE")
    print()
    print(f"📊 Summary:")
    print(f"   • Total files organized: {total_organized}")
    print(f"   • Categories processed: {len(results)}")

    if results:
        print()
        print("   Details:")
        for desc, count in results.items():
            print(f"   - {desc}: {count} files")

PYEOF

log ""
log "==================================================================="
log "Auto-organization complete"
log "Log saved to: $LOG_FILE"
log "==================================================================="

# Cleanup old logs (keep last 30 days)
find "$LOG_DIR" -name "auto_organize_*.log" -type f -mtime +30 -delete 2>/dev/null || true

exit 0
