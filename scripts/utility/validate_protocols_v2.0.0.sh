#!/bin/bash
# Script Name: validate_protocols
# Version: 2.0.0
# Purpose: Validate protocol files meet standards (environment-agnostic)
# Created: 2025-11-10
# Protocol Reference: documentation/protocols/documentation_standards_protocol.md
#
# Changelog:
# v2.0.0 (2025-11-10):
#   - Made paths environment-agnostic
#   - Added duplicate detection
#   - Added cross-reference validation
#   - Check both documentation/protocols/ and conversations/
#   - Improved reporting format
# v1.0.0 (2025-10-28): Initial version

# Configuration
BASE_PATH="${SKIPPY_BASE_PATH:-$(pwd)}"
DOC_PROTOCOLS="$BASE_PATH/documentation/protocols"
CONV_PROTOCOLS="$BASE_PATH/conversations"
ISSUES_FOUND=0
WARNINGS_FOUND=0

# Colors for output (if terminal supports it)
if [ -t 1 ]; then
    RED='\033[0;31m'
    YELLOW='\033[1;33m'
    GREEN='\033[0;32m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    RED=''
    YELLOW=''
    GREEN=''
    BLUE=''
    NC=''
fi

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Protocol Validation Report v2.0.0   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo "Base Path: $BASE_PATH"
echo "Documentation Protocols: $DOC_PROTOCOLS"
echo "Conversations Protocols: $CONV_PROTOCOLS"
echo ""

# Function to check headers
check_headers() {
    local dir=$1
    local location=$2

    echo -e "\n${BLUE}═══ Checking Headers: $location ═══${NC}"

    for file in "$dir"/*protocol*.md; do
        [ -f "$file" ] || continue
        basename_file=$(basename "$file")

        # Skip archived files
        [[ "$file" == *"/archive/"* ]] && continue

        # Check for Version header
        if ! grep -q "^\*\*Version" "$file"; then
            echo -e "${YELLOW}⚠️  Missing Version: $basename_file${NC}"
            ((WARNINGS_FOUND++))
        fi

        # Check for Date header
        if ! grep -q "^\*\*Last Updated\|^\*\*Date Created\|^\*\*Created" "$file"; then
            echo -e "${YELLOW}⚠️  Missing Date: $basename_file${NC}"
            ((WARNINGS_FOUND++))
        fi

        # Check for Purpose/Context
        if ! grep -q "^## Purpose\|^## Context" "$file"; then
            echo -e "${YELLOW}⚠️  Missing Purpose/Context: $basename_file${NC}"
            ((WARNINGS_FOUND++))
        fi
    done
}

# Function to check naming conventions
check_naming() {
    local dir=$1
    local location=$2

    echo -e "\n${BLUE}═══ Checking Naming Conventions: $location ═══${NC}"

    for file in "$dir"/*.md; do
        [ -f "$file" ] || continue
        basename_file=$(basename "$file")

        # Skip archived files and special files
        [[ "$file" == *"/archive/"* ]] && continue
        [[ "$basename_file" =~ ^(README|TEMPLATE|PROTOCOL_INDEX)\.md$ ]] && continue

        # Check for uppercase letters in protocol files
        if [[ "$basename_file" =~ protocol.*\.md$ ]] && [[ "$basename_file" =~ [A-Z] ]]; then
            echo -e "${YELLOW}⚠️  Uppercase in protocol filename: $basename_file${NC}"
            ((WARNINGS_FOUND++))
        fi

        # Check for spaces
        if [[ "$basename_file" =~ [[:space:]] ]]; then
            echo -e "${RED}❌ Spaces in filename: $basename_file${NC}"
            ((ISSUES_FOUND++))
        fi
    done
}

# Function to check code blocks
check_code_blocks() {
    local dir=$1
    local location=$2

    echo -e "\n${BLUE}═══ Checking Code Blocks: $location ═══${NC}"

    for file in "$dir"/*.md; do
        [ -f "$file" ] || continue
        basename_file=$(basename "$file")

        # Skip archived files
        [[ "$file" == *"/archive/"* ]] && continue

        # Count opening and closing code blocks
        opens=$(grep -c '^\`\`\`' "$file" 2>/dev/null || echo "0")
        if [ -z "$opens" ]; then
            opens=0
        fi

        if [ $((opens % 2)) -ne 0 ]; then
            echo -e "${RED}❌ Unclosed code block: $basename_file${NC}"
            ((ISSUES_FOUND++))
        fi
    done
}

# Function to find duplicate protocols
check_duplicates() {
    echo -e "\n${BLUE}═══ Checking for Duplicate Protocols ═══${NC}"

    # Get protocol names from both locations
    doc_protocols=$(find "$DOC_PROTOCOLS" -name "*protocol*.md" -type f ! -path "*/archive/*" 2>/dev/null | xargs -n1 basename | sort)
    conv_protocols=$(find "$CONV_PROTOCOLS" -name "*protocol*.md" -maxdepth 1 -type f 2>/dev/null | xargs -n1 basename | sort)

    # Find duplicates
    duplicates=$(comm -12 <(echo "$doc_protocols") <(echo "$conv_protocols"))

    if [ -n "$duplicates" ]; then
        echo -e "${YELLOW}⚠️  Found duplicate protocols:${NC}"
        echo "$duplicates" | while read dup; do
            echo "   - $dup"
            ((WARNINGS_FOUND++))
        done
    else
        echo -e "${GREEN}✅ No duplicates found${NC}"
    fi
}

# Function to check for TODOs
check_todos() {
    local dir=$1
    local location=$2

    echo -e "\n${BLUE}═══ Checking for TODOs: $location ═══${NC}"

    TODO_FOUND=$(grep -r "TODO\|FIXME\|XXX\|TBD" "$dir" --include="*.md" 2>/dev/null | \
        grep -v "example\|Example\|EXAMPLE\|Template\|template\|TEMPLATE" | \
        grep -v "/archive/" | \
        wc -l)

    if [ "$TODO_FOUND" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Found $TODO_FOUND TODOs/FIXMEs${NC}"
        grep -r "TODO\|FIXME\|XXX\|TBD" "$dir" --include="*.md" 2>/dev/null | \
            grep -v "example\|Example\|EXAMPLE\|Template\|template\|TEMPLATE" | \
            grep -v "/archive/" | \
            head -5 | while read line; do
            echo "   $line"
        done
        if [ "$TODO_FOUND" -gt 5 ]; then
            echo "   ... and $((TODO_FOUND - 5)) more"
        fi
        ((WARNINGS_FOUND+=TODO_FOUND))
    else
        echo -e "${GREEN}✅ No TODOs found${NC}"
    fi
}

# Function to check cross-references
check_cross_references() {
    echo -e "\n${BLUE}═══ Checking Cross-References ═══${NC}"

    local broken=0

    # Check documentation/protocols references
    for file in "$DOC_PROTOCOLS"/*protocol*.md; do
        [ -f "$file" ] || continue

        # Find markdown links
        refs=$(grep -o '\[.*\](.*\.md)' "$file" 2>/dev/null || true)

        if [ -n "$refs" ]; then
            echo "$refs" | while IFS= read -r ref; do
                # Extract the filename
                linked_file=$(echo "$ref" | sed 's/.*(\(.*\))/\1/')

                # Check if it's a relative path
                if [[ ! "$linked_file" =~ ^http ]] && [[ ! "$linked_file" =~ ^/ ]]; then
                    # Try to find the file
                    dir=$(dirname "$file")
                    if [ ! -f "$dir/$linked_file" ] && [ ! -f "$DOC_PROTOCOLS/$linked_file" ] && [ ! -f "$CONV_PROTOCOLS/$linked_file" ]; then
                        echo -e "${YELLOW}⚠️  Broken reference in $(basename $file): $linked_file${NC}"
                        ((broken++))
                    fi
                fi
            done
        fi
    done

    if [ $broken -eq 0 ]; then
        echo -e "${GREEN}✅ All cross-references valid${NC}"
    else
        echo -e "${YELLOW}⚠️  Found $broken potential broken references${NC}"
        ((WARNINGS_FOUND+=broken))
    fi
}

# Function to count protocols
count_protocols() {
    echo -e "\n${BLUE}═══ Protocol Inventory ═══${NC}"

    DOC_COUNT=$(find "$DOC_PROTOCOLS" -name "*protocol*.md" -type f ! -path "*/archive/*" 2>/dev/null | wc -l)
    CONV_COUNT=$(find "$CONV_PROTOCOLS" -name "*protocol*.md" -maxdepth 1 -type f 2>/dev/null | wc -l)
    ARCHIVED_COUNT=$(find "$CONV_PROTOCOLS/archive" -name "*protocol*.md" -type f 2>/dev/null | wc -l)
    TOTAL=$((DOC_COUNT + CONV_COUNT))

    echo "Documentation Protocols: $DOC_COUNT"
    echo "Conversations Protocols: $CONV_COUNT"
    echo "Archived Protocols: $ARCHIVED_COUNT"
    echo -e "${GREEN}Total Active Protocols: $TOTAL${NC}"
}

# Function to calculate header compliance
calculate_compliance() {
    echo -e "\n${BLUE}═══ Header Compliance Report ═══${NC}"

    # Documentation protocols
    doc_total=$(find "$DOC_PROTOCOLS" -name "*protocol*.md" -type f ! -path "*/archive/*" 2>/dev/null | wc -l)
    doc_compliant=0

    for file in "$DOC_PROTOCOLS"/*protocol*.md; do
        [ -f "$file" ] || continue
        if grep -q "^\*\*Version" "$file" && grep -q "^\*\*Last Updated\|^\*\*Date Created" "$file"; then
            ((doc_compliant++))
        fi
    done

    # Conversations protocols
    conv_total=$(find "$CONV_PROTOCOLS" -name "*protocol*.md" -maxdepth 1 -type f 2>/dev/null | wc -l)
    conv_compliant=0

    for file in "$CONV_PROTOCOLS"/*protocol*.md; do
        [ -f "$file" ] || continue
        [[ "$file" == *"/archive/"* ]] && continue
        if grep -q "^\*\*Version" "$file" && grep -q "^\*\*Last Updated\|^\*\*Date Created" "$file"; then
            ((conv_compliant++))
        fi
    done

    # Calculate percentages
    if [ $doc_total -gt 0 ]; then
        doc_percent=$((100 * doc_compliant / doc_total))
        echo -e "Documentation: ${GREEN}$doc_compliant/$doc_total ($doc_percent%)${NC}"
    fi

    if [ $conv_total -gt 0 ]; then
        conv_percent=$((100 * conv_compliant / conv_total))
        if [ $conv_percent -lt 50 ]; then
            echo -e "Conversations: ${YELLOW}$conv_compliant/$conv_total ($conv_percent%)${NC}"
        else
            echo -e "Conversations: ${GREEN}$conv_compliant/$conv_total ($conv_percent%)${NC}"
        fi
    fi

    overall_total=$((doc_total + conv_total))
    overall_compliant=$((doc_compliant + conv_compliant))
    if [ $overall_total -gt 0 ]; then
        overall_percent=$((100 * overall_compliant / overall_total))
        echo -e "Overall: ${GREEN}$overall_compliant/$overall_total ($overall_percent%)${NC}"
    fi
}

# Main validation sequence

# Check if directories exist
if [ ! -d "$DOC_PROTOCOLS" ] && [ ! -d "$CONV_PROTOCOLS" ]; then
    echo -e "${RED}❌ Error: No protocol directories found!${NC}"
    echo "   Expected: $DOC_PROTOCOLS or $CONV_PROTOCOLS"
    exit 1
fi

# Run all checks
count_protocols

if [ -d "$DOC_PROTOCOLS" ]; then
    check_headers "$DOC_PROTOCOLS" "documentation/protocols"
    check_naming "$DOC_PROTOCOLS" "documentation/protocols"
    check_code_blocks "$DOC_PROTOCOLS" "documentation/protocols"
    check_todos "$DOC_PROTOCOLS" "documentation/protocols"
fi

if [ -d "$CONV_PROTOCOLS" ]; then
    check_headers "$CONV_PROTOCOLS" "conversations"
    check_naming "$CONV_PROTOCOLS" "conversations"
    check_code_blocks "$CONV_PROTOCOLS" "conversations"
    check_todos "$CONV_PROTOCOLS" "conversations"
fi

check_duplicates
check_cross_references
calculate_compliance

# Summary
echo ""
echo -e "${BLUE}═════════════════════════════════════════${NC}"
echo -e "${BLUE}             SUMMARY                      ${NC}"
echo -e "${BLUE}═════════════════════════════════════════${NC}"

if [ $ISSUES_FOUND -eq 0 ] && [ $WARNINGS_FOUND -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo -e "${GREEN}✅ No issues found${NC}"
    echo -e "${GREEN}✅ No warnings${NC}"
    exit 0
else
    if [ $ISSUES_FOUND -gt 0 ]; then
        echo -e "${RED}❌ Found $ISSUES_FOUND critical issues${NC}"
    fi
    if [ $WARNINGS_FOUND -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Found $WARNINGS_FOUND warnings${NC}"
    fi

    echo ""
    echo "Next steps:"
    if [ $WARNINGS_FOUND -gt 50 ]; then
        echo "  1. Standardize headers in conversations/ protocols"
    fi
    if [ $ISSUES_FOUND -gt 0 ]; then
        echo "  2. Fix critical issues (spaces in filenames, unclosed code blocks)"
    fi
    echo "  3. Review and address TODOs"
    echo "  4. Verify cross-references"

    exit 1
fi
