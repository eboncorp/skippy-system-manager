#!/bin/bash

# Script to prepare campaign folder for Claude.ai upload
# Converts all files to text-only format and creates organized archives

set -e

PROJECT_DIR="/home/dave/Documents/Government/budgets/RunDaveRun"
CAMPAIGN_DIR="$PROJECT_DIR/campaign"
OUTPUT_DIR="$PROJECT_DIR/campaign_claude_ready"

echo -e "\033[0;34m=== Preparing Campaign Folder for Claude.ai ==={NC}\033[0m"

# Clean and create output directory
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"/{markdown_docs,plugin,other_files}

echo "Processing campaign folder..."

cd "$CAMPAIGN_DIR"

# 1. Copy all markdown files as .txt
echo "  Converting markdown files..."
find . -maxdepth 1 -name "*.md" -type f | while read -r file; do
    basename=$(basename "$file" .md)
    cp "$file" "$OUTPUT_DIR/markdown_docs/${basename}.txt"
done

# 2. Copy text files
echo "  Copying text files..."
find . -maxdepth 1 -name "*.txt" -type f -exec cp {} "$OUTPUT_DIR/other_files/" \;

# 3. Handle the plugin directory
echo "  Processing plugin directory..."
if [ -d "dave-biggers-policy-manager" ]; then
    cd dave-biggers-policy-manager
    find . -type f | while read -r file; do
        ext="${file##*.}"
        # Include code and text files
        if [[ "$ext" =~ ^(php|js|css|md|txt|json|xml|html|htm)$ ]]; then
            # Preserve directory structure
            target_dir="$OUTPUT_DIR/plugin/$(dirname "$file")"
            mkdir -p "$target_dir"

            # Copy with .txt extension for md files, original extension for code
            if [ "$ext" = "md" ]; then
                cp "$file" "$target_dir/$(basename "$file" .md).txt"
            else
                cp "$file" "$target_dir/$(basename "$file")"
            fi
        fi
    done
    cd ..
fi

# 4. Extract and convert existing zip files
echo "  Processing existing zip files..."
for zipfile in *.zip; do
    [ -f "$zipfile" ] || continue

    basename=$(basename "$zipfile" .zip)
    temp_extract="$OUTPUT_DIR/temp_$basename"
    mkdir -p "$temp_extract"

    unzip -q "$zipfile" -d "$temp_extract" 2>/dev/null || true

    # Convert extracted files
    find "$temp_extract" -type f | while read -r file; do
        filename=$(basename "$file")
        ext="${filename##*.}"

        if [[ "$ext" =~ ^(md|txt|json|xml|csv|html|css|js|php|py|sh|yaml|yml)$ ]]; then
            if [ "$ext" = "md" ]; then
                cp "$file" "$OUTPUT_DIR/other_files/${filename%.md}_from_${basename}.txt"
            else
                cp "$file" "$OUTPUT_DIR/other_files/${filename}_from_${basename}"
            fi
        fi
    done

    rm -rf "$temp_extract"
done

# 5. Create organized archives
echo -e "\nCreating archives..."

cd "$OUTPUT_DIR"

# Archive 1: All markdown documents
if [ "$(find markdown_docs -type f 2>/dev/null | wc -l)" -gt 0 ]; then
    cd markdown_docs
    zip -q -r ../campaign_markdown_docs.zip .
    cd ..
    echo "  ✓ campaign_markdown_docs.zip ($(du -sh campaign_markdown_docs.zip | cut -f1))"
fi

# Archive 2: Plugin files
if [ "$(find plugin -type f 2>/dev/null | wc -l)" -gt 0 ]; then
    cd plugin
    zip -q -r ../campaign_plugin.zip .
    cd ..
    echo "  ✓ campaign_plugin.zip ($(du -sh campaign_plugin.zip | cut -f1))"
fi

# Archive 3: Other files
if [ "$(find other_files -type f 2>/dev/null | wc -l)" -gt 0 ]; then
    cd other_files
    zip -q -r ../campaign_other_files.zip .
    cd ..
    echo "  ✓ campaign_other_files.zip ($(du -sh campaign_other_files.zip | cut -f1))"
fi

# Archive 4: Everything combined
zip -q -r campaign_complete.zip markdown_docs plugin other_files 2>/dev/null || true
echo "  ✓ campaign_complete.zip ($(du -sh campaign_complete.zip | cut -f1))"

# Clean up extracted directories
rm -rf markdown_docs plugin other_files

# Create summary
echo -e "\n\033[0;32m=== Conversion Complete ===\033[0m"
echo ""
echo "Output location: $OUTPUT_DIR"
echo ""
echo "Archives created:"
ls -lh *.zip 2>/dev/null | awk '{printf "  %-40s %8s\n", $9, $5}'
echo ""
echo "File counts:"
unzip -l campaign_complete.zip 2>/dev/null | tail -1 | awk '{print "  Total files: " $2}'
echo ""
echo "\033[0;33mRECOMMENDED: Upload campaign_complete.zip to Claude.ai\033[0m"
