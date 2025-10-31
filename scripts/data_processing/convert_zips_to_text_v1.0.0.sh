#!/bin/bash

# Script to convert all zip files to text-only format and recompress
# For Claude.ai upload preparation

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_DIR="/home/dave/Documents/Government/budgets/RunDaveRun"
ZIPS_DIR="$PROJECT_DIR/zips"
OUTPUT_DIR="$PROJECT_DIR/zips_text_output"
TEMP_DIR="$OUTPUT_DIR/temp"

echo -e "${BLUE}Starting conversion of zip files to text-only format...${NC}"

# Clean up and create directories
rm -rf "$OUTPUT_DIR"
mkdir -p "$TEMP_DIR"

# Process each zip file
cd "$ZIPS_DIR"
for zipfile in *.zip; do
    echo -e "\n${GREEN}Processing: $zipfile${NC}"

    # Create subdirectory for this zip
    ZIP_NAME="${zipfile%.zip}"
    EXTRACT_DIR="$TEMP_DIR/$ZIP_NAME"
    mkdir -p "$EXTRACT_DIR"

    # Extract
    unzip -q "$zipfile" -d "$EXTRACT_DIR" 2>/dev/null || echo "  (some errors ignored)"

    # Convert all files to .txt with text-only content
    find "$EXTRACT_DIR" -type f | while read -r file; do
        filename=$(basename "$file")
        extension="${filename##*.}"
        base="${filename%.*}"

        # Check if it's already a text-based file
        if [[ "$extension" =~ ^(md|txt|json|xml|csv|html|htm|css|js|py|sh|yaml|yml)$ ]]; then
            # Copy with .txt extension
            cp "$file" "$EXTRACT_DIR/${base}.txt"
            # Remove original if not already .txt
            if [ "$extension" != "txt" ]; then
                rm "$file"
            fi
        else
            # For binary or unknown files, just note their existence
            echo "  Skipping binary/unknown file: $filename"
            rm "$file"
        fi
    done

    # Create compressed text-only zip
    cd "$EXTRACT_DIR"
    if [ "$(find . -type f | wc -l)" -gt 0 ]; then
        zip -q -r "$OUTPUT_DIR/${ZIP_NAME}_text.zip" .
        echo -e "  ${GREEN}✓${NC} Created: ${ZIP_NAME}_text.zip"

        # Show file count and size
        FILE_COUNT=$(find . -type f | wc -l)
        SIZE=$(du -sh "$OUTPUT_DIR/${ZIP_NAME}_text.zip" | cut -f1)
        echo "  Files: $FILE_COUNT | Size: $SIZE"
    else
        echo "  No text files found in $zipfile"
    fi
    cd "$ZIPS_DIR"
done

# Create a single combined archive with all text files
echo -e "\n${BLUE}Creating combined archive...${NC}"
cd "$TEMP_DIR"
zip -q -r "$OUTPUT_DIR/all_zips_text_combined.zip" .
COMBINED_SIZE=$(du -sh "$OUTPUT_DIR/all_zips_text_combined.zip" | cut -f1)
echo -e "${GREEN}✓${NC} Created: all_zips_text_combined.zip (Size: $COMBINED_SIZE)"

# Clean up temp directory
rm -rf "$TEMP_DIR"

# Summary
echo -e "\n${BLUE}=== Conversion Complete ===${NC}"
echo -e "Output directory: $OUTPUT_DIR"
echo -e "\nIndividual text archives:"
ls -lh "$OUTPUT_DIR"/*_text.zip 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
echo -e "\nCombined archive:"
ls -lh "$OUTPUT_DIR"/all_zips_text_combined.zip | awk '{print "  " $9 " (" $5 ")"}'

echo -e "\n${GREEN}Ready for upload to Claude.ai!${NC}"
