#!/bin/bash
# Quick header check script

cd /home/user/skippy-system-manager/conversations

for f in *protocol*.md; do
  [ -f "$f" ] || continue

  has_version=$(grep -c "^\*\*Version" "$f")
  has_date=$(grep -cE "^\*\*(Last Updated|Date Created|Created)" "$f")
  has_purpose=$(grep -c "^## Purpose\|^## Context" "$f")

  if [ "$has_version" -eq 0 ] || [ "$has_date" -eq 0 ] || [ "$has_purpose" -eq 0 ]; then
    echo "=== $f ==="
    [ "$has_version" -eq 0 ] && echo "  ✗ Missing Version"
    [ "$has_date" -eq 0 ] && echo "  ✗ Missing Date"
    [ "$has_purpose" -eq 0 ] && echo "  ✗ Missing Purpose/Context"
  fi
done
