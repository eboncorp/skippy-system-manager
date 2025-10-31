#!/bin/bash

cd /home/dave/Documents/Government/budgets/RunDaveRun

OUTPUT_DIR="zips_text_output"
mkdir -p "$OUTPUT_DIR/temp"

# Process remaining zip files
for zipfile in zips/*.zip; do
    basename=$(basename "$zipfile" .zip)
    output_file="$OUTPUT_DIR/${basename}_text.zip"

    # Skip if already processed
    if [ -f "$output_file" ]; then
        echo "✓ Already exists: ${basename}_text.zip"
        continue
    fi

    echo "Processing: $basename..."

    # Create temp directory for this zip
    temp_dir="$OUTPUT_DIR/temp/$basename"
    rm -rf "$temp_dir"
    mkdir -p "$temp_dir"

    # Extract
    unzip -q "$zipfile" -d "$temp_dir" 2>/dev/null || true

    # Convert files to .txt
    find "$temp_dir" -type f | while read -r file; do
        filename=$(basename "$file")
        ext="${filename##*.}"

        # Keep text-based files, convert to .txt extension
        if [[ "$ext" =~ ^(md|txt|json|xml|csv|html|css|js|py|sh|yaml|yml)$ ]]; then
            if [ "$ext" != "txt" ]; then
                newname="${filename%.*}.txt"
                mv "$file" "$(dirname "$file")/$newname"
            fi
        else
            # Remove non-text files
            rm -f "$file"
        fi
    done

    # Create zip if files exist
    cd "$temp_dir"
    if [ "$(find . -type f 2>/dev/null | wc -l)" -gt 0 ]; then
        zip -q -r "../../$output_file" . 2>/dev/null
        echo "  ✓ Created: ${basename}_text.zip"
    else
        echo "  ⚠ No text files found"
    fi
    cd - > /dev/null
done

# Create combined archive
echo -e "\nCreating combined archive..."
cd "$OUTPUT_DIR/temp"
zip -q -r "../all_zips_text_combined.zip" . 2>/dev/null
cd - > /dev/null

# Clean up
rm -rf "$OUTPUT_DIR/temp"

echo -e "\n=== Summary ==="
ls -lh "$OUTPUT_DIR"/*.zip | awk '{print $9, "("$5")"}'
