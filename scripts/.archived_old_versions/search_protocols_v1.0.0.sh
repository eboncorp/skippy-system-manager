#!/bin/bash
# Script Name: search_protocols
# Version: 1.0.0
# Purpose: Search protocol content quickly
# Created: 2025-10-28
# Usage: search_protocols.sh <search_term>

PROTOCOL_DIR="/home/dave/skippy/conversations"
QUERY="$1"

if [ -z "$QUERY" ]; then
    echo "Usage: search_protocols.sh <search_term>"
    echo ""
    echo "Examples:"
    echo "  search_protocols.sh 'database backup'"
    echo "  search_protocols.sh 'WordPress'"
    echo "  search_protocols.sh 'error logging'"
    exit 1
fi

echo "🔍 Searching protocols for: $QUERY"
echo "=================================="
echo ""

# Search with context and color
RESULTS=$(grep -r -i -n -C 2 --color=never "$QUERY" "$PROTOCOL_DIR" --include="*.md" 2>/dev/null)

if [ -z "$RESULTS" ]; then
    echo "No results found for '$QUERY'"
    echo ""
    echo "Try:"
    echo "  - Different keywords"
    echo "  - Broader search terms"
    echo "  - Check spelling"
    exit 0
fi

# Format results
echo "$RESULTS" | while IFS=: read -r file line content; do
    if [ -n "$file" ] && [ -f "$file" ]; then
        protocol_name=$(basename "$file" .md)
        echo "📄 $protocol_name (line $line)"
        echo "   $content"
        echo ""
    fi
done | head -50  # Limit to first 50 matches

# Count total matches
TOTAL_MATCHES=$(echo "$RESULTS" | wc -l)
if [ "$TOTAL_MATCHES" -gt 50 ]; then
    echo "... and $(($TOTAL_MATCHES - 50)) more matches"
    echo ""
fi

echo "Total matches: $TOTAL_MATCHES"
