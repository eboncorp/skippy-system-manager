#!/bin/bash
# Fix Hardcoded Paths
# Version: 1.0.0
# Purpose: Find and fix hardcoded paths in Skippy scripts
# Usage: ./fix_hardcoded_paths_v1.0.0.sh [--dry-run] [--report-only]

set -euo pipefail

# Colors
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[1;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_RESET='\033[0m'

# Configuration
DRY_RUN=false
REPORT_ONLY=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Counters
FILES_SCANNED=0
FILES_WITH_HARDCODED_PATHS=0
TOTAL_REPLACEMENTS=0

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --report-only)
            REPORT_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--dry-run] [--report-only]"
            exit 1
            ;;
    esac
done

#######################################
# Print colored message
# Arguments:
#   $1 - Color
#   $2 - Message
#######################################
print_colored() {
    local color="$1"
    local message="$2"
    echo -e "${color}${message}${COLOR_RESET}"
}

#######################################
# Scan file for hardcoded paths
# Arguments:
#   $1 - File path
# Returns:
#   Number of hardcoded paths found
#######################################
scan_file() {
    local file="$1"
    local count=0

    ((FILES_SCANNED++))

    # Patterns to search for
    local patterns=(
        "/home/dave/skippy"
        "/home/dave/RunDaveRun"
        "/home/dave/GoogleDrive"
        "/home/dave/Skippy"
        "/home/dave/"
    )

    local found=false
    for pattern in "${patterns[@]}"; do
        if grep -q "$pattern" "$file" 2>/dev/null; then
            if [[ "$found" == "false" ]]; then
                print_colored "$COLOR_YELLOW" "\n📁 $file"
                ((FILES_WITH_HARDCODED_PATHS++))
                found=true
            fi

            local matches
            matches=$(grep -n "$pattern" "$file" | head -5)
            echo "$matches" | while IFS= read -r line; do
                print_colored "$COLOR_RED" "  ⚠ $line"
                ((count++))
            done
        fi
    done

    return "$count"
}

#######################################
# Fix hardcoded paths in file
# Arguments:
#   $1 - File path
#######################################
fix_file() {
    local file="$1"
    local backup="${file}.backup"

    if [[ "$DRY_RUN" == "true" ]]; then
        print_colored "$COLOR_BLUE" "  [DRY RUN] Would fix: $file"
        return 0
    fi

    # Create backup
    cp "$file" "$backup"

    # Replacements
    local replacements=0

    # Replace /home/dave/skippy with ${SKIPPY_BASE_PATH}
    if grep -q "/home/dave/skippy" "$file"; then
        sed -i 's|/home/dave/skippy|\${SKIPPY_BASE_PATH}|g' "$file"
        ((replacements++))
    fi

    # Replace /home/dave/RunDaveRun with ${WORDPRESS_BASE_PATH}
    if grep -q "/home/dave/RunDaveRun" "$file"; then
        sed -i 's|/home/dave/RunDaveRun|\${WORDPRESS_BASE_PATH}|g' "$file"
        ((replacements++))
    fi

    # Replace /home/dave/GoogleDrive with ${GDRIVE_MOUNT_PATH:-$HOME/GoogleDrive}
    if grep -q "/home/dave/GoogleDrive" "$file"; then
        sed -i 's|/home/dave/GoogleDrive|\${GDRIVE_MOUNT_PATH:-\$HOME/GoogleDrive}|g' "$file"
        ((replacements++))
    fi

    # Replace /home/dave/Skippy with ${SKIPPY_BASE_PATH}
    if grep -q "/home/dave/Skippy" "$file"; then
        sed -i 's|/home/dave/Skippy|\${SKIPPY_BASE_PATH}|g' "$file"
        ((replacements++))
    fi

    # Replace remaining /home/dave/ with $HOME/
    if grep -q "/home/dave/" "$file"; then
        sed -i 's|/home/dave/|\$HOME/|g' "$file"
        ((replacements++))
    fi

    if ((replacements > 0)); then
        print_colored "$COLOR_GREEN" "  ✓ Fixed $replacements patterns in $file"
        TOTAL_REPLACEMENTS=$((TOTAL_REPLACEMENTS + replacements))

        # Verify bash syntax if it's a shell script
        if [[ "$file" == *.sh ]]; then
            if ! bash -n "$file" 2>/dev/null; then
                print_colored "$COLOR_RED" "  ✗ Syntax error after fix, restoring backup"
                mv "$backup" "$file"
                return 1
            fi
        fi

        # Remove backup if successful
        rm -f "$backup"
    else
        rm -f "$backup"
    fi

    return 0
}

#######################################
# Main function
#######################################
main() {
    print_colored "$COLOR_BLUE" "=================================================="
    print_colored "$COLOR_BLUE" "  Skippy Hardcoded Path Scanner"
    print_colored "$COLOR_BLUE" "=================================================="
    echo ""

    if [[ "$DRY_RUN" == "true" ]]; then
        print_colored "$COLOR_YELLOW" "🔍 Running in DRY RUN mode (no changes will be made)"
    fi

    if [[ "$REPORT_ONLY" == "true" ]]; then
        print_colored "$COLOR_YELLOW" "📊 Running in REPORT ONLY mode"
    fi

    echo ""
    print_colored "$COLOR_BLUE" "Scanning scripts directory..."

    # Find all scripts
    local script_files=()
    while IFS= read -r -d '' file; do
        script_files+=("$file")
    done < <(find "$BASE_DIR/scripts" "$BASE_DIR/lib" "$BASE_DIR/mcp-servers" \
             -type f \( -name "*.sh" -o -name "*.py" \) \
             ! -path "*/archive/*" \
             ! -path "*/.venv/*" \
             ! -path "*/node_modules/*" \
             -print0 2>/dev/null)

    # Scan all files
    for file in "${script_files[@]}"; do
        scan_file "$file" || true
    done

    # Summary
    echo ""
    print_colored "$COLOR_BLUE" "=================================================="
    print_colored "$COLOR_BLUE" "  Scan Summary"
    print_colored "$COLOR_BLUE" "=================================================="
    echo ""
    echo "Files scanned: $FILES_SCANNED"
    echo "Files with hardcoded paths: $FILES_WITH_HARDCODED_PATHS"
    echo ""

    if [[ "$REPORT_ONLY" == "true" ]]; then
        if ((FILES_WITH_HARDCODED_PATHS > 0)); then
            print_colored "$COLOR_YELLOW" "⚠ Found $FILES_WITH_HARDCODED_PATHS files with hardcoded paths"
            print_colored "$COLOR_YELLOW" "Run without --report-only to fix them"
            exit 1
        else
            print_colored "$COLOR_GREEN" "✓ No hardcoded paths found!"
            exit 0
        fi
    fi

    # Ask to fix
    if ((FILES_WITH_HARDCODED_PATHS > 0)) && [[ "$DRY_RUN" == "false" ]]; then
        echo ""
        read -p "Fix these files? (y/n) " -n 1 -r
        echo ""

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_colored "$COLOR_BLUE" "\nFixing files..."

            for file in "${script_files[@]}"; do
                if grep -q -E "/home/dave/(skippy|RunDaveRun|GoogleDrive|Skippy)" "$file" 2>/dev/null; then
                    fix_file "$file" || true
                fi
            done

            echo ""
            print_colored "$COLOR_GREEN" "✓ Fixed $TOTAL_REPLACEMENTS patterns across $FILES_WITH_HARDCODED_PATHS files"
            echo ""
            print_colored "$COLOR_YELLOW" "⚠ Remember to:"
            echo "  1. Test the modified scripts"
            echo "  2. Set SKIPPY_BASE_PATH and WORDPRESS_BASE_PATH in config.env"
            echo "  3. Source config.env in your scripts"
        else
            print_colored "$COLOR_YELLOW" "Aborted by user"
        fi
    elif [[ "$DRY_RUN" == "true" ]] && ((FILES_WITH_HARDCODED_PATHS > 0)); then
        print_colored "$COLOR_YELLOW" "\n⚠ Run without --dry-run to actually fix these files"
    else
        print_colored "$COLOR_GREEN" "\n✓ No hardcoded paths found!"
    fi
}

# Run main function
main
