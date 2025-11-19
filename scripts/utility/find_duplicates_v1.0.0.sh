#!/bin/bash
################################################################################
# Script: find_duplicates_v1.0.0.sh
# Purpose: Find duplicate files in system by content (MD5 hash)
# Version: 1.0.0
# Created: 2025-10-28
# Location: /home/dave/skippy/development/scripts/scripts/utility/
################################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SEARCH_DIR="${1:-/home/dave/skippy}"
TEMP_DIR="/tmp/duplicate_finder_$$"
OUTPUT_FILE="/tmp/duplicate_report_$(date +%Y%m%d_%H%M%S).txt"

echo -e "${BLUE}=== Duplicate File Finder ===${NC}"
echo "Searching in: $SEARCH_DIR"
echo "Report will be saved to: $OUTPUT_FILE"
echo ""

# Create temp directory
mkdir -p "$TEMP_DIR"

# Function to clean up
cleanup() {
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

echo -e "${YELLOW}[1/4] Finding all files...${NC}"
# Find all regular files, exclude certain directories
find "$SEARCH_DIR" \
    -type f \
    ! -path "*/.*" \
    ! -path "*/__pycache__/*" \
    ! -path "*/node_modules/*" \
    ! -path "*/.git/*" \
    2>/dev/null > "$TEMP_DIR/all_files.txt"

TOTAL_FILES=$(wc -l < "$TEMP_DIR/all_files.txt")
echo "Found $TOTAL_FILES files to analyze"

echo -e "${YELLOW}[2/4] Calculating MD5 hashes...${NC}"
# Calculate MD5 for each file
while IFS= read -r file; do
    if [ -f "$file" ]; then
        md5=$(md5sum "$file" 2>/dev/null | awk '{print $1}')
        size=$(stat -f "%z" "$file" 2>/dev/null || stat -c "%s" "$file" 2>/dev/null)
        echo "$md5|$size|$file"
    fi
done < "$TEMP_DIR/all_files.txt" > "$TEMP_DIR/file_hashes.txt"

echo -e "${YELLOW}[3/4] Finding duplicates...${NC}"
# Find duplicate hashes (files with same MD5)
awk -F'|' '{print $1}' "$TEMP_DIR/file_hashes.txt" | sort | uniq -d > "$TEMP_DIR/duplicate_hashes.txt"

DUPLICATE_GROUPS=$(wc -l < "$TEMP_DIR/duplicate_hashes.txt")
echo "Found $DUPLICATE_GROUPS groups of duplicate files"

echo -e "${YELLOW}[4/4] Generating report...${NC}"

# Generate report
{
    echo "======================================================================"
    echo "DUPLICATE FILES REPORT"
    echo "Generated: $(date)"
    echo "Search Directory: $SEARCH_DIR"
    echo "======================================================================"
    echo ""
    echo "Summary:"
    echo "  Total files scanned: $TOTAL_FILES"
    echo "  Duplicate groups found: $DUPLICATE_GROUPS"
    echo ""
    echo "======================================================================"
    echo ""

    GROUP_NUM=1
    TOTAL_WASTED=0

    while IFS= read -r hash; do
        echo "----------------------------------------------------------------------"
        echo "Duplicate Group #$GROUP_NUM (MD5: $hash)"
        echo "----------------------------------------------------------------------"

        # Get all files with this hash
        grep "^$hash|" "$TEMP_DIR/file_hashes.txt" | while IFS='|' read -r h size filepath; do
            size_kb=$((size / 1024))
            echo "  [$size_kb KB] $filepath"
        done

        # Calculate wasted space (all but one copy)
        COUNT=$(grep -c "^$hash|" "$TEMP_DIR/file_hashes.txt")
        if [ "$COUNT" -gt 1 ]; then
            FIRST_SIZE=$(grep "^$hash|" "$TEMP_DIR/file_hashes.txt" | head -1 | cut -d'|' -f2)
            WASTED=$((FIRST_SIZE * (COUNT - 1)))
            WASTED_KB=$((WASTED / 1024))
            TOTAL_WASTED=$((TOTAL_WASTED + WASTED))
            echo "  Wasted space: $WASTED_KB KB ($(($COUNT - 1)) duplicate copies)"
        fi

        echo ""
        GROUP_NUM=$((GROUP_NUM + 1))
    done < "$TEMP_DIR/duplicate_hashes.txt"

    echo "======================================================================"
    echo "TOTAL WASTED SPACE: $((TOTAL_WASTED / 1024)) KB ($((TOTAL_WASTED / 1048576)) MB)"
    echo "======================================================================"

} > "$OUTPUT_FILE"

# Display summary
echo ""
echo -e "${GREEN}✅ Report generated successfully!${NC}"
echo ""
echo "Summary:"
echo "  Total files scanned: $TOTAL_FILES"
echo "  Duplicate groups found: $DUPLICATE_GROUPS"
echo ""

# Calculate total wasted space
TOTAL_WASTED=0
while IFS= read -r hash; do
    COUNT=$(grep -c "^$hash|" "$TEMP_DIR/file_hashes.txt")
    if [ "$COUNT" -gt 1 ]; then
        FIRST_SIZE=$(grep "^$hash|" "$TEMP_DIR/file_hashes.txt" | head -1 | cut -d'|' -f2)
        WASTED=$((FIRST_SIZE * (COUNT - 1)))
        TOTAL_WASTED=$((TOTAL_WASTED + WASTED))
    fi
done < "$TEMP_DIR/duplicate_hashes.txt"

echo "  Total wasted space: $((TOTAL_WASTED / 1024)) KB ($((TOTAL_WASTED / 1048576)) MB)"
echo ""
echo "Full report: $OUTPUT_FILE"
echo ""

# Show first few duplicate groups
if [ "$DUPLICATE_GROUPS" -gt 0 ]; then
    echo -e "${BLUE}First 3 duplicate groups:${NC}"
    head -3 "$TEMP_DIR/duplicate_hashes.txt" | while IFS= read -r hash; do
        echo ""
        echo "MD5: $hash"
        grep "^$hash|" "$TEMP_DIR/file_hashes.txt" | while IFS='|' read -r h size filepath; do
            size_kb=$((size / 1024))
            echo "  [$size_kb KB] $filepath"
        done
    done
fi

echo ""
echo -e "${YELLOW}To view full report:${NC} cat $OUTPUT_FILE"
