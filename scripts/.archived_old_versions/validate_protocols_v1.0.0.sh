#!/bin/bash
# Script Name: validate_protocols
# Version: 1.0.0
# Purpose: Validate protocol files meet standards
# Created: 2025-10-28
# Protocol Reference: /home/dave/skippy/conversations/documentation_standards_protocol.md

PROTOCOL_DIR="/home/dave/skippy/conversations"
ISSUES_FOUND=0

echo "🔍 Protocol Validation Report"
echo "=============================="
echo ""

# Check 1: All protocols have required headers
echo "Checking headers..."
for file in "$PROTOCOL_DIR"/*protocol*.md; do
    [ -f "$file" ] || continue
    basename_file=$(basename "$file")

    if ! grep -q "^**Date Created**:\|^**Created**:" "$file"; then
        echo "❌ Missing Date Created: $basename_file"
        ((ISSUES_FOUND++))
    fi
    if ! grep -q "^**Purpose**:" "$file"; then
        echo "❌ Missing Purpose: $basename_file"
        ((ISSUES_FOUND++))
    fi
done

# Check 2: File naming convention
echo ""
echo "Checking naming conventions..."
for file in "$PROTOCOL_DIR"/*.md; do
    [ -f "$file" ] || continue
    basename_file=$(basename "$file")

    # Check for uppercase letters
    if [[ "$basename_file" =~ [A-Z] ]]; then
        echo "⚠️  Uppercase in filename: $basename_file"
    fi

    # Check for spaces
    if [[ "$basename_file" =~ [[:space:]] ]]; then
        echo "⚠️  Spaces in filename: $basename_file"
    fi
done

# Check 3: Code block completeness
echo ""
echo "Checking code blocks..."
for file in "$PROTOCOL_DIR"/*.md; do
    [ -f "$file" ] || continue
    basename_file=$(basename "$file")

    # Count opening and closing code blocks
    opens=$(grep -c '^```' "$file" 2>/dev/null || echo "0")
    if [ $((opens % 2)) -ne 0 ]; then
        echo "❌ Unclosed code block: $basename_file"
        ((ISSUES_FOUND++))
    fi
done

# Check 4: TODO/FIXME in production
echo ""
echo "Checking for TODOs..."
TODO_FOUND=$(grep -r "TODO\|FIXME\|XXX\|TBD" "$PROTOCOL_DIR" --include="*.md" 2>/dev/null | grep -v "example\|Example" | wc -l)
if [ "$TODO_FOUND" -gt 0 ]; then
    echo "⚠️  Found $TODO_FOUND TODOs/FIXMEs in protocols"
    grep -r "TODO\|FIXME\|XXX\|TBD" "$PROTOCOL_DIR" --include="*.md" 2>/dev/null | grep -v "example\|Example" | head -5
fi

# Check 5: Protocol count
echo ""
echo "Checking protocol inventory..."
PROTOCOL_COUNT=$(find "$PROTOCOL_DIR" -name "*protocol*.md" -type f | wc -l)
echo "Total protocols found: $PROTOCOL_COUNT"

# Summary
echo ""
echo "=============================="
if [ $ISSUES_FOUND -eq 0 ] && [ "$TODO_FOUND" -eq 0 ]; then
    echo "✅ All checks passed!"
    exit 0
else
    if [ $ISSUES_FOUND -gt 0 ]; then
        echo "⚠️  Found $ISSUES_FOUND critical issues"
    fi
    if [ "$TODO_FOUND" -gt 0 ]; then
        echo "⚠️  Found $TODO_FOUND TODOs (review if intentional)"
    fi
    exit 1
fi
