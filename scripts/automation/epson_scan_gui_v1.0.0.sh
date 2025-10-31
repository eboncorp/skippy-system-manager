#!/bin/bash

# Epson V39 Scanner GUI - Graphical interface for scanning and processing documents
# Uses simple-scan for scanning and provides OCR-based auto-naming with categories

OUTPUT_BASE_DIR="/home/dave/ScannedDocuments"
SESSION_DIR="$OUTPUT_BASE_DIR/$(date +%Y-%m-%d_%H-%M-%S)"
SCAN_DIR="$SESSION_DIR/scans"
OCR_LANG="eng"

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

# Check dependencies
if ! command -v zenity >/dev/null 2>&1; then
    xmessage -center "Error: zenity is not installed. Please install it with: sudo apt install zenity"
    exit 1
fi

# Welcome dialog
zenity --question \
    --title="Epson V39 Smart Scanner" \
    --text="Welcome to Epson V39 Smart Scanner!\n\nThis tool will:\n• Open the scanner application\n• Automatically process and name your documents using OCR\n• Organize them into categories\n\nReady to begin?" \
    --width=400 \
    --ok-label="Start Scanning" \
    --cancel-label="Exit"

if [[ $? -ne 0 ]]; then
    exit 0
fi

# Get user preferences
PREFS=$(zenity --forms \
    --title="Scan Settings" \
    --text="Configure your scan session" \
    --add-combo="Enable OCR Auto-naming:" --combo-values="Yes|No" \
    --add-combo="Auto-categorize documents:" --combo-values="Yes|No" \
    --add-entry="Save to folder:" \
    --width=400)

if [[ $? -ne 0 ]]; then
    exit 0
fi

# Parse preferences
IFS='|' read -r enable_ocr auto_categorize custom_folder <<< "$PREFS"

ENABLE_OCR=true
[[ "$enable_ocr" == "No" ]] && ENABLE_OCR=false

AUTO_CATEGORIZE=true
[[ "$auto_categorize" == "No" ]] && AUTO_CATEGORIZE=false

[[ -n "$custom_folder" ]] && SESSION_DIR="$custom_folder/$(date +%Y-%m-%d_%H-%M-%S)" && mkdir -p "$SESSION_DIR/processed" "$SESSION_DIR/originals"

SCAN_DIR="$SESSION_DIR/scans"
mkdir -p "$SCAN_DIR"

# Show scan instructions
zenity --info \
    --title="Ready to Scan" \
    --text="The scanner application will now open.\n\n<b>Instructions:</b>\n1. Place your document on the scanner\n2. Click 'Scan' in the scanner window\n3. Repeat for all documents\n4. Close the scanner window when done\n\n<b>Save location:</b>\n$SCAN_DIR\n\n<b>IMPORTANT:</b> Save all scans to the folder shown above!" \
    --width=500

# Open scanner with progress dialog in background
(
    cd "$SCAN_DIR"
    simple-scan >/dev/null 2>&1
) &
SCANNER_PID=$!

# Wait with a dialog
zenity --question \
    --title="Scanning in Progress" \
    --text="Scanner is open.\n\nWhen you've finished scanning all documents:\n• Close the scanner window\n• Click 'Done' below to process your scans" \
    --width=400 \
    --ok-label="Done Scanning" \
    --cancel-label="Cancel"

CONTINUE=$?

# Kill scanner if still running
kill $SCANNER_PID 2>/dev/null
wait $SCANNER_PID 2>/dev/null

if [[ $CONTINUE -ne 0 ]]; then
    zenity --warning --title="Cancelled" --text="Scanning cancelled." --width=300
    exit 0
fi

# Check for scanned files
SCANNED_FILES=$(find "$SCAN_DIR" -type f \( -name "*.pdf" -o -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) 2>/dev/null)

if [[ -z "$SCANNED_FILES" ]]; then
    zenity --warning \
        --title="No Files Found" \
        --text="No scanned documents were found in:\n$SCAN_DIR\n\nPlease make sure you saved your scans to the correct location." \
        --width=400
    exit 0
fi

# Count files
TOTAL_FILES=$(echo "$SCANNED_FILES" | wc -l)

# Processing dialog
(
    echo "0"
    echo "# Starting document processing..."

    PROCESSED=0

    # Helper functions
    clean_filename() {
        echo "$1" | sed 's/[^a-zA-Z0-9 ._-]//g' | tr -s ' ' | xargs | cut -c1-100
    }

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
    echo "$SCANNED_FILES" | while read -r file; do
        ((PROCESSED++))
        filename=$(basename "$file")
        extension="${filename##*.}"

        PERCENT=$((PROCESSED * 100 / TOTAL_FILES))
        echo "$PERCENT"
        echo "# Processing: $filename ($PROCESSED of $TOTAL_FILES)"

        # Perform OCR
        suggested_name="document_$(date +%Y%m%d_%H%M%S)_$(printf "%03d" $PROCESSED)"
        category=""

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
            fi
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

        sleep 0.1  # Small delay for UI
    done

    echo "100"
    echo "# Processing complete!"

) | zenity --progress \
    --title="Processing Documents" \
    --text="Processing scanned documents..." \
    --percentage=0 \
    --auto-close \
    --width=400

# Cleanup scan folder
rm -rf "$SCAN_DIR"

# Generate summary
SUMMARY="<b>Processing Complete!</b>\n\n"
SUMMARY+="<b>Documents saved to:</b>\n$SESSION_DIR/processed\n\n"

if $AUTO_CATEGORIZE; then
    SUMMARY+="<b>Documents by Category:</b>\n"
    for cat_path in "${CATEGORIES[@]}"; do
        cat_dir="$SESSION_DIR/processed/$cat_path"
        if [[ -d "$cat_dir" ]]; then
            count=$(find "$cat_dir" -type f 2>/dev/null | wc -l)
            if [[ $count -gt 0 ]]; then
                SUMMARY+="  • $cat_path: $count documents\n"
            fi
        fi
    done
fi

uncategorized=$(find "$SESSION_DIR/processed" -maxdepth 1 -type f 2>/dev/null | wc -l)
if [[ $uncategorized -gt 0 ]]; then
    SUMMARY+="  • Uncategorized: $uncategorized documents\n"
fi

# Show completion dialog with options
zenity --question \
    --title="Scan Complete" \
    --text="$SUMMARY" \
    --width=500 \
    --ok-label="Open Folder" \
    --cancel-label="Close"

if [[ $? -eq 0 ]]; then
    xdg-open "$SESSION_DIR/processed" 2>/dev/null &
fi

exit 0