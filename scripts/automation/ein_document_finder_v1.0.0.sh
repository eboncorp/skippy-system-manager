#!/bin/bash
# EIN Document Finder
# Searches for documents that might contain EIN information

EIN_SEARCH_DIR="/home/dave/EINDocuments"
LOG_FILE="$EIN_SEARCH_DIR/ein_search.log"

mkdir -p "$EIN_SEARCH_DIR"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_message "=========================================="
log_message "Starting EIN Document Search"
log_message "=========================================="

# Function to search local documents first
search_local_documents() {
    log_message "Searching local documents for EIN-related content..."

    # Search common document directories
    local search_dirs=(
        "/home/dave/Documents"
        "/home/dave/Scans"
        "/home/dave/Downloads"
        "/home/dave/Desktop"
        "/home/dave/Personal"
        "/home/dave/Business"
        "/home/dave/Tax"
    )

    local ein_files=()

    for dir in "${search_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            log_message "Searching in: $dir"

            # Search for files with EIN-related names
            find "$dir" -type f \( -iname "*ein*" -o -iname "*tax*" -o -iname "*irs*" -o -iname "*business*" -o -iname "*form*" -o -iname "*ss4*" -o -iname "*federal*" \) 2>/dev/null | while read -r file; do
                echo "📄 Found: $file"
                cp "$file" "$EIN_SEARCH_DIR/" 2>/dev/null || echo "  ⚠️  Could not copy: $file"
            done

            # Search inside text files for EIN patterns
            find "$dir" -type f \( -name "*.txt" -o -name "*.md" -o -name "*.doc" -o -name "*.docx" -o -name "*.pdf" \) -exec grep -l -i "ein\|employer.*identification\|tax.*id\|federal.*id" {} \; 2>/dev/null | while read -r file; do
                echo "📝 Text match: $file"
                cp "$file" "$EIN_SEARCH_DIR/" 2>/dev/null || echo "  ⚠️  Could not copy: $file"
            done
        fi
    done
}

# Function to search Google Photos with small batches
search_google_photos_smart() {
    log_message "Searching Google Photos with smart batching..."

    # Try different strategies with very small batches
    local strategies=(
        "media/by-year/2024:5"
        "media/by-year/2023:5"
        "media/by-year/2022:5"
        "album:10"
    )

    for strategy in "${strategies[@]}"; do
        IFS=':' read -r path max_files <<< "$strategy"
        log_message "Trying: googlephotos:$path (max $max_files files)"

        # Very aggressive filtering for EIN-related content
        timeout 45 rclone copy "googlephotos:$path" "$EIN_SEARCH_DIR/temp_photos" \
            --include "*.{jpg,jpeg,png,pdf}" \
            --include "*ein*" --include "*tax*" --include "*irs*" --include "*business*" --include "*form*" --include "*screenshot*" \
            --max-size 10M \
            --max-transfer "$max_files" \
            --transfers 1 \
            --checkers 2 \
            --max-duration 40s \
            2>/dev/null

        # Check what we got
        local downloaded=$(find "$EIN_SEARCH_DIR/temp_photos" -type f 2>/dev/null | wc -l)
        if [[ $downloaded -gt 0 ]]; then
            log_message "✓ Downloaded $downloaded files from $path"

            # Analyze these files
            python3 /home/dave/Scripts/targeted_document_scanner.py \
                --search-terms ein tax irs business form screenshot \
                --local-dir "$EIN_SEARCH_DIR/temp_photos" \
                --output "$EIN_SEARCH_DIR" 2>/dev/null

            # Move temp files to main directory
            find "$EIN_SEARCH_DIR/temp_photos" -type f -exec mv {} "$EIN_SEARCH_DIR/" \; 2>/dev/null
            rmdir "$EIN_SEARCH_DIR/temp_photos" 2>/dev/null
        else
            log_message "✗ No files downloaded from $path"
        fi

        # Brief pause between attempts
        sleep 2
    done
}

# Function to search with OCR if tesseract is available
search_with_ocr() {
    if command -v tesseract >/dev/null 2>&1; then
        log_message "Running OCR search for EIN patterns..."

        find "$EIN_SEARCH_DIR" -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" \) | while read -r image; do
            log_message "OCR analyzing: $(basename "$image")"

            # Extract text and search for EIN patterns
            if tesseract "$image" stdout 2>/dev/null | grep -qi "ein\|employer.*identification\|tax.*id\|ss.*4\|federal.*id"; then
                echo "🎯 EIN PATTERN FOUND in: $(basename "$image")"
                mv "$image" "$EIN_SEARCH_DIR/ein_candidates/" 2>/dev/null || mkdir -p "$EIN_SEARCH_DIR/ein_candidates/" && mv "$image" "$EIN_SEARCH_DIR/ein_candidates/"
            fi
        done
    else
        log_message "Tesseract not available, skipping OCR search"
    fi
}

# Function to search backup drives
search_backup_drives() {
    log_message "Searching backup drives for EIN documents..."

    # Check Google Drive backup
    if rclone lsd googledrive: >/dev/null 2>&1; then
        log_message "Searching Google Drive backup..."

        timeout 30 rclone copy "googledrive:Backups/ebonhawk-full" "$EIN_SEARCH_DIR/backup_search" \
            --include "*ein*" --include "*tax*" --include "*irs*" --include "*business*" --include "*form*" \
            --max-size 20M \
            --max-transfer 10 \
            --transfers 1 \
            --max-duration 25s \
            2>/dev/null

        local backup_files=$(find "$EIN_SEARCH_DIR/backup_search" -type f 2>/dev/null | wc -l)
        if [[ $backup_files -gt 0 ]]; then
            log_message "✓ Found $backup_files files in backup"
            find "$EIN_SEARCH_DIR/backup_search" -type f -exec mv {} "$EIN_SEARCH_DIR/" \; 2>/dev/null
        fi
        rm -rf "$EIN_SEARCH_DIR/backup_search" 2>/dev/null
    fi
}

# Generate summary report
generate_ein_report() {
    log_message "Generating EIN search report..."

    local report_file="$EIN_SEARCH_DIR/ein_search_report_$(date +%Y%m%d_%H%M%S).txt"

    cat > "$report_file" << EOF
EIN Document Search Report
Generated: $(date)

SEARCH STRATEGY:
================
1. Local document directories
2. Google Photos smart search
3. OCR text analysis (if available)
4. Backup drive search

FOUND FILES:
============
EOF

    find "$EIN_SEARCH_DIR" -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.pdf" -o -name "*.doc*" -o -name "*.txt" \) | while read -r file; do
        echo "• $(basename "$file") ($(du -h "$file" | cut -f1))" >> "$report_file"
    done

    cat >> "$report_file" << EOF

CANDIDATE FILES WITH HIGH EIN PROBABILITY:
==========================================
EOF

    if [[ -d "$EIN_SEARCH_DIR/ein_candidates" ]]; then
        find "$EIN_SEARCH_DIR/ein_candidates" -type f | while read -r file; do
            echo "🎯 $(basename "$file")" >> "$report_file"
        done
    fi

    cat >> "$report_file" << EOF

NEXT STEPS:
===========
1. Review files in: $EIN_SEARCH_DIR
2. Check high-probability candidates in: $EIN_SEARCH_DIR/ein_candidates/
3. Manually verify EIN numbers found
4. Securely store or delete copies as needed

LOG FILE: $LOG_FILE
EOF

    echo "📊 Report saved to: $report_file"
    log_message "Report saved to: $report_file"
}

# Main execution
echo "🔍 Searching for EIN-related documents..."
echo "This will search:"
echo "  • Local document directories"
echo "  • Google Photos (with smart batching)"
echo "  • Backup drives"
echo "  • OCR text analysis (if available)"
echo

search_local_documents
search_google_photos_smart
search_with_ocr
search_backup_drives
generate_ein_report

# Final summary
found_files=$(find "$EIN_SEARCH_DIR" -type f | wc -l)
echo
echo "🎯 EIN SEARCH COMPLETE!"
echo "Found $found_files potential files"
echo "Check directory: $EIN_SEARCH_DIR"

if [[ -d "$EIN_SEARCH_DIR/ein_candidates" ]]; then
    candidate_files=$(find "$EIN_SEARCH_DIR/ein_candidates" -type f | wc -l)
    echo "High-probability candidates: $candidate_files"
fi

log_message "EIN search completed. Found $found_files files."
log_message "=========================================="