#!/bin/bash
# Automated Document Screenshot Scanner
# Scans Google Photos for document screenshots and organizes them

# Configuration
SCANNER_DIR="/home/dave/DocumentScreenshots"
LOG_FILE="$SCANNER_DIR/scanner.log"
REPORT_DIR="$SCANNER_DIR/reports"

# Create directories
mkdir -p "$SCANNER_DIR" "$REPORT_DIR"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_message "=========================================="
log_message "Starting Automated Document Scanner"
log_message "=========================================="

# Function to scan specific year
scan_year() {
    local year=$1
    log_message "Scanning photos from year: $year"

    python3 /home/dave/Scripts/find_document_screenshots.py \
        --year "$year" \
        --max-files 50 \
        --output "$SCANNER_DIR" \
        2>&1 | tee -a "$LOG_FILE"
}

# Function to scan recent photos
scan_recent() {
    log_message "Scanning recent photos (last 30 days equivalent)"

    python3 /home/dave/Scripts/find_document_screenshots.py \
        --max-files 100 \
        --output "$SCANNER_DIR" \
        2>&1 | tee -a "$LOG_FILE"
}

# Function to scan all years incrementally
scan_all_years() {
    log_message "Starting comprehensive year-by-year scan"

    # Get list of available years
    years=$(rclone lsf googlephotos:media/by-year/ 2>/dev/null | sed 's/\///g' | sort -nr)

    for year in $years; do
        if [[ "$year" =~ ^[0-9]{4}$ ]] && [[ "$year" -ge 2010 ]]; then
            log_message "Processing year: $year"
            scan_year "$year"

            # Brief pause between years
            sleep 2
        fi
    done
}

# Function to generate summary report
generate_summary() {
    log_message "Generating summary report..."

    local summary_file="$REPORT_DIR/summary_$(date +%Y%m%d).txt"

    cat > "$summary_file" << EOF
Document Screenshot Scanner Summary
Generated: $(date)

DIRECTORY CONTENTS:
===================
$(find "$SCANNER_DIR" -type f -name "*.jpg" -o -name "*.png" | wc -l) total image files found
$(find "$SCANNER_DIR/detected" -type f 2>/dev/null | wc -l) potential documents detected

DETECTED DOCUMENTS:
==================
EOF

    if [[ -d "$SCANNER_DIR/detected" ]]; then
        find "$SCANNER_DIR/detected" -type f -name "*.jpg" -o -name "*.png" | while read -r file; do
            echo "• $(basename "$file")" >> "$summary_file"
        done
    fi

    cat >> "$summary_file" << EOF

RECENT ANALYSIS REPORTS:
=======================
EOF

    find "$REPORT_DIR" -name "document_scan_*.json" -mtime -7 | sort -r | head -5 | while read -r report; do
        echo "• $(basename "$report")" >> "$summary_file"
        if command -v jq >/dev/null 2>&1; then
            echo "  - $(jq -r '.total_images // 0' "$report") images analyzed" >> "$summary_file"
            echo "  - $(jq -r '.potential_documents | length' "$report") documents found" >> "$summary_file"
        fi
    done

    log_message "Summary report saved to: $summary_file"
    echo "📊 Summary saved to: $summary_file"
}

# Function to organize found documents
organize_documents() {
    log_message "Organizing detected documents..."

    if [[ -d "$SCANNER_DIR/detected" ]]; then
        # Create date-based organization
        find "$SCANNER_DIR/detected" -type f | while read -r file; do
            # Get file modification date
            file_date=$(stat -c %Y "$file" 2>/dev/null)
            if [[ -n "$file_date" ]]; then
                year=$(date -d "@$file_date" +%Y)
                month=$(date -d "@$file_date" +%m)

                # Create year/month directory
                target_dir="$SCANNER_DIR/organized/$year/$month"
                mkdir -p "$target_dir"

                # Copy file to organized structure
                cp "$file" "$target_dir/"
                log_message "Organized: $(basename "$file") -> $year/$month/"
            fi
        done
    fi
}

# Main execution based on arguments
case "${1:-recent}" in
    "year")
        if [[ -n "$2" ]]; then
            scan_year "$2"
        else
            echo "Usage: $0 year YYYY"
            exit 1
        fi
        ;;
    "recent")
        scan_recent
        ;;
    "all")
        scan_all_years
        ;;
    "summary")
        generate_summary
        ;;
    "organize")
        organize_documents
        ;;
    "full")
        scan_recent
        organize_documents
        generate_summary
        ;;
    *)
        echo "Usage: $0 [recent|year YYYY|all|summary|organize|full]"
        echo "  recent   - Scan recent photos"
        echo "  year     - Scan specific year"
        echo "  all      - Scan all years (comprehensive)"
        echo "  summary  - Generate summary report"
        echo "  organize - Organize found documents by date"
        echo "  full     - Run recent scan + organize + summary"
        exit 1
        ;;
esac

# Always generate a basic summary at the end
if [[ "$1" != "summary" ]]; then
    echo
    echo "📋 QUICK SUMMARY:"
    echo "Found documents: $(find "$SCANNER_DIR/detected" -type f 2>/dev/null | wc -l)"
    echo "Log file: $LOG_FILE"
    echo "Output directory: $SCANNER_DIR"
fi

log_message "Automated document scanner completed"
log_message "=========================================="