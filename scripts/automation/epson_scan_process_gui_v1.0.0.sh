#!/bin/bash

# Epson Scanner - Process Documents GUI
# Simplified version: You scan manually, then this processes and organizes them

OUTPUT_BASE_DIR="/home/dave/ScannedDocuments"
SESSION_DIR="$OUTPUT_BASE_DIR/$(date +%Y-%m-%d_%H-%M-%S)"
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

mkdir -p "$SESSION_DIR/processed" "$SESSION_DIR/originals"

# Check dependencies
if ! command -v zenity >/dev/null 2>&1; then
    echo "Error: zenity not installed"
    exit 1
fi

# Welcome
zenity --info \
    --title="Epson Smart Document Processor" \
    --text="<b>Welcome to Smart Document Processor!</b>\n\nThis tool will:\n• Let you select scanned documents\n• Automatically name them using OCR\n• Organize them into categories\n\n<b>First, scan your documents using epsonscan2</b>\n(You can find it in your applications menu)\n\nWhen your documents are scanned, click OK to select them." \
    --width=450

if [[ $? -ne 0 ]]; then
    exit 0
fi

# Get settings
PREFS=$(zenity --forms \
    --title="Processing Settings" \
    --text="Configure document processing" \
    --add-combo="Enable OCR Auto-naming:" --combo-values="Yes|No" \
    --add-combo="Auto-categorize documents:" --combo-values="Yes|No" \
    --width=400)

if [[ $? -ne 0 ]]; then
    exit 0
fi

IFS='|' read -r enable_ocr auto_categorize <<< "$PREFS"

ENABLE_OCR=true
[[ "$enable_ocr" == "No" ]] && ENABLE_OCR=false

AUTO_CATEGORIZE=true
[[ "$auto_categorize" == "No" ]] && AUTO_CATEGORIZE=false

# Select files
FILES=$(zenity --file-selection \
    --title="Select Scanned Documents" \
    --multiple \
    --separator="|" \
    --file-filter="Documents | *.pdf *.PDF *.png *.PNG *.jpg *.JPG *.jpeg *.JPEG")

if [[ $? -ne 0 ]] || [[ -z "$FILES" ]]; then
    zenity --warning --title="Cancelled" --text="No files selected." --width=300
    exit 0
fi

# Count files
TOTAL_FILES=$(echo "$FILES" | tr '|' '\n' | wc -l)

# Processing
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
        local doc_company=""

        # Detect document type with more patterns
        if echo "$ocr_text" | grep -qiE "invoice|bill to|amount due"; then
            doc_type="Invoice"
        elif echo "$ocr_text" | grep -qiE "receipt|paid|transaction"; then
            doc_type="Receipt"
        elif echo "$ocr_text" | grep -qiE "contract|agreement|terms and conditions"; then
            doc_type="Contract"
        elif echo "$ocr_text" | grep -qiE "report|quarterly|annual"; then
            doc_type="Report"
        elif echo "$ocr_text" | grep -qiE "statement|account balance|balance due"; then
            doc_type="Statement"
        elif echo "$ocr_text" | grep -qiE "internal revenue|irs|form [0-9]|1099|w-2|tax|ein|employer.id"; then
            doc_type="Tax_Document"
        elif echo "$ocr_text" | grep -qiE "medical|patient|doctor|prescription|hospital"; then
            doc_type="Medical"
        elif echo "$ocr_text" | grep -qiE "certificate|certification|certified"; then
            doc_type="Certificate"
        elif echo "$ocr_text" | grep -qiE "letter|dear|sincerely"; then
            doc_type="Letter"
        fi

        # Extract date (multiple formats)
        local extracted_date=$(echo "$ocr_text" | grep -oE "(January|February|March|April|May|June|July|August|September|October|November|December) [0-9]{1,2}, [0-9]{4}" | head -1)
        if [[ -z "$extracted_date" ]]; then
            extracted_date=$(echo "$ocr_text" | grep -oE "[0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4}" | head -1)
        fi
        if [[ -n "$extracted_date" ]]; then
            doc_date=$(date -d "$extracted_date" +%Y-%m-%d 2>/dev/null || echo "$doc_date")
        fi

        # Extract company/organization name (look for ALL CAPS lines or "incorporated/llc")
        doc_company=$(echo "$ocr_text" | grep -E "^[A-Z][A-Z0-9 ]{3,40}(INCORPORATED|INC|LLC|CORP|LTD)" | head -1 | cut -c1-40)
        if [[ -z "$doc_company" ]]; then
            doc_company=$(echo "$ocr_text" | grep -E "^[A-Z ]{5,40}$" | grep -v "DEPARTMENT\|SERVICE\|TREASURY" | head -1 | cut -c1-40)
        fi
        doc_company=$(clean_filename "$doc_company")

        # Build filename
        local filename="${doc_date}"
        [[ -n "$doc_type" ]] && filename="${filename}_${doc_type}"
        [[ -n "$doc_company" ]] && filename="${filename}_${doc_company}"

        # If still no meaningful name, use first meaningful line
        if [[ "$filename" == "$doc_date" ]]; then
            local first_line=$(echo "$ocr_text" | grep -E '.{10,}' | head -1 | cut -c1-50)
            filename="${doc_date}_$(clean_filename "$first_line")"
        fi

        echo "${filename}|${doc_type}"
    }

    # Process each file
    echo "$FILES" | tr '|' '\n' | while read -r file; do
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
            fi

            # If no text extracted from PDF, it's an image-only PDF - use Tesseract
            if [[ -z "$ocr_text" ]] && [[ "$extension" == "pdf" ]]; then
                temp_img="/tmp/ocr_temp_$$"
                # Use pdftoppm (much faster than ImageMagick for PDFs)
                if command -v pdftoppm >/dev/null 2>&1; then
                    timeout 10 pdftoppm -f 1 -l 1 -r 150 "$file" "$temp_img" >/dev/null 2>&1
                    if [[ -f "${temp_img}-1.ppm" ]]; then
                        ocr_text=$(timeout 15 tesseract "${temp_img}-1.ppm" stdout -l "$OCR_LANG" 2>/dev/null)
                        # Debug: save OCR text
                        echo "$ocr_text" > "/tmp/last_ocr_${PROCESSED}.txt"
                        rm -f "${temp_img}"-*.ppm
                    fi
                fi
            elif command -v tesseract >/dev/null 2>&1; then
                ocr_text=$(tesseract "$file" stdout -l "$OCR_LANG" 2>/dev/null)
                echo "$ocr_text" > "/tmp/last_ocr_${PROCESSED}.txt"
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

        # Copy file
        cp "$file" "$final_path"
        cp "$file" "$SESSION_DIR/originals/$(basename "$file")"

        sleep 0.1
    done

    echo "100"
    echo "# Processing complete!"

) | zenity --progress \
    --title="Processing Documents" \
    --text="Processing documents..." \
    --percentage=0 \
    --auto-close \
    --width=400

# Generate summary
SUMMARY="<b>Processing Complete!</b>\n\n"
SUMMARY+="<b>Processed:</b> $TOTAL_FILES documents\n\n"
SUMMARY+="<b>Saved to:</b>\n$SESSION_DIR/processed\n\n"

if $AUTO_CATEGORIZE; then
    SUMMARY+="<b>By Category:</b>\n"
    for cat_path in "${CATEGORIES[@]}"; do
        cat_dir="$SESSION_DIR/processed/$cat_path"
        if [[ -d "$cat_dir" ]]; then
            count=$(find "$cat_dir" -type f 2>/dev/null | wc -l)
            if [[ $count -gt 0 ]]; then
                SUMMARY+="  • $cat_path: $count\n"
            fi
        fi
    done
fi

uncategorized=$(find "$SESSION_DIR/processed" -maxdepth 1 -type f 2>/dev/null | wc -l)
if [[ $uncategorized -gt 0 ]]; then
    SUMMARY+="  • Uncategorized: $uncategorized\n"
fi

# Show completion with option to open folder
zenity --question \
    --title="Complete" \
    --text="$SUMMARY" \
    --width=500 \
    --ok-label="Open Folder" \
    --cancel-label="Close"

if [[ $? -eq 0 ]]; then
    xdg-open "$SESSION_DIR/processed" &
fi