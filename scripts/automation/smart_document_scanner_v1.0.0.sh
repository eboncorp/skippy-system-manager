#!/bin/bash
# Smart Document Scanner with OCR-based Auto-naming
# Scans documents, performs OCR, and names them based on content

# Configuration
SCANNER_DEVICE="brother4:net1;dev1"  # Brother MFC-7860DW
ADF_CAPACITY=35  # Brother MFC-7860DW ADF holds 35 sheets
OUTPUT_BASE_DIR="/home/dave/ScannedDocuments"
SESSION_DIR="$OUTPUT_BASE_DIR/$(date +%Y-%m-%d_%H-%M-%S)"
RESOLUTION=300  # DPI (150, 200, 300, 600) - 300 is optimal for OCR
MODE="Color"    # Color, Gray, or Lineart
FORMAT="pdf"    # pdf, png, jpg, or tiff

# OCR Configuration
OCR_LANG="eng"  # OCR language (eng, fra, deu, spa, etc.)
MAX_FILENAME_LENGTH=100  # Maximum characters in filename
ENABLE_OCR=true  # Set to false to disable OCR naming

# Create output directory
mkdir -p "$SESSION_DIR/temp" "$SESSION_DIR/processed"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="$SESSION_DIR/scan.log"
OCR_LOG="$SESSION_DIR/ocr_results.txt"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      Smart Document Scanner with OCR                 ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo -e "${GREEN}Scanner:${NC} Brother MFC-7860DW (ADF: $ADF_CAPACITY sheets)"
echo -e "${GREEN}Output:${NC} $SESSION_DIR"
echo -e "${GREEN}OCR:${NC} $(if $ENABLE_OCR; then echo "Enabled - Auto-naming active"; else echo "Disabled"; fi)"
echo -e "${GREEN}Resolution:${NC} $RESOLUTION DPI | ${GREEN}Mode:${NC} $MODE | ${GREEN}Format:${NC} $FORMAT"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}\n"

# Counter for total documents scanned
TOTAL_SCANNED=0
BATCH_NUMBER=1
declare -A DOCUMENT_NAMES  # Associative array to store document names

# Function to check dependencies
check_dependencies() {
    local missing_deps=()

    # Check for tesseract
    if ! command -v tesseract >/dev/null 2>&1; then
        missing_deps+=("tesseract-ocr")
    fi

    # Check for ImageMagick convert
    if ! command -v convert >/dev/null 2>&1; then
        missing_deps+=("imagemagick")
    fi

    # Check for PDF tools
    if ! command -v pdftotext >/dev/null 2>&1; then
        missing_deps+=("poppler-utils")
    fi

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        echo -e "${YELLOW}Missing optional dependencies for full functionality:${NC}"
        for dep in "${missing_deps[@]}"; do
            echo -e "  • $dep"
        done
        echo -e "${CYAN}Install with: sudo apt install ${missing_deps[*]}${NC}"
        echo -e "${YELLOW}Continuing with limited functionality...${NC}\n"

        # Disable OCR if tesseract is missing
        if [[ " ${missing_deps[@]} " =~ " tesseract-ocr " ]]; then
            ENABLE_OCR=false
            echo -e "${YELLOW}OCR disabled due to missing tesseract${NC}\n"
        fi
    fi
}

# Function to clean text for filename
clean_filename() {
    local text="$1"

    # Remove special characters, keep alphanumeric, spaces, and basic punctuation
    local cleaned=$(echo "$text" | sed 's/[^a-zA-Z0-9 ._-]//g')

    # Replace multiple spaces with single space
    cleaned=$(echo "$cleaned" | tr -s ' ')

    # Trim spaces
    cleaned=$(echo "$cleaned" | xargs)

    # Limit length
    if [[ ${#cleaned} -gt $MAX_FILENAME_LENGTH ]]; then
        cleaned="${cleaned:0:$MAX_FILENAME_LENGTH}"
    fi

    # If empty after cleaning, return empty
    [[ -z "$cleaned" ]] && echo "" || echo "$cleaned"
}

# Function to extract meaningful title from OCR text
extract_document_title() {
    local ocr_text="$1"
    local doc_type=""
    local doc_date=""
    local doc_title=""

    # Extract first few lines for title detection
    local first_lines=$(echo "$ocr_text" | head -10)

    # Try to identify document type
    if echo "$ocr_text" | grep -qi "invoice"; then
        doc_type="Invoice"
        # Try to extract invoice number
        local invoice_num=$(echo "$ocr_text" | grep -oiE "invoice[[:space:]]*#?[[:space:]]*[0-9]+" | head -1 | grep -oE "[0-9]+$")
        [[ -n "$invoice_num" ]] && doc_title="${doc_title}_${invoice_num}"
    elif echo "$ocr_text" | grep -qi "receipt"; then
        doc_type="Receipt"
    elif echo "$ocr_text" | grep -qi "contract\|agreement"; then
        doc_type="Contract"
    elif echo "$ocr_text" | grep -qi "report"; then
        doc_type="Report"
    elif echo "$ocr_text" | grep -qi "letter"; then
        doc_type="Letter"
    elif echo "$ocr_text" | grep -qi "memo\|memorandum"; then
        doc_type="Memo"
    elif echo "$ocr_text" | grep -qi "statement"; then
        doc_type="Statement"
    elif echo "$ocr_text" | grep -qi "tax"; then
        doc_type="Tax_Document"
    elif echo "$ocr_text" | grep -qi "medical\|doctor\|patient"; then
        doc_type="Medical"
    elif echo "$ocr_text" | grep -qi "bank\|financial"; then
        doc_type="Financial"
    fi

    # Try to extract date (multiple formats)
    local extracted_date=$(echo "$ocr_text" | grep -oE "([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})|([0-9]{4}[/-][0-9]{1,2}[/-][0-9]{1,2})|([A-Za-z]+ [0-9]{1,2},? [0-9]{4})" | head -1)
    if [[ -n "$extracted_date" ]]; then
        # Convert date to standard format (YYYY-MM-DD)
        doc_date=$(date -d "$extracted_date" +%Y-%m-%d 2>/dev/null || echo "$extracted_date" | tr '/' '-')
    fi

    # Extract company/organization name (look for common patterns)
    local company=$(echo "$first_lines" | grep -oE "^[A-Z][A-Za-z0-9 &,.\-']+" | head -1 | cut -d' ' -f1-3)

    # Extract first meaningful line as title if no type detected
    if [[ -z "$doc_type" ]]; then
        # Get first non-empty line with more than 3 characters
        doc_title=$(echo "$first_lines" | grep -E '.{3,}' | head -1 | cut -c1-50)
        doc_title=$(clean_filename "$doc_title")
    fi

    # Construct filename
    local filename=""
    [[ -n "$doc_date" ]] && filename="${doc_date}_"
    [[ -n "$doc_type" ]] && filename="${filename}${doc_type}"
    [[ -n "$company" ]] && filename="${filename}_$(clean_filename "$company")"
    [[ -z "$filename" && -n "$doc_title" ]] && filename="$doc_title"

    # If still empty, use first few words
    if [[ -z "$filename" ]]; then
        filename=$(echo "$first_lines" | tr '\n' ' ' | cut -d' ' -f1-5)
        filename=$(clean_filename "$filename")
    fi

    echo "$filename"
}

# Function to perform OCR on a document
perform_ocr() {
    local input_file="$1"
    local output_name="$2"

    if ! $ENABLE_OCR; then
        echo "$output_name"
        return
    fi

    echo -e "${CYAN}  Performing OCR analysis...${NC}"

    local temp_text="$SESSION_DIR/temp/ocr_temp.txt"
    local ocr_successful=false
    local ocr_text=""

    # Perform OCR based on file type
    if [[ "$input_file" == *.pdf ]]; then
        # Try pdftotext first (faster and more accurate for text PDFs)
        if command -v pdftotext >/dev/null 2>&1; then
            pdftotext "$input_file" "$temp_text" 2>/dev/null
            if [[ -s "$temp_text" ]]; then
                ocr_text=$(cat "$temp_text")
                ocr_successful=true
            fi
        fi

        # If pdftotext didn't work, convert PDF to image and use tesseract
        if ! $ocr_successful && command -v convert >/dev/null 2>&1 && command -v tesseract >/dev/null 2>&1; then
            convert -density 300 "$input_file[0]" "$SESSION_DIR/temp/temp_page.png" 2>/dev/null
            if [[ -f "$SESSION_DIR/temp/temp_page.png" ]]; then
                tesseract "$SESSION_DIR/temp/temp_page.png" "$SESSION_DIR/temp/ocr_result" -l "$OCR_LANG" 2>/dev/null
                if [[ -f "$SESSION_DIR/temp/ocr_result.txt" ]]; then
                    ocr_text=$(cat "$SESSION_DIR/temp/ocr_result.txt")
                    ocr_successful=true
                    rm -f "$SESSION_DIR/temp/temp_page.png" "$SESSION_DIR/temp/ocr_result.txt"
                fi
            fi
        fi
    else
        # For image files, use tesseract directly
        if command -v tesseract >/dev/null 2>&1; then
            tesseract "$input_file" "$SESSION_DIR/temp/ocr_result" -l "$OCR_LANG" 2>/dev/null
            if [[ -f "$SESSION_DIR/temp/ocr_result.txt" ]]; then
                ocr_text=$(cat "$SESSION_DIR/temp/ocr_result.txt")
                ocr_successful=true
                rm -f "$SESSION_DIR/temp/ocr_result.txt"
            fi
        fi
    fi

    # Clean up temp file
    rm -f "$temp_text"

    if $ocr_successful && [[ -n "$ocr_text" ]]; then
        # Extract title from OCR text
        local suggested_name=$(extract_document_title "$ocr_text")

        if [[ -n "$suggested_name" ]]; then
            echo -e "${GREEN}  ✓ Document identified: $suggested_name${NC}"

            # Log OCR results
            {
                echo "===== Document: $output_name ====="
                echo "Suggested name: $suggested_name"
                echo "First 500 chars of OCR:"
                echo "${ocr_text:0:500}"
                echo ""
            } >> "$OCR_LOG"

            echo "$suggested_name"
        else
            echo -e "${YELLOW}  ⚠ Could not extract meaningful title${NC}"
            echo "$output_name"
        fi
    else
        echo -e "${YELLOW}  ⚠ OCR failed or no text found${NC}"
        echo "$output_name"
    fi
}

# Function to scan and process documents
scan_and_process() {
    local batch_dir="$SESSION_DIR/temp/batch_$(printf "%03d" $BATCH_NUMBER)"
    mkdir -p "$batch_dir"

    echo -e "\n${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Batch #$BATCH_NUMBER${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}Load up to $ADF_CAPACITY documents into the ADF${NC}"
    echo -e "${YELLOW}Press ENTER when ready to scan, or 'q' to quit${NC}"

    read -r response
    if [[ "$response" == "q" ]]; then
        return 1
    fi

    echo -e "\n${CYAN}Starting batch scan...${NC}"
    log_message "Starting batch #$BATCH_NUMBER"

    # Scan documents
    local source_option="Automatic Document Feeder"
    local available_sources=$(scanimage -d "$SCANNER_DEVICE" --help 2>/dev/null | grep -A 10 "^\-\-source" | grep -E "^\s+\w")

    if echo "$available_sources" | grep -q "ADF"; then
        source_option="ADF"
    fi

    # Scan to temporary files first
    echo -e "${CYAN}Scanning documents...${NC}"
    scanimage -d "$SCANNER_DEVICE" \
        --source "$source_option" \
        --resolution "$RESOLUTION" \
        --mode "$MODE" \
        --batch="$batch_dir/scan_%04d.pnm" \
        --batch-start=1 \
        --progress 2>&1 | while IFS= read -r line; do
            if [[ "$line" =~ "Scanning page" ]]; then
                page_num=$(echo "$line" | grep -oP '\d+')
                echo -e "${GREEN}→ Scanning page $page_num${NC}"
            elif [[ "$line" =~ "batch aborted" ]] || [[ "$line" =~ "Document feeder out of documents" ]]; then
                echo -e "${YELLOW}Scanning complete${NC}"
            fi
        done

    # Process each scanned document
    echo -e "\n${CYAN}Processing scanned documents...${NC}"
    local scan_count=0

    for scan_file in "$batch_dir"/scan_*.pnm; do
        if [[ ! -f "$scan_file" ]]; then
            continue
        fi

        scan_count=$((scan_count + 1))
        TOTAL_SCANNED=$((TOTAL_SCANNED + 1))

        echo -e "\n${MAGENTA}Processing document $scan_count:${NC}"

        # Convert to final format
        local temp_output="$SESSION_DIR/temp/temp_$(printf "%04d" $TOTAL_SCANNED).$FORMAT"

        if [[ "$FORMAT" == "pdf" ]]; then
            if command -v convert >/dev/null 2>&1; then
                convert "$scan_file" "$temp_output" 2>/dev/null
            else
                cp "$scan_file" "${temp_output%.pdf}.pnm"
                temp_output="${temp_output%.pdf}.pnm"
            fi
        else
            convert "$scan_file" "$temp_output" 2>/dev/null || cp "$scan_file" "$temp_output"
        fi

        # Perform OCR and get suggested filename
        local base_name="document_$(printf "%04d" $TOTAL_SCANNED)"
        local suggested_name=$(perform_ocr "$temp_output" "$base_name")

        # Ensure unique filename
        local final_name="$suggested_name"
        local counter=1
        while [[ -f "$SESSION_DIR/processed/${final_name}.$FORMAT" ]]; do
            final_name="${suggested_name}_$(printf "%02d" $counter)"
            counter=$((counter + 1))
        done

        # Move to processed folder with final name
        local final_path="$SESSION_DIR/processed/${final_name}.$FORMAT"
        mv "$temp_output" "$final_path"

        # Store document name mapping
        DOCUMENT_NAMES["$base_name"]="$final_name"

        echo -e "${GREEN}✓ Saved as: ${final_name}.$FORMAT${NC}"

        # Clean up temporary scan file
        rm -f "$scan_file"
    done

    # Clean up
    rmdir "$batch_dir" 2>/dev/null

    echo -e "\n${GREEN}Batch #$BATCH_NUMBER complete: $scan_count documents processed${NC}"
    log_message "Batch #$BATCH_NUMBER complete: $scan_count documents"

    BATCH_NUMBER=$((BATCH_NUMBER + 1))
    return 0
}

# Function to generate final report
generate_report() {
    echo -e "\n${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║              Smart Scan Summary                      ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
    echo -e "${GREEN}Total documents:${NC} $TOTAL_SCANNED"
    echo -e "${GREEN}Output folder:${NC} $SESSION_DIR/processed"

    if [[ $TOTAL_SCANNED -gt 0 ]]; then
        echo -e "\n${CYAN}Document Names:${NC}"

        # Create detailed report
        local report_file="$SESSION_DIR/scan_report.txt"
        {
            echo "Smart Document Scan Report"
            echo "=========================="
            echo "Date: $(date)"
            echo "Total Documents: $TOTAL_SCANNED"
            echo "OCR Enabled: $ENABLE_OCR"
            echo ""
            echo "Documents Processed:"
            echo "-------------------"
        } > "$report_file"

        # List all documents with their names
        for file in "$SESSION_DIR/processed"/*; do
            if [[ -f "$file" ]]; then
                local basename=$(basename "$file")
                local size=$(du -h "$file" | cut -f1)
                echo "  • $basename ($size)"
                echo "$basename - Size: $size" >> "$report_file"
            fi
        done | head -20

        if [[ $TOTAL_SCANNED -gt 20 ]]; then
            echo "  ... and $((TOTAL_SCANNED - 20)) more"
        fi

        # Total size
        local total_size=$(du -sh "$SESSION_DIR/processed" 2>/dev/null | cut -f1)
        echo -e "\n${GREEN}Total size:${NC} $total_size"
        echo "" >> "$report_file"
        echo "Total Size: $total_size" >> "$report_file"

        echo -e "\n${GREEN}Reports generated:${NC}"
        echo "  • Scan report: $report_file"
        [[ -f "$OCR_LOG" ]] && echo "  • OCR details: $OCR_LOG"
        echo "  • Scan log: $LOG_FILE"
    fi
}

# Main execution
check_dependencies

echo -e "\n${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Ready to begin smart scanning${NC}"
echo -e "${YELLOW}Documents will be automatically named based on content${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}\n"

# Main scanning loop
while true; do
    if ! scan_and_process; then
        break
    fi

    echo -e "\n${BLUE}Continue with another batch?${NC}"
    echo -e "${YELLOW}Load more documents and press ENTER, or 'q' to finish${NC}"
    read -r continue_response

    if [[ "$continue_response" == "q" ]]; then
        break
    fi
done

# Clean up temp directory
rm -rf "$SESSION_DIR/temp"

# Generate final report
if [[ $TOTAL_SCANNED -gt 0 ]]; then
    generate_report

    echo -e "\n${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║         Smart scanning complete!                     ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
    echo -e "${GREEN}Documents saved to: $SESSION_DIR/processed${NC}"
    echo -e "${GREEN}Documents were automatically named based on content${NC}"
else
    echo -e "\n${YELLOW}No documents were scanned${NC}"
fi