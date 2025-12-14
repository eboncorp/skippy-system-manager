#!/bin/bash

# Epson V39 Smart Document Scanner with OCR-based Auto-naming and Organization
# Features: Auto document detection, OCR naming, categorization, and network sharing

# Configuration
SCANNER_DEVICE=""  # Will be auto-detected for Epson V39
OUTPUT_BASE_DIR="/home/dave/ScannedDocuments"
SESSION_DIR="$OUTPUT_BASE_DIR/$(date +%Y-%m-%d_%H-%M-%S)"
RESOLUTION=300  # DPI (150, 200, 300, 600) - 300 is optimal for OCR
MODE="Color"    # Color, Gray, or Lineart
FORMAT="pdf"    # pdf, png, jpg, or tiff

# OCR Configuration
OCR_LANG="eng"  # OCR language (eng, fra, deu, spa, etc.)
MAX_FILENAME_LENGTH=100  # Maximum characters in filename
ENABLE_OCR=true  # Set to false to disable OCR naming
AUTO_CATEGORIZE=true  # Automatically organize into category folders

# Document Categories
declare -A CATEGORIES=(
    ["Invoice"]="Financial/Invoices"
    ["Receipt"]="Financial/Receipts"
    ["Contract"]="Legal/Contracts"
    ["Agreement"]="Legal/Agreements"
    ["Report"]="Reports"
    ["Letter"]="Correspondence"
    ["Memo"]="Correspondence/Memos"
    ["Statement"]="Financial/Statements"
    ["Tax_Document"]="Financial/Tax"
    ["Medical"]="Medical"
    ["Financial"]="Financial/General"
    ["Insurance"]="Insurance"
    ["Bill"]="Financial/Bills"
    ["ID_Document"]="Personal/ID"
    ["Certificate"]="Personal/Certificates"
)

# Create output directories
mkdir -p "$SESSION_DIR/temp" "$SESSION_DIR/processed" "$SESSION_DIR/originals"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Log files
LOG_FILE="$SESSION_DIR/scan.log"
OCR_LOG="$SESSION_DIR/ocr_results.txt"
INVENTORY_FILE="$SESSION_DIR/document_inventory.csv"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Initialize inventory file
echo "Timestamp,Original_Name,Final_Name,Category,OCR_Status,File_Path,File_Size,Pages" > "$INVENTORY_FILE"

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Epson V39 Smart Document Scanner with OCR          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo -e "${GREEN}Output:${NC} $SESSION_DIR"
echo -e "${GREEN}OCR:${NC} $(if $ENABLE_OCR; then echo "Enabled - Auto-naming active"; else echo "Disabled"; fi)"
echo -e "${GREEN}Auto-Categorize:${NC} $(if $AUTO_CATEGORIZE; then echo "Enabled"; else echo "Disabled"; fi)"
echo -e "${GREEN}Resolution:${NC} $RESOLUTION DPI | ${GREEN}Mode:${NC} $MODE | ${GREEN}Format:${NC} $FORMAT"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}\n"

# Counter for total documents scanned
TOTAL_SCANNED=0
declare -A DOCUMENT_NAMES  # Associative array to store document names

# Function to detect Epson V39 scanner
detect_epson_scanner() {
    echo -e "${CYAN}Detecting Epson V39 scanner...${NC}"

    # Try to find Epson scanner (with timeout)
    local scanners=$(timeout 15 scanimage -L 2>/dev/null)

    # Look for Epson V39 or similar
    if echo "$scanners" | grep -qi "epson\|v39\|perfection"; then
        # Extract device name
        SCANNER_DEVICE=$(echo "$scanners" | grep -i "epson\|v39\|perfection" | sed -n "s/device \`\([^']*\)'.*/\1/p" | head -1)

        if [[ -n "$SCANNER_DEVICE" ]]; then
            echo -e "${GREEN}✓ Found Epson scanner: $SCANNER_DEVICE${NC}"
            return 0
        fi
    fi

    # Try alternative detection methods
    if [[ -z "$SCANNER_DEVICE" ]]; then
        # Check for epsonscan2 backend
        SCANNER_DEVICE=$(echo "$scanners" | grep "epsonscan2:" | sed -n "s/device \`\([^']*\)'.*/\1/p" | head -1)
    fi

    if [[ -z "$SCANNER_DEVICE" ]]; then
        # Check for epson2 backend
        SCANNER_DEVICE=$(echo "$scanners" | grep "epson2:" | sed -n "s/device \`\([^']*\)'.*/\1/p" | head -1)
    fi

    if [[ -z "$SCANNER_DEVICE" ]]; then
        # Check for USB scanner
        SCANNER_DEVICE=$(echo "$scanners" | grep "usb:" | sed -n "s/device \`\([^']*\)'.*/\1/p" | head -1)
    fi

    if [[ -n "$SCANNER_DEVICE" ]]; then
        echo -e "${GREEN}✓ Found scanner: $SCANNER_DEVICE${NC}"
        return 0
    else
        echo -e "${RED}✗ No scanner detected. Please check connection.${NC}"
        echo -e "${YELLOW}Available devices:${NC}"
        scanimage -L
        return 1
    fi
}

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
        if [[ " ${missing_deps[*]} " =~ " tesseract-ocr " ]]; then
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

# Function to extract meaningful title and category from OCR text
extract_document_info() {
    local ocr_text="$1"
    local doc_type=""
    local doc_date=""
    local doc_title=""
    local doc_company=""

    # Extract first few lines for title detection
    local first_lines=$(echo "$ocr_text" | head -10)

    # Try to identify document type and extract relevant information
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
    elif echo "$ocr_text" | grep -qi "tax\|1099\|w-2\|1040"; then
        doc_type="Tax_Document"
    elif echo "$ocr_text" | grep -qi "medical\|doctor\|patient\|prescription"; then
        doc_type="Medical"
    elif echo "$ocr_text" | grep -qi "insurance\|policy\|claim"; then
        doc_type="Insurance"
    elif echo "$ocr_text" | grep -qi "bill\|amount due\|payment"; then
        doc_type="Bill"
    elif echo "$ocr_text" | grep -qi "driver.*license\|passport\|social security"; then
        doc_type="ID_Document"
    elif echo "$ocr_text" | grep -qi "certificate\|certification\|diploma"; then
        doc_type="Certificate"
    elif echo "$ocr_text" | grep -qi "bank\|financial\|account"; then
        doc_type="Financial"
    fi

    # Try to extract company/organization name
    # Look for common patterns like "From:", company names in headers, etc.
    local company=$(echo "$first_lines" | grep -oE "^[A-Z][A-Za-z0-9 &,.-]{2,30}$" | head -1)
    if [[ -n "$company" ]]; then
        doc_company=$(clean_filename "$company")
    fi

    # Try to extract date (multiple formats)
    local extracted_date=$(echo "$ocr_text" | grep -oE "([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})|([0-9]{4}[/-][0-9]{1,2}[/-][0-9]{1,2})|([A-Za-z]+ [0-9]{1,2},? [0-9]{4})" | head -1)
    if [[ -n "$extracted_date" ]]; then
        # Convert date to standard format (YYYY-MM-DD)
        doc_date=$(date -d "$extracted_date" +%Y-%m-%d 2>/dev/null || echo "$extracted_date" | tr '/' '-')
    fi

    # If no date found, use today's date
    [[ -z "$doc_date" ]] && doc_date=$(date +%Y-%m-%d)

    # Build filename
    local filename=""
    if [[ -n "$doc_type" ]]; then
        filename="${doc_date}_${doc_type}"
        [[ -n "$doc_company" ]] && filename="${filename}_${doc_company}"
        [[ -n "$doc_title" ]] && filename="${filename}${doc_title}"
    else
        # Fallback: use first meaningful line from OCR
        local first_meaningful=$(echo "$ocr_text" | grep -E "^.{5,}" | head -1)
        if [[ -n "$first_meaningful" ]]; then
            filename="${doc_date}_$(clean_filename "$first_meaningful" | cut -c1-50)"
        fi
    fi

    # Return both filename and category
    echo "${filename}|${doc_type}"
}

# Function to perform OCR and get document name
perform_ocr_naming() {
    local input_file="$1"
    local output_name="$2"
    local ocr_text=""
    local ocr_successful=false

    echo -e "${CYAN}  Performing OCR analysis...${NC}"

    local temp_text="$SESSION_DIR/temp/ocr_temp.txt"

    # Handle different file types
    if [[ "$input_file" =~ \.pdf$ ]]; then
        # For PDF files, try pdftotext first (faster)
        if command -v pdftotext >/dev/null 2>&1; then
            pdftotext -l 3 "$input_file" "$temp_text" 2>/dev/null
            if [[ -s "$temp_text" ]]; then
                ocr_text=$(cat "$temp_text")
                ocr_successful=true
            fi
        fi

        # If pdftotext didn't work, convert PDF to image and use tesseract
        if ! $ocr_successful && command -v convert >/dev/null 2>&1 && command -v tesseract >/dev/null 2>&1; then
            convert -density 300 "${input_file}[0]" "$SESSION_DIR/temp/temp_page.png" 2>/dev/null
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
        # Extract title and category from OCR text
        local info=$(extract_document_info "$ocr_text")
        local suggested_name=$(echo "$info" | cut -d'|' -f1)
        local doc_category=$(echo "$info" | cut -d'|' -f2)

        if [[ -n "$suggested_name" ]]; then
            echo -e "${GREEN}  ✓ Document identified: $suggested_name${NC}"
            [[ -n "$doc_category" ]] && echo -e "${GREEN}    Category: $doc_category${NC}"

            # Log OCR results
            {
                echo "===== Document: $output_name ====="
                echo "Suggested name: $suggested_name"
                echo "Category: $doc_category"
                echo "First 500 chars of OCR:"
                echo "${ocr_text:0:500}"
                echo ""
            } >> "$OCR_LOG"

            echo "${suggested_name}|${doc_category}"
        else
            echo -e "${YELLOW}  ⚠ Could not extract meaningful title${NC}"
            echo "${output_name}|"
        fi
    else
        echo -e "${YELLOW}  ⚠ OCR failed or no text found${NC}"
        echo "${output_name}|"
    fi
}

# Function to scan single document
scan_single_document() {
    local doc_num=$1
    local scan_file="$SESSION_DIR/temp/scan_$(printf "%04d" $doc_num)"

    echo -e "\n${CYAN}Scanning document #$doc_num...${NC}"

    # Perform the scan
    scanimage -d "$SCANNER_DEVICE" \
        --resolution "$RESOLUTION" \
        --mode "$MODE" \
        --format=pnm \
        --output-file="${scan_file}.pnm" 2>&1 | while IFS= read -r line; do
            if [[ "$line" =~ "Progress" ]]; then
                echo -ne "\r${CYAN}Progress: ${line##*:}${NC}"
            fi
        done

    echo -e "\n"

    if [[ -f "${scan_file}.pnm" ]]; then
        echo -e "${GREEN}✓ Scan completed${NC}"

        # Convert to desired format
        echo -e "${CYAN}Converting to $FORMAT format...${NC}"

        case "$FORMAT" in
            pdf)
                convert "${scan_file}.pnm" "${scan_file}.pdf" 2>/dev/null
                rm -f "${scan_file}.pnm"
                scan_file="${scan_file}.pdf"
                ;;
            jpg|jpeg)
                convert "${scan_file}.pnm" "${scan_file}.jpg" 2>/dev/null
                rm -f "${scan_file}.pnm"
                scan_file="${scan_file}.jpg"
                ;;
            png)
                convert "${scan_file}.pnm" "${scan_file}.png" 2>/dev/null
                rm -f "${scan_file}.pnm"
                scan_file="${scan_file}.png"
                ;;
            *)
                scan_file="${scan_file}.pnm"
                ;;
        esac

        # Perform OCR if enabled
        local final_name="scan_$(date +%Y%m%d_%H%M%S)_$(printf "%03d" $doc_num)"
        local category=""

        if $ENABLE_OCR && [[ -f "$scan_file" ]]; then
            local ocr_result=$(perform_ocr_naming "$scan_file" "$final_name")
            local suggested_name=$(echo "$ocr_result" | cut -d'|' -f1)
            category=$(echo "$ocr_result" | cut -d'|' -f2)

            if [[ -n "$suggested_name" ]] && [[ "$suggested_name" != "$final_name" ]]; then
                final_name="$suggested_name"
            fi
        fi

        # Determine final destination
        local dest_dir="$SESSION_DIR/processed"
        if $AUTO_CATEGORIZE && [[ -n "$category" ]] && [[ -n "${CATEGORIES[$category]}" ]]; then
            dest_dir="$SESSION_DIR/processed/${CATEGORIES[$category]}"
            mkdir -p "$dest_dir"
        fi

        # Ensure unique filename
        local final_path="$dest_dir/${final_name}.${FORMAT}"
        local counter=1
        while [[ -f "$final_path" ]]; do
            final_path="$dest_dir/${final_name}_$(printf "%02d" $counter).${FORMAT}"
            ((counter++))
        done

        # Move file to final location
        mv "$scan_file" "$final_path"

        # Keep original copy if requested
        cp "$final_path" "$SESSION_DIR/originals/original_$(printf "%04d" $doc_num).${FORMAT}"

        # Get file size
        local file_size=$(stat -c%s "$final_path" 2>/dev/null || echo "0")

        # Log to inventory
        echo "$(date +%Y-%m-%d_%H:%M:%S),original_$(printf "%04d" $doc_num),$final_name,$category,$(if $ENABLE_OCR; then echo "Yes"; else echo "No"; fi),$final_path,$file_size,1" >> "$INVENTORY_FILE"

        echo -e "${GREEN}✓ Document saved: ${final_path}${NC}"
        log_message "Scanned and processed: $final_path (Category: ${category:-None})"

        ((TOTAL_SCANNED++))
        return 0
    else
        echo -e "${RED}✗ Scan failed for document #$doc_num${NC}"
        return 1
    fi
}

# Function to scan batch with flatbed
scan_batch_flatbed() {
    local continue_scanning=true
    local doc_num=1

    while $continue_scanning; do
        echo -e "\n${BLUE}════════════════════════════════════════════════════${NC}"
        echo -e "${YELLOW}Place document #$doc_num on scanner glass${NC}"
        echo -e "${CYAN}Press ENTER to scan, 's' to skip, or 'q' to quit:${NC} "

        read -r response

        case "$response" in
            q|Q)
                continue_scanning=false
                ;;
            s|S)
                echo -e "${YELLOW}Skipping document #$doc_num${NC}"
                ;;
            *)
                scan_single_document $doc_num
                ((doc_num++))
                ;;
        esac
    done
}

# Function to generate summary report
generate_summary() {
    echo -e "\n${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                  SCAN SUMMARY                        ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"

    echo -e "${GREEN}Total Documents Scanned:${NC} $TOTAL_SCANNED"
    echo -e "${GREEN}Output Directory:${NC} $SESSION_DIR"

    if $AUTO_CATEGORIZE; then
        echo -e "\n${CYAN}Documents by Category:${NC}"
        for cat_path in "${CATEGORIES[@]}"; do
            local cat_dir="$SESSION_DIR/processed/$cat_path"
            if [[ -d "$cat_dir" ]]; then
                local count=$(find "$cat_dir" -type f | wc -l)
                [[ $count -gt 0 ]] && echo -e "  • $cat_path: $count documents"
            fi
        done
    fi

    # Show uncategorized documents
    local uncategorized=$(find "$SESSION_DIR/processed" -maxdepth 1 -type f | wc -l)
    [[ $uncategorized -gt 0 ]] && echo -e "  • Uncategorized: $uncategorized documents"

    echo -e "\n${CYAN}Files Created:${NC}"
    echo -e "  • Inventory: $INVENTORY_FILE"
    echo -e "  • OCR Log: $OCR_LOG"
    echo -e "  • Scan Log: $LOG_FILE"

    # Calculate total size
    local total_size=$(du -sh "$SESSION_DIR" 2>/dev/null | cut -f1)
    echo -e "\n${GREEN}Total Storage Used:${NC} $total_size"

    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
}

# Function for network scanner check
check_network_access() {
    echo -e "\n${CYAN}Network Scanner Access:${NC}"

    if systemctl is-active --quiet saned.socket; then
        echo -e "${GREEN}✓ Network scanning is enabled on port 6566${NC}"
        echo -e "${CYAN}Other computers can access this scanner using:${NC}"
        echo -e "  ${YELLOW}Server IP:${NC} $(hostname -I | awk '{print $1}')"
        echo -e "  ${YELLOW}Port:${NC} 6566"
    else
        echo -e "${YELLOW}ℹ Network scanning is not configured${NC}"
        echo -e "  Run: ${GREEN}sudo /home/dave/Scripts/install_epson_v39_scanner.sh${NC}"
    fi
}

# Main execution
main() {
    # Check dependencies
    check_dependencies

    # Detect scanner
    if ! detect_epson_scanner; then
        echo -e "${RED}Cannot proceed without a scanner.${NC}"
        echo -e "${YELLOW}Please ensure the Epson V39 is connected and powered on.${NC}"
        exit 1
    fi

    # Check network access
    check_network_access

    # Start scanning
    echo -e "\n${CYAN}Ready to scan documents${NC}"
    scan_batch_flatbed

    # Generate summary
    generate_summary

    log_message "Scanning session completed. Total documents: $TOTAL_SCANNED"
}

# Handle cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Cleaning up temporary files...${NC}"
    rm -rf "$SESSION_DIR/temp"
    echo -e "${GREEN}✓ Cleanup completed${NC}"
}

trap cleanup EXIT

# Run main function
main "$@"