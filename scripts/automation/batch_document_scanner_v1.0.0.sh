#!/bin/bash
# Batch Document Scanner for Brother MFC-7860DW
# Automatically scans all documents in the ADF (up to 35 pages)
# Saves each page as a separate file

# Configuration
SCANNER_DEVICE="brother4:net1;dev1"  # Brother MFC-7860DW
ADF_CAPACITY=35  # Brother MFC-7860DW ADF holds 35 sheets
OUTPUT_BASE_DIR="/home/dave/ScannedDocuments"
SESSION_DIR="$OUTPUT_BASE_DIR/$(date +%Y-%m-%d_%H-%M-%S)"
RESOLUTION=300  # DPI (150, 200, 300, 600)
MODE="Color"    # Color, Gray, or Lineart
FORMAT="pdf"    # pdf, png, jpg, or tiff

# Create output directory
mkdir -p "$SESSION_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="$SESSION_DIR/scan.log"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        Automatic Document Scanner                    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo -e "${GREEN}Scanner:${NC} Brother MFC-7860DW (ADF capacity: $ADF_CAPACITY sheets)"
echo -e "${GREEN}Output Directory:${NC} $SESSION_DIR"
echo -e "${GREEN}Resolution:${NC} $RESOLUTION DPI"
echo -e "${GREEN}Mode:${NC} $MODE"
echo -e "${GREEN}Format:${NC} $FORMAT"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}\n"

# Counter for total documents scanned
TOTAL_SCANNED=0
BATCH_NUMBER=1

# Function to check scanner availability
check_scanner() {
    echo -e "${CYAN}Checking scanner availability...${NC}"
    scanimage -L | grep -q "$SCANNER_DEVICE"
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✓ Scanner detected and ready${NC}"
        return 0
    else
        echo -e "${RED}✗ Scanner not detected. Please check connection.${NC}"
        return 1
    fi
}

# Function to scan all documents in ADF
scan_adf_batch() {
    local batch_dir="$SESSION_DIR/batch_$(printf "%03d" $BATCH_NUMBER)"
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

    echo -e "\n${CYAN}Starting automatic batch scan...${NC}"
    log_message "Starting batch #$BATCH_NUMBER"

    # Determine source option for ADF
    # Try to detect available source options
    local source_option="Automatic Document Feeder"

    # Check available sources
    local available_sources=$(scanimage -d "$SCANNER_DEVICE" --help 2>/dev/null | grep -A 10 "^\-\-source" | grep -E "^\s+\w")

    if echo "$available_sources" | grep -q "ADF"; then
        source_option="ADF"
    elif echo "$available_sources" | grep -q "Automatic"; then
        source_option="Automatic Document Feeder"
    fi

    # Use scanimage batch mode
    if [[ "$FORMAT" == "pdf" ]]; then
        # For PDF, scan to individual pages then combine
        echo -e "${CYAN}Scanning documents to PDF format...${NC}"

        scanimage -d "$SCANNER_DEVICE" \
            --source "$source_option" \
            --resolution "$RESOLUTION" \
            --mode "$MODE" \
            --batch="$batch_dir/page_%04d.pnm" \
            --batch-start=1 \
            --progress 2>&1 | while IFS= read -r line; do
                if [[ "$line" =~ "Scanning page" ]]; then
                    page_num=$(echo "$line" | grep -oP '\d+')
                    echo -e "${GREEN}→ Scanning page $page_num${NC}"
                elif [[ "$line" =~ "batch aborted" ]] || [[ "$line" =~ "Document feeder out of documents" ]]; then
                    echo -e "${YELLOW}ADF empty or error - batch complete${NC}"
                fi
            done

        # Convert PNM files to PDF
        local pnm_count=$(ls -1 "$batch_dir"/*.pnm 2>/dev/null | wc -l)
        if [[ $pnm_count -gt 0 ]]; then
            echo -e "${CYAN}Converting $pnm_count pages to PDF...${NC}"

            for pnm_file in "$batch_dir"/*.pnm; do
                if [[ -f "$pnm_file" ]]; then
                    local base_name=$(basename "$pnm_file" .pnm)
                    local pdf_file="$SESSION_DIR/document_$(printf "%04d" $((TOTAL_SCANNED + 1))).pdf"

                    # Convert PNM to PDF using ImageMagick or similar
                    if command -v convert >/dev/null 2>&1; then
                        convert "$pnm_file" "$pdf_file" 2>/dev/null
                    elif command -v pnmtopdf >/dev/null 2>&1; then
                        pnmtopdf "$pnm_file" > "$pdf_file" 2>/dev/null
                    else
                        # Keep as PNM if no converter available
                        pdf_file="$SESSION_DIR/document_$(printf "%04d" $((TOTAL_SCANNED + 1))).pnm"
                        mv "$pnm_file" "$pdf_file"
                    fi

                    if [[ -f "$pdf_file" ]]; then
                        TOTAL_SCANNED=$((TOTAL_SCANNED + 1))
                        echo -e "${GREEN}✓ Saved: $(basename "$pdf_file")${NC}"
                        rm -f "$pnm_file"  # Clean up temporary PNM
                    fi
                fi
            done
        fi

    else
        # For image formats, scan directly to final format
        echo -e "${CYAN}Scanning documents to $FORMAT format...${NC}"

        scanimage -d "$SCANNER_DEVICE" \
            --source "$source_option" \
            --resolution "$RESOLUTION" \
            --mode "$MODE" \
            --batch="$SESSION_DIR/document_%04d.$FORMAT" \
            --batch-start=$((TOTAL_SCANNED + 1)) \
            --format="$FORMAT" \
            --progress 2>&1 | while IFS= read -r line; do
                if [[ "$line" =~ "Scanning page" ]]; then
                    page_num=$(echo "$line" | grep -oP '\d+')
                    echo -e "${GREEN}→ Scanning page $page_num${NC}"
                    TOTAL_SCANNED=$((TOTAL_SCANNED + 1))
                elif [[ "$line" =~ "batch aborted" ]] || [[ "$line" =~ "Document feeder out of documents" ]]; then
                    echo -e "${YELLOW}ADF empty or error - batch complete${NC}"
                fi
            done
    fi

    # Count actual files created
    local new_files=$(ls -1 "$SESSION_DIR"/document_*.* 2>/dev/null | wc -l)
    local batch_count=$((new_files - TOTAL_SCANNED))
    TOTAL_SCANNED=$new_files

    echo -e "\n${GREEN}Batch #$BATCH_NUMBER complete: $batch_count documents scanned${NC}"
    log_message "Batch #$BATCH_NUMBER complete: $batch_count documents"

    # Clean up empty batch directory
    rmdir "$batch_dir" 2>/dev/null

    BATCH_NUMBER=$((BATCH_NUMBER + 1))
    return 0
}

# Function to generate summary report
generate_summary() {
    echo -e "\n${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║               Scanning Session Summary                ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
    echo -e "${GREEN}Total documents scanned:${NC} $TOTAL_SCANNED"
    echo -e "${GREEN}Total batches:${NC} $((BATCH_NUMBER - 1))"
    echo -e "${GREEN}Output directory:${NC} $SESSION_DIR"

    # List all scanned files
    if [[ $TOTAL_SCANNED -gt 0 ]]; then
        echo -e "\n${CYAN}Scanned files:${NC}"
        ls -lh "$SESSION_DIR"/document_*.* 2>/dev/null | awk '{printf "  • %-30s %s\n", $9, $5}' | head -20

        if [[ $TOTAL_SCANNED -gt 20 ]]; then
            echo "  ... and $((TOTAL_SCANNED - 20)) more files"
        fi
    fi

    # Calculate total size
    if [[ -d "$SESSION_DIR" ]]; then
        local total_size=$(du -sh "$SESSION_DIR" 2>/dev/null | cut -f1)
        echo -e "\n${GREEN}Total size:${NC} $total_size"
    fi

    # Create index file
    local index_file="$SESSION_DIR/index.txt"
    {
        echo "Document Scanning Session Index"
        echo "==============================="
        echo "Date: $(date)"
        echo "Scanner: Brother MFC-7860DW"
        echo "Total Documents: $TOTAL_SCANNED"
        echo "Total Batches: $((BATCH_NUMBER - 1))"
        echo "Resolution: $RESOLUTION DPI"
        echo "Mode: $MODE"
        echo "Format: $FORMAT"
        echo ""
        echo "Files:"
        echo "------"
        ls -1 "$SESSION_DIR"/document_*.* 2>/dev/null | while read -r file; do
            echo "$(basename "$file")"
        done
    } > "$index_file"

    echo -e "\n${GREEN}Index file created:${NC} $index_file"
    log_message "Session complete: $TOTAL_SCANNED documents scanned"
}

# Function to merge PDFs if requested
merge_pdfs() {
    if [[ "$FORMAT" != "pdf" ]]; then
        echo -e "${YELLOW}Not PDF format, skipping merge${NC}"
        return
    fi

    if ! command -v pdfunite >/dev/null 2>&1 && ! command -v gs >/dev/null 2>&1; then
        echo -e "${YELLOW}PDF merge tools not available (install poppler-utils or ghostscript)${NC}"
        return
    fi

    echo -e "\n${CYAN}Would you like to merge all PDFs into a single file? (y/n)${NC}"
    read -r merge_response

    if [[ "$merge_response" == "y" ]]; then
        local merged_file="$SESSION_DIR/merged_$(date +%Y%m%d_%H%M%S).pdf"

        if command -v pdfunite >/dev/null 2>&1; then
            echo -e "${CYAN}Merging PDFs using pdfunite...${NC}"
            pdfunite "$SESSION_DIR"/document_*.pdf "$merged_file" 2>/dev/null
        elif command -v gs >/dev/null 2>&1; then
            echo -e "${CYAN}Merging PDFs using ghostscript...${NC}"
            gs -dBATCH -dNOPAUSE -q -sDEVICE=pdfwrite -sOutputFile="$merged_file" "$SESSION_DIR"/document_*.pdf
        fi

        if [[ -f "$merged_file" ]]; then
            echo -e "${GREEN}✓ Merged PDF created: $merged_file${NC}"
            local merged_size=$(du -h "$merged_file" | cut -f1)
            echo -e "${GREEN}  Size: $merged_size${NC}"
        fi
    fi
}

# Main execution
if ! check_scanner; then
    echo -e "${RED}Scanner not available. Exiting.${NC}"
    exit 1
fi

echo -e "\n${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Ready to begin scanning${NC}"
echo -e "${YELLOW}The ADF can hold up to $ADF_CAPACITY pages${NC}"
echo -e "${YELLOW}Each page will be saved as a separate file${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}\n"

# Main scanning loop
while true; do
    if ! scan_adf_batch; then
        break
    fi

    echo -e "\n${BLUE}Continue with another batch?${NC}"
    echo -e "${YELLOW}Load more documents and press ENTER, or 'q' to finish${NC}"
    read -r continue_response

    if [[ "$continue_response" == "q" ]]; then
        break
    fi
done

# Generate summary
if [[ $TOTAL_SCANNED -gt 0 ]]; then
    generate_summary

    # Offer to merge PDFs if applicable
    if [[ "$FORMAT" == "pdf" ]] && [[ $TOTAL_SCANNED -gt 1 ]]; then
        merge_pdfs
    fi

    echo -e "\n${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║           Scanning session complete!                  ║${NC}"
    echo -e "${GREEN}║     All files saved to: $SESSION_DIR${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
else
    echo -e "\n${YELLOW}No documents were scanned${NC}"
fi