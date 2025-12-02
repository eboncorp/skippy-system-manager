#!/bin/bash
# Fix unclosed code blocks in conversations/ files

cd /home/user/skippy-system-manager/conversations

fixed=0
errors=0

for file in *.md; do
  [ -f "$file" ] || continue

  # Count opening code blocks
  opens=$(grep -c '^\`\`\`' "$file" 2>/dev/null || echo "0")

  # Check if odd number (unclosed)
  if [ $((opens % 2)) -ne 0 ]; then
    echo "Fixing: $file (has $opens code blocks)"

    # Add closing code block at end of file
    echo '```' >> "$file"

    ((fixed++))
  fi
done

echo ""
echo "Summary:"
echo "  Fixed: $fixed files"
echo "  Errors: $errors files"
