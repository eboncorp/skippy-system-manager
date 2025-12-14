#!/bin/bash

# Epson V39 Smart Document Scanner with OCR (epsonscan2 version)
# Features: Auto document detection, OCR naming, categorization

# Configuration
OUTPUT_BASE_DIR="/home/dave/ScannedDocuments"
SESSION_DIR="$OUTPUT_BASE_DIR/$(date +%Y-%m-%d_%H-%M-%S)"
RESOLUTION=300  # DPI
FORMAT="pdf"    # pdf, png, jpg
SETTINGS_FILE="/tmp/epson_scan_settings.SF2"

# OCR Configuration
OCR_LANG="eng"
MAX_FILENAME_LENGTH=100
ENABLE_OCR=true
AUTO_CATEGORIZE=true

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

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Log files
LOG_FILE="$SESSION_DIR/scan.log"
OCR_LOG="$SESSION_DIR/ocr_results.txt"
INVENTORY_FILE="$SESSION_DIR/document_inventory.csv"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Initialize inventory
echo "Timestamp,Original_Name,Final_Name,Category,OCR_Status,File_Path,File_Size" > "$INVENTORY_FILE"

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Epson V39 Smart Document Scanner with OCR          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo -e "${GREEN}Output:${NC} $SESSION_DIR"
echo -e "${GREEN}OCR:${NC} $(if $ENABLE_OCR; then echo "Enabled"; else echo "Disabled"; fi)"
echo -e "${GREEN}Auto-Categorize:${NC} $(if $AUTO_CATEGORIZE; then echo "Enabled"; else echo "Disabled"; fi)"
echo -e "${GREEN}Resolution:${NC} $RESOLUTION DPI | ${GREEN}Format:${NC} $FORMAT"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}\n"

TOTAL_SCANNED=0

# Create settings file
create_settings_file() {
    local output_file="$1"
    local format_code=6  # PDF

    case "$FORMAT" in
        png) format_code=0 ;;
        jpg|jpeg) format_code=1 ;;
        pdf) format_code=6 ;;
    esac

    cat > "$SETTINGS_FILE" <<EOF
{
    "Preset": [
        {
            "0": [
                {
                    "ColorType": {"int": 909670447},
                    "Resolution": {"int": $RESOLUTION},
                    "ImageFormat": {"int": $format_code},
                    "FileNamePrefix": {"string": "scan"},
                    "UserDefinePath": {"string": "$SESSION_DIR/temp/"},
                    "FileNameCounter": {"int": 1},
                    "FileNameOverWrite": {"int": 0},
                    "Folder": {"int": 101},
                    "PDFAllPages": {"int": 1},
                    "Brightness": {"int": 0},
                    "Contrast": {"int": 0},
                    "Gamma": {"int": 22},
                    "AutoSize": {"int": 0},
                    "FunctionalUnit": {"int": 0}
                }
            ]
        }
    ]
}
EOF
}

# Detect scanner
detect_scanner() {
    echo -e "${CYAN}Detecting Epson scanner...${NC}"

    local device_list=$(epsonscan2 --list 2>&1)
    local device_id=$(echo "$device_list" | grep "device ID" | sed 's/device ID ://' | xargs)

    if [[ -n "$device_id" ]]; then
        echo -e "${GREEN}[OK] Found: $device_id${NC}"
        echo "$device_id"
        return 0
    else
        echo -e "${RED}[X] No Epson scanner detected${NC}"
        return 1
    fi
}

# Check dependencies
check_dependencies() {
    local missing_deps=()

    if ! command -v tesseract >/dev/null 2>&1; then
        missing_deps+=("tesseract-ocr")
        ENABLE_OCR=false
    fi

    if ! command -v convert >/dev/null 2>&1; then
        missing_deps+=("imagemagick")
    fi

    if ! command -v pdftotext >/dev/null 2>&1; then
        missing_deps+=("poppler-utils")
    fi

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        echo -e "${YELLOW}Missing dependencies: ${missing_deps[*]}${NC}"
        echo -e "${YELLOW}OCR may be limited${NC}\n"
    fi
}

# Clean filename
clean_filename() {
    local text="$1"
    local cleaned=$(echo "$text" | sed 's/[^a-zA-Z0-9 ._-]//g' | tr -s ' ' | xargs)

    if [[ ${#cleaned} -gt $MAX_FILENAME_LENGTH ]]; then
        cleaned="${cleaned:0:$MAX_FILENAME_LENGTH}"
    fi

    [[ -z "$cleaned" ]] && echo "" || echo "$cleaned"
}

# Extract document info from OCR
extract_document_info() {
    local ocr_text="$1"
    local doc_type=""
    local doc_date=""
    local doc_company=""

    local first_lines=$(echo "$ocr_text" | head -10)

    # Identify document type
    if echo "$ocr_text" | grep -qi "invoice"; then
        doc_type="Invoice"
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
    elif echo "$ocr_text" | grep -qi "medical\|doctor\|patient"; then
        doc_type="Medical"
    elif echo "$ocr_text" | grep -qi "insurance\|policy"; then
        doc_type="Insurance"
    elif echo "$ocr_text" | grep -qi "bill\|amount due"; then
        doc_type="Bill"
    elif echo "$ocr_text" | grep -qi "certificate\|certification"; then
        doc_type="Certificate"
    elif echo "$ocr_text" | grep -qi "bank\|financial"; then
        doc_type="Financial"
    fi

    # Extract date
    local extracted_date=$(echo "$ocr_text" | grep -oE "([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})|([0-9]{4}[/-][0-9]{1,2}[/-][0-9]{1,2})" | head -1)
    if [[ -n "$extracted_date" ]]; then
        doc_date=$(date -d "$extracted_date" +%Y-%m-%d 2>/dev/null || echo "$extracted_date" | tr '/' '-')
    fi

    [[ -z "$doc_date" ]] && doc_date=$(date +%Y-%m-%d)

    # Extract company
    doc_company=$(echo "$first_lines" | grep -oE "^[A-Z][A-Za-z0-9 &,.-]{2,30}$" | head -1)
    if [[ -n "$doc_company" ]]; then
        doc_company=$(clean_filename "$doc_company")
    fi

    # Build filename
    local filename=""
    if [[ -n "$doc_type" ]]; then
        filename="${doc_date}_${doc_type}"
        [[ -n "$doc_company" ]] && filename="${filename}_${doc_company}"
    else
        local first_meaningful=$(echo "$ocr_text" | grep -E "^.{5,}" | head -1)
        if [[ -n "$first_meaningful" ]]; then
            filename="${doc_date}_$(clean_filename "$first_meaningful" | cut -c1-50)"
        fi
    fi

    echo "${filename}|${doc_type}"
}

# Perform OCR
perform_ocr_naming() {
    local input_file="$1"
    local output_name="$2"

    if ! $ENABLE_OCR; then
        echo "${output_name}|"
        return
    fi

    echo -e "${CYAN}  Performing OCR...${NC}"

    local temp_text="$SESSION_DIR/temp/ocr_temp.txt"
    local ocr_text=""
    local ocr_successful=false

    if [[ "$input_file" =~ \.pdf$ ]]; then
        if command -v pdftotext >/dev/null 2>&1; then
            pdftotext -l 3 "$input_file" "$temp_text" 2>/dev/null
            if [[ -s "$temp_text" ]]; then
                ocr_text=$(cat "$temp_text")
                ocr_successful=true
            fi
        fi

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
        if command -v tesseract >/dev/null 2>&1; then
            tesseract "$input_file" "$SESSION_DIR/temp/ocr_result" -l "$OCR_LANG" 2>/dev/null
            if [[ -f "$SESSION_DIR/temp/ocr_result.txt" ]]; then
                ocr_text=$(cat "$SESSION_DIR/temp/ocr_result.txt")
                ocr_successful=true
                rm -f "$SESSION_DIR/temp/ocr_result.txt"
            fi
        fi
    fi

    rm -f "$temp_text"

    if $ocr_successful && [[ -n "$ocr_text" ]]; then
        local info=$(extract_document_info "$ocr_text")
        local suggested_name=$(echo "$info" | cut -d'|' -f1)
        local doc_category=$(echo "$info" | cut -d'|' -f2)

        if [[ -n "$suggested_name" ]]; then
            echo -e "${GREEN}  [OK] Identified: $suggested_name${NC}"
            [[ -n "$doc_category" ]] && echo -e "${GREEN}    Category: $doc_category${NC}"

            {
                echo "===== Document: $output_name ====="
                echo "Suggested: $suggested_name"
                echo "Category: $doc_category"
                echo "OCR text (first 500 chars):"
                echo "${ocr_text:0:500}"
                echo ""
            } >> "$OCR_LOG"

            echo "${suggested_name}|${doc_category}"
        else
            echo -e "${YELLOW}  [!] Could not extract title${NC}"
            echo "${output_name}|"
        fi
    else
        echo -e "${YELLOW}  [!] OCR failed${NC}"
        echo "${output_name}|"
    fi
}

# Scan single document
scan_document() {
    local doc_num=$1
    local device_id="$2"

    echo -e "\n${CYAN}Scanning document #$doc_num...${NC}"

    # Update settings file counter
    create_settings_file

    # Perform scan
    local scan_output=$(epsonscan2 --scan "$device_id" "$SETTINGS_FILE" 2>&1)

    # Wait a moment for file to be written
    sleep 2

    # Find the scanned file
    local scan_file=$(ls -t "$SESSION_DIR/temp"/scan_*.* 2>/dev/null | head -1)

    if [[ -f "$scan_file" ]]; then
        echo -e "${GREEN}[OK] Scan completed${NC}"

        # Perform OCR
        local final_name="scan_$(date +%Y%m%d_%H%M%S)_$(printf "%03d" $doc_num)"
        local category=""

        if $ENABLE_OCR; then
            local ocr_result=$(perform_ocr_naming "$scan_file" "$final_name")
            local suggested_name=$(echo "$ocr_result" | cut -d'|' -f1)
            category=$(echo "$ocr_result" | cut -d'|' -f2)

            if [[ -n "$suggested_name" ]] && [[ "$suggested_name" != "$final_name" ]]; then
                final_name="$suggested_name"
            fi
        fi

        # Determine destination
        local dest_dir="$SESSION_DIR/processed"
        if $AUTO_CATEGORIZE && [[ -n "$category" ]]; then
            local cat_path="${CATEGORIES[$category]}"
            if [[ -n "$cat_path" ]]; then
                dest_dir="$SESSION_DIR/processed/$cat_path"
                mkdir -p "$dest_dir"
            fi
        fi

        # Get file extension
        local extension="${scan_file##*.}"

        # Ensure unique filename
        local final_path="$dest_dir/${final_name}.${extension}"
        local counter=1
        while [[ -f "$final_path" ]]
        do
            final_path="$dest_dir/${final_name}_$(printf "%02d" $counter).${extension}"
            counter=$((counter + 1))
        done

        # Move file
        mv "$scan_file" "$final_path"

        # Keep original
        cp "$final_path" "$SESSION_DIR/originals/original_$(printf "%04d" $doc_num).${extension}"

        # Get file size
        local file_size=$(stat -c%s "$final_path" 2>/dev/null || echo "0")

        # Log to inventory
        echo "$(date +%Y-%m-%d_%H:%M:%S),original_$(printf "%04d" $doc_num),$final_name,$category,$(if $ENABLE_OCR; then echo "Yes"; else echo "No"; fi),$final_path,$file_size" >> "$INVENTORY_FILE"

        echo -e "${GREEN}[OK] Saved: ${final_path}${NC}"
        log_message "Scanned: $final_path (Category: ${category:-None})"

        ((TOTAL_SCANNED++))
        return 0
    else
        echo -e "${RED}[X] Scan failed${NC}"
        echo -e "${YELLOW}Output: $scan_output${NC}"
        return 1
    fi
}

# Main scanning loop
scan_batch() {
    local device_id="$1"
    local doc_num=1
    local continue_scanning=true

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
                scan_document $doc_num "$device_id"
                ((doc_num++))
                ;;
        esac
    done
}

# Generate summary
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
                [[ $count -gt 0 ]] && echo -e "  • $cat_path: $count"
            fi
        done
    fi

    local uncategorized=$(find "$SESSION_DIR/processed" -maxdepth 1 -type f 2>/dev/null | wc -l)
    [[ $uncategorized -gt 0 ]] && echo -e "  • Uncategorized: $uncategorized"

    echo -e "\n${CYAN}Files Created:${NC}"
    echo -e "  • Inventory: $INVENTORY_FILE"
    echo -e "  • OCR Log: $OCR_LOG"
    echo -e "  • Scan Log: $LOG_FILE"

    local total_size=$(du -sh "$SESSION_DIR" 2>/dev/null | cut -f1)
    echo -e "\n${GREEN}Total Storage:${NC} $total_size"

    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
}

# Main execution
main() {
    check_dependencies

    local device_id=$(detect_scanner)
    if [[ -z "$device_id" ]]; then
        echo -e "${RED}Cannot proceed without scanner${NC}"
        exit 1
    fi

    # Create settings file
    create_settings_file

    echo -e "\n${CYAN}Ready to scan${NC}"
    scan_batch "$device_id"

    generate_summary
    log_message "Scanning session completed. Total: $TOTAL_SCANNED"
}

# Cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    rm -rf "$SESSION_DIR/temp"
    rm -f "$SETTINGS_FILE"
    echo -e "${GREEN}[OK] Done${NC}"
}

trap cleanup EXIT

# Run
main "$@"