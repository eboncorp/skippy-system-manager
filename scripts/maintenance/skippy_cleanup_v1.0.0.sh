#!/bin/bash
# Skippy Cleanup Script v1.0.0
# Purpose: Remove misplaced home directory files from skippy project
#
# Usage: ./skippy_cleanup_v1.0.0.sh [--dry-run]
#
# Created: 2024-12-24
#
# These directories are home directory artifacts that should NOT be in the
# skippy project. They're already in .gitignore but waste disk space.

set -euo pipefail

SKIPPY_DIR="/home/dave/skippy"
DRY_RUN=false

if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "=== DRY RUN MODE - No changes will be made ==="
    echo ""
fi

# Directories that should not be in skippy (home directory artifacts)
DIRS_TO_REMOVE=(
    ".steam"          # 8.5G - Steam gaming
    ".config"         # 7.4G - User config (belongs in ~/)
    ".cache"          # 2.4G - Cache files
    ".venvs"          # 2.2G - Virtual environments (recreatable)
    ".npm"            # 1.6G - NPM cache
    ".npm-global"     # 102M - NPM global
    ".thunderbird"    # 708M - Email (backup elsewhere!)
    ".tidytux"        # 738M - Old system manager
    ".local"          # 102M - Local share
    ".android_secure" # 53M - Android files
    ".backup_logs"    # 73M - Old backup logs
    ".ebonhawk-maintenance" # 3.2M - Old maintenance
    ".plcc-helper"    # 16M - Helper files
    ".wp-cli"         # 13M - WP-CLI cache
    ".unified-system-manager" # 300K - Old manager
    ".advanced-system-manager" # 60K - Old manager
    ".nexus"          # 200K - Old nexus files
    ".chainlink-sepolia" # 12K - Old blockchain
    ".ebon-link-2-sepolia" # 16K - Old blockchain
    ".config_backup_20251028" # 36K - Old backup
    ".cups"           # 4K - Printer config
    ".hplip"          # 4K - HP printer
    ".gnupg"          # 44K - GPG keys (be careful!)
    ".pki"            # 176K - PKI certs
    ".dotnet"         # 164K - .NET
    ".mozilla"        # 8K - Firefox
    ".Trash"          # 12K - Trash
    ".Trash-999"      # 128K - Trash
    ".epsonscan2"     # 32K - Scanner config
    ".devcontainer"   # 12K - Dev container
    ".dashboard"      # 8K - Dashboard
    ".home-server"    # 56K - Home server
)

# Directories in operations to clean
OPERATIONS_OLD=(
    "operations/claude_old"
    "operations/scans_old"
    "operations/temp_old"
    "operations/temp"
)

# Scripts archives to consolidate
SCRIPTS_ARCHIVES=(
    "scripts/.archived_old_versions"
    "scripts/.archived_broken"
    "scripts/archive"
)

echo "=== SKIPPY CLEANUP AUDIT ==="
echo ""
echo "Directory: $SKIPPY_DIR"
echo "Date: $(date)"
echo ""

echo "--- Home Directory Artifacts (should not be in skippy) ---"
total_size=0
for dir in "${DIRS_TO_REMOVE[@]}"; do
    full_path="$SKIPPY_DIR/$dir"
    if [[ -d "$full_path" ]]; then
        size=$(du -sh "$full_path" 2>/dev/null | cut -f1)
        echo "  $dir: $size"
        if [[ "$DRY_RUN" == false ]]; then
            # Special handling for .gnupg - don't delete without confirmation
            if [[ "$dir" == ".gnupg" ]]; then
                echo "    SKIPPED: .gnupg may contain important keys. Remove manually if safe."
            else
                rm -rf "$full_path"
                echo "    DELETED"
            fi
        fi
    fi
done
echo ""

echo "--- Operations Old Directories ---"
for dir in "${OPERATIONS_OLD[@]}"; do
    full_path="$SKIPPY_DIR/$dir"
    if [[ -d "$full_path" ]]; then
        size=$(du -sh "$full_path" 2>/dev/null | cut -f1)
        echo "  $dir: $size"
        if [[ "$DRY_RUN" == false ]]; then
            rm -rf "$full_path"
            echo "    DELETED"
        fi
    fi
done
echo ""

echo "--- Scripts Archives (consider consolidating) ---"
for dir in "${SCRIPTS_ARCHIVES[@]}"; do
    full_path="$SKIPPY_DIR/$dir"
    if [[ -d "$full_path" ]]; then
        size=$(du -sh "$full_path" 2>/dev/null | cut -f1)
        count=$(find "$full_path" -type f | wc -l)
        echo "  $dir: $size ($count files)"
    fi
done
echo ""

echo "--- Summary ---"
if [[ "$DRY_RUN" == true ]]; then
    echo "Run without --dry-run to delete files"
else
    echo "Cleanup complete! Run 'du -sh $SKIPPY_DIR' to see new size"
fi

echo ""
echo "=== MANUAL CLEANUP RECOMMENDED ==="
echo ""
echo "1. Git history (.git is 9.4G):"
echo "   Consider: git gc --aggressive --prune=now"
echo ""
echo "2. Consolidate script archives into single .archive/ directory"
echo ""
echo "3. Clean work/archive/ (497M) if old sessions no longer needed"
echo ""
echo "4. Review media/ (68G) - should this be in skippy?"
echo ""
