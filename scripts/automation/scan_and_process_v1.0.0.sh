#!/bin/bash

# Scan and Process Documents - Uses GUI for scanning, auto-processes with OCR
# This is a hybrid approach that works around epsonscan2 CLI limitations

OUTPUT_BASE_DIR="/home/dave/ScannedDocuments"
SESSION_DIR="$OUTPUT_BASE_DIR/$(date +%Y-%m-%d_%H-%M-%S)"
SCAN_DIR="$SESSION_DIR/scans"
OCR_LANG="eng"
ENABLE_OCR=true
AUTO_CATEGORIZE=true

# Document Categories
declare -A CATEGORIES=(
    ["Invoice"]="Financial/Invoices"
    ["Receipt"]="Financial/Receipts"
    ["Contract"]="Legal/Contracts"
    ["Report"]="Reports"
    ["Letter"]="Correspondence"
    ["Statement"]="Financial/Statements"
    ["Tax_Document"]="Financial/Tax"
    ["Medical"]="Medical"
    ["Bill"]="Financial/Bills"
    ["Certificate"]="Personal/Certificates"
)

mkdir -p "$SCAN_DIR" "$SESSION_DIR/processed" "$SESSION_DIR/originals"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Scan and Process Documents                   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo -e "${GREEN}Scan folder:${NC} $SCAN_DIR"
echo -e "${GREEN}Output folder:${NC} $SESSION_DIR/processed"
echo

echo -e "${CYAN}Opening scanner GUI...${NC}"
echo -e "${YELLOW}Please scan your documents and save them to:${NC}"
echo -e "${GREEN}$SCAN_DIR${NC}"
echo
echo -e "${YELLOW}When done scanning, close the scanner window and press ENTER${NC}"

# Open simple-scan with the scan directory
cd "$SCAN_DIR"
simple-scan &
SCANNER_PID=$!

# Wait for user to finish
read -p "Press ENTER when done scanning..."

# Kill scanner if still running
kill $SCANNER_PID 2>/dev/null

# Check if any files were scanned
SCANNED_FILES=$(find "$SCAN_DIR" -type f \( -name "*.pdf" -o -name "*.png" -o -name "*.jpg" \) 2>/dev/null)

if [[ -z "$SCANNED_FILES" ]]; then
    echo -e "${YELLOW}No scanned files found in $SCAN_DIR${NC}"
    exit 0
fi

echo -e "\n${CYAN}Processing scanned documents...${NC}\n"

TOTAL=0

# Function to clean filename
clean_filename() {
    echo "$1" | sed 's/[^a-zA-Z0-9 ._-]//g' | tr -s ' ' | xargs | cut -c1-100
}

# Function to extract document info
extract_doc_info() {
    local ocr_text="$1"
    local doc_type=""
    local doc_date=$(date +%Y-%m-%d)

    if echo "$ocr_text" | grep -qi "invoice"; then
        doc_type="Invoice"
    elif echo "$ocr_text" | grep -qi "receipt"; then
        doc_type="Receipt"
    elif echo "$ocr_text" | grep -qi "contract"; then
        doc_type="Contract"
    elif echo "$ocr_text" | grep -qi "report"; then
        doc_type="Report"
    elif echo "$ocr_text" | grep -qi "statement"; then
        doc_type="Statement"
    elif echo "$ocr_text" | grep -qi "tax"; then
        doc_type="Tax_Document"
    elif echo "$ocr_text" | grep -qi "medical"; then
        doc_type="Medical"
    elif echo "$ocr_text" | grep -qi "bill"; then
        doc_type="Bill"
    elif echo "$ocr_text" | grep -qi "certificate"; then
        doc_type="Certificate"
    fi

    local extracted_date=$(echo "$ocr_text" | grep -oE "[0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4}" | head -1)
    if [[ -n "$extracted_date" ]]; then
        doc_date=$(date -d "$extracted_date" +%Y-%m-%d 2>/dev/null || echo "$doc_date")
    fi

    if [[ -n "$doc_type" ]]; then
        echo "${doc_date}_${doc_type}|${doc_type}"
    else
        local first_line=$(echo "$ocr_text" | grep -E '.{5,}' | head -1 | cut -c1-50)
        echo "${doc_date}_$(clean_filename "$first_line")|"
    fi
}

# Process each file
find "$SCAN_DIR" -type f \( -name "*.pdf" -o -name "*.png" -o -name "*.jpg" \) | while read -r file; do
    ((TOTAL++))
    filename=$(basename "$file")
    extension="${filename##*.}"

    echo -e "${CYAN}Processing: $filename${NC}"

    # Perform OCR
    if $ENABLE_OCR && command -v tesseract >/dev/null 2>&1; then
        ocr_text=""

        if [[ "$extension" == "pdf" ]] && command -v pdftotext >/dev/null 2>&1; then
            ocr_text=$(pdftotext -l 3 "$file" - 2>/dev/null)
        elif command -v tesseract >/dev/null 2>&1; then
            ocr_text=$(tesseract "$file" stdout -l "$OCR_LANG" 2>/dev/null)
        fi

        if [[ -n "$ocr_text" ]]; then
            info=$(extract_doc_info "$ocr_text")
            suggested_name=$(echo "$info" | cut -d'|' -f1)
            category=$(echo "$info" | cut -d'|' -f2)

            echo -e "${GREEN}  Identified: $suggested_name${NC}"
            [[ -n "$category" ]] && echo -e "${GREEN}  Category: $category${NC}"
        else
            suggested_name="document_$(date +%Y%m%d_%H%M%S)_$(printf "%03d" $TOTAL)"
            category=""
        fi
    else
        suggested_name="document_$(date +%Y%m%d_%H%M%S)_$(printf "%03d" $TOTAL)"
        category=""
    fi

    # Determine destination
    dest_dir="$SESSION_DIR/processed"
    if $AUTO_CATEGORIZE && [[ -n "$category" ]]; then
        cat_path="${CATEGORIES[$category]}"
        if [[ -n "$cat_path" ]]; then
            dest_dir="$SESSION_DIR/processed/$cat_path"
            mkdir -p "$dest_dir"
        fi
    fi

    # Ensure unique filename
    final_path="$dest_dir/${suggested_name}.${extension}"
    counter=1
    while [[ -f "$final_path" ]]
    do
        final_path="$dest_dir/${suggested_name}_$(printf "%02d" $counter).${extension}"
        counter=$((counter + 1))
    done

    # Move file
    cp "$file" "$final_path"
    cp "$file" "$SESSION_DIR/originals/$(basename "$file")"

    echo -e "${GREEN}  Saved: $final_path${NC}\n"
done

# Cleanup scan folder
rm -rf "$SCAN_DIR"

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              PROCESSING COMPLETE                     ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo -e "${GREEN}Documents processed and organized in:${NC}"
echo -e "${GREEN}$SESSION_DIR/processed${NC}"
echo

# Show summary
if $AUTO_CATEGORIZE; then
    echo -e "${CYAN}Documents by category:${NC}"
    for cat_path in "${CATEGORIES[@]}"; do
        cat_dir="$SESSION_DIR/processed/$cat_path"
        if [[ -d "$cat_dir" ]]; then
            count=$(find "$cat_dir" -type f | wc -l)
            [[ $count -gt 0 ]] && echo -e "  $cat_path: $count"
        fi
    done
fi

uncategorized=$(find "$SESSION_DIR/processed" -maxdepth 1 -type f 2>/dev/null | wc -l)
[[ $uncategorized -gt 0 ]] && echo -e "  Uncategorized: $uncategorized"

echo