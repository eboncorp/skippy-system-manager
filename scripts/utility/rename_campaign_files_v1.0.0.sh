#!/bin/bash
# Rename all files in campaign directory to lowercase with underscores

cd /home/dave/rundaverun/campaign || exit 1

count=0
for file in *; do
  if [ -f "$file" ]; then
    # Convert to lowercase and replace spaces with underscores
    newname=$(echo "$file" | tr '[:upper:]' '[:lower:]' | sed 's/ /_/g')

    if [ "$file" != "$newname" ]; then
      mv "$file" "$newname"
      echo "✓ $file → $newname"
      ((count++))
    fi
  fi
done

echo ""
echo "Renamed $count files in campaign directory"
