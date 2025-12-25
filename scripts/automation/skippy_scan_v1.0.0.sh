#!/bin/bash

# Skippy Scan v1.0.0
# Unified scanning interface for Epson V39 with Skippy integration
#
# Usage:
#   skippy_scan_v1.0.0.sh [mode] [options]
#
# Modes:
#   gui       - Launch graphical scanner (default)
#   smart     - CLI scanner with OCR auto-naming
#   quick     - Single document scan
#   batch     - Batch scanning mode
#   status    - Check scanner status
#   process   - Process incoming scans
#
# Dependencies:
#   - epsonscan2 (Epson scanner driver)
#   - tesseract-ocr (optional, for OCR)
#   - zenity (optional, for GUI dialogs)
#
# Created: 2025-12-22

set -euo pipefail

# Configuration
SKIPPY_SCAN_DIR="/home/dave/skippy/operations/scans"
INCOMING_DIR="$SKIPPY_SCAN_DIR/incoming"
PROCESSED_DIR="$SKIPPY_SCAN_DIR/processed"
SCAN_OUTPUT_DIR="/home/dave/ScannedDocuments"
SCANNER_SCRIPTS_DIR="/home/dave/skippy/scripts/automation"
LOG_DIR="/home/dave/skippy/logs/scanning"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Ensure directories exist
mkdir -p "$INCOMING_DIR" "$PROCESSED_DIR" "$LOG_DIR"

# Logging
LOG_FILE="$LOG_DIR/skippy_scan_$(date +%Y%m%d).log"
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Banner
show_banner() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║        ${CYAN}Skippy Scan${BLUE} - Document Scanning Suite          ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
}

# Check scanner
check_scanner() {
    echo -e "${CYAN}Checking for Epson scanner...${NC}"

    if ! command -v epsonscan2 >/dev/null 2>&1; then
        echo -e "${RED}[X] epsonscan2 not installed${NC}"
        echo -e "${YELLOW}Install with: sudo apt install epsonscan2${NC}"
        return 1
    fi

    local device_info=$(epsonscan2 --list 2>&1)
    local device_id=$(echo "$device_info" | grep "device ID" | sed 's/device ID ://' | xargs)

    if [[ -n "$device_id" ]]; then
        echo -e "${GREEN}[OK] Scanner found: $device_id${NC}"
        return 0
    else
        echo -e "${RED}[X] No scanner detected${NC}"
        echo -e "${YELLOW}Check USB connection and try again${NC}"
        return 1
    fi
}

# Check dependencies
check_dependencies() {
    local missing=()

    command -v epsonscan2 >/dev/null 2>&1 || missing+=("epsonscan2")
    command -v tesseract >/dev/null 2>&1 || missing+=("tesseract-ocr")
    command -v convert >/dev/null 2>&1 || missing+=("imagemagick")
    command -v pdftotext >/dev/null 2>&1 || missing+=("poppler-utils")

    if [[ ${#missing[@]} -gt 0 ]]; then
        echo -e "${YELLOW}Missing optional dependencies: ${missing[*]}${NC}"
        echo -e "${YELLOW}Some features may be limited${NC}"
    else
        echo -e "${GREEN}[OK] All dependencies installed${NC}"
    fi
}

# Show status
show_status() {
    show_banner
    echo ""

    check_scanner
    echo ""
    check_dependencies
    echo ""

    # Show queue status
    echo -e "${CYAN}Document Queue Status:${NC}"
    local incoming_count=$(find "$INCOMING_DIR" -type f -name "*.pdf" 2>/dev/null | wc -l)
    local processed_count=$(find "$PROCESSED_DIR" -type f 2>/dev/null | wc -l)

    echo -e "  Incoming queue: ${YELLOW}$incoming_count${NC} documents"
    echo -e "  Processed: ${GREEN}$processed_count${NC} documents"

    # Show recent scans
    if [[ -d "$SCAN_OUTPUT_DIR" ]]; then
        local recent_sessions=$(ls -t "$SCAN_OUTPUT_DIR" 2>/dev/null | head -3)
        if [[ -n "$recent_sessions" ]]; then
            echo -e "\n${CYAN}Recent scan sessions:${NC}"
            echo "$recent_sessions" | while read -r session; do
                local session_path="$SCAN_OUTPUT_DIR/$session"
                local count=$(find "$session_path" -type f \( -name "*.pdf" -o -name "*.png" \) 2>/dev/null | wc -l)
                echo -e "  • $session ($count files)"
            done
        fi
    fi

    echo ""
}

# Launch GUI scanner
launch_gui() {
    show_banner
    echo -e "${GREEN}Launching GUI Scanner...${NC}\n"

    if ! check_scanner; then
        return 1
    fi

    log "Launched GUI scanner"

    if [[ -f "$SCANNER_SCRIPTS_DIR/epson_scan_gui_v1.0.0.sh" ]]; then
        bash "$SCANNER_SCRIPTS_DIR/epson_scan_gui_v1.0.0.sh"
    else
        echo -e "${YELLOW}GUI script not found, launching simple-scan...${NC}"
        simple-scan &
    fi
}

# Launch smart scanner
launch_smart() {
    show_banner
    echo -e "${GREEN}Launching Smart Scanner with OCR...${NC}\n"

    if ! check_scanner; then
        return 1
    fi

    log "Launched smart scanner"

    if [[ -f "$SCANNER_SCRIPTS_DIR/epson_v39_smart_scanner_v2.0.0.sh" ]]; then
        bash "$SCANNER_SCRIPTS_DIR/epson_v39_smart_scanner_v2.0.0.sh"
    else
        echo -e "${RED}Smart scanner script not found${NC}"
        return 1
    fi
}

# Quick single scan
quick_scan() {
    show_banner
    echo -e "${GREEN}Quick Scan Mode${NC}\n"

    if ! check_scanner; then
        return 1
    fi

    local output_dir="$INCOMING_DIR"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local output_file="$output_dir/scan_${timestamp}.pdf"

    echo -e "${CYAN}Scanning to: $output_file${NC}"
    echo -e "${YELLOW}Place document on scanner and press ENTER...${NC}"
    read -r

    # Create settings file
    local settings_file="/tmp/skippy_quick_scan.SF2"
    cat > "$settings_file" <<EOF
{
    "Preset": [
        {
            "0": [
                {
                    "ColorType": {"int": 909670447},
                    "Resolution": {"int": 300},
                    "ImageFormat": {"int": 6},
                    "FileNamePrefix": {"string": "scan_$timestamp"},
                    "UserDefinePath": {"string": "$output_dir/"},
                    "FileNameCounter": {"int": 1},
                    "PDFAllPages": {"int": 1}
                }
            ]
        }
    ]
}
EOF

    local device_id=$(epsonscan2 --list 2>&1 | grep "device ID" | sed 's/device ID ://' | xargs)

    echo -e "${CYAN}Scanning...${NC}"
    epsonscan2 --scan "$device_id" "$settings_file" 2>&1

    sleep 2

    if [[ -f "$output_file" ]] || ls "$output_dir"/scan_${timestamp}*.pdf 1>/dev/null 2>&1; then
        local scanned_file=$(ls -t "$output_dir"/scan_${timestamp}*.pdf 2>/dev/null | head -1)
        echo -e "${GREEN}[OK] Scan saved: $scanned_file${NC}"
        log "Quick scan completed: $scanned_file"
    else
        echo -e "${RED}[X] Scan may have failed${NC}"
        return 1
    fi

    rm -f "$settings_file"
}

# Process incoming queue
process_queue() {
    show_banner
    echo -e "${GREEN}Processing Incoming Scan Queue${NC}\n"

    local incoming_files=$(find "$INCOMING_DIR" -type f -name "*.pdf" 2>/dev/null)
    local count=$(echo "$incoming_files" | grep -c . 2>/dev/null || echo 0)

    if [[ $count -eq 0 ]]; then
        echo -e "${YELLOW}No documents in incoming queue${NC}"
        return 0
    fi

    echo -e "${CYAN}Found $count documents to process${NC}\n"

    # Check for document intelligence script
    if [[ -f "$SCANNER_SCRIPTS_DIR/smart_document_scanner_v1.0.0.sh" ]]; then
        echo -e "${CYAN}Running document intelligence...${NC}"
        bash "$SCANNER_SCRIPTS_DIR/smart_document_scanner_v1.0.0.sh"
    else
        echo -e "${YELLOW}Processing manually...${NC}"

        echo "$incoming_files" | while read -r file; do
            if [[ -f "$file" ]]; then
                local basename=$(basename "$file")
                local dest="$PROCESSED_DIR/scanned_documents/$basename"
                mkdir -p "$PROCESSED_DIR/scanned_documents"
                mv "$file" "$dest"
                echo -e "  Moved: $basename"
            fi
        done
    fi

    log "Processed incoming queue"
}

# Move recent scans to Skippy queue
import_scans() {
    show_banner
    echo -e "${GREEN}Import Recent Scans to Skippy Queue${NC}\n"

    if [[ ! -d "$SCAN_OUTPUT_DIR" ]]; then
        echo -e "${YELLOW}No scan sessions found${NC}"
        return 0
    fi

    # Find recent sessions with processed files
    local sessions=$(ls -t "$SCAN_OUTPUT_DIR" 2>/dev/null | head -5)

    if [[ -z "$sessions" ]]; then
        echo -e "${YELLOW}No scan sessions found${NC}"
        return 0
    fi

    echo -e "${CYAN}Recent scan sessions:${NC}"
    local i=1
    echo "$sessions" | while read -r session; do
        local path="$SCAN_OUTPUT_DIR/$session"
        local count=$(find "$path" -type f \( -name "*.pdf" -o -name "*.png" \) 2>/dev/null | wc -l)
        echo "  $i) $session ($count files)"
        ((i++))
    done

    echo ""
    echo -e "${YELLOW}Enter session number to import (or 'a' for all, 'q' to quit):${NC} "
    read -r choice

    case "$choice" in
        q|Q)
            return 0
            ;;
        a|A)
            echo "$sessions" | while read -r session; do
                import_session "$SCAN_OUTPUT_DIR/$session"
            done
            ;;
        [1-5])
            local selected=$(echo "$sessions" | sed -n "${choice}p")
            if [[ -n "$selected" ]]; then
                import_session "$SCAN_OUTPUT_DIR/$selected"
            fi
            ;;
        *)
            echo -e "${RED}Invalid selection${NC}"
            ;;
    esac
}

import_session() {
    local session_path="$1"

    echo -e "${CYAN}Importing from: $session_path${NC}"

    local files=$(find "$session_path" -type f \( -name "*.pdf" -o -name "*.png" \) 2>/dev/null)

    if [[ -z "$files" ]]; then
        echo -e "${YELLOW}No files to import${NC}"
        return 0
    fi

    local imported=0
    echo "$files" | while read -r file; do
        if [[ -f "$file" ]]; then
            local basename=$(basename "$file")
            cp "$file" "$INCOMING_DIR/$basename"
            echo -e "  Imported: $basename"
            ((imported++))
        fi
    done

    echo -e "${GREEN}[OK] Import complete${NC}"
    log "Imported scans from $session_path"
}

# Show help
show_help() {
    show_banner
    echo ""
    echo -e "${CYAN}Usage:${NC} skippy_scan_v1.0.0.sh [mode] [options]"
    echo ""
    echo -e "${CYAN}Modes:${NC}"
    echo "  gui       Launch graphical scanner (default)"
    echo "  smart     CLI scanner with OCR auto-naming"
    echo "  quick     Single document quick scan"
    echo "  status    Show scanner and queue status"
    echo "  process   Process incoming document queue"
    echo "  import    Import recent scans to Skippy queue"
    echo "  help      Show this help message"
    echo ""
    echo -e "${CYAN}Examples:${NC}"
    echo "  skippy_scan_v1.0.0.sh              # Launch GUI"
    echo "  skippy_scan_v1.0.0.sh smart        # Smart scan with OCR"
    echo "  skippy_scan_v1.0.0.sh quick        # Quick single scan"
    echo "  skippy_scan_v1.0.0.sh status       # Check status"
    echo ""
    echo -e "${CYAN}Paths:${NC}"
    echo "  Incoming:  $INCOMING_DIR"
    echo "  Processed: $PROCESSED_DIR"
    echo "  Scans:     $SCAN_OUTPUT_DIR"
    echo ""
}

# Interactive menu
interactive_menu() {
    show_banner
    echo ""

    if ! check_scanner 2>/dev/null; then
        echo -e "${YELLOW}Warning: Scanner may not be connected${NC}"
    fi
    echo ""

    echo -e "${CYAN}Select scanning mode:${NC}"
    echo "  1) GUI Scanner (graphical interface)"
    echo "  2) Smart Scanner (CLI with OCR)"
    echo "  3) Quick Scan (single document to queue)"
    echo "  4) Show Status"
    echo "  5) Process Incoming Queue"
    echo "  6) Import Recent Scans"
    echo "  7) Help"
    echo "  q) Quit"
    echo ""
    echo -e "${YELLOW}Enter choice:${NC} "
    read -r choice

    case "$choice" in
        1) launch_gui ;;
        2) launch_smart ;;
        3) quick_scan ;;
        4) show_status ;;
        5) process_queue ;;
        6) import_scans ;;
        7) show_help ;;
        q|Q) exit 0 ;;
        *) echo -e "${RED}Invalid choice${NC}" ;;
    esac
}

# Main
main() {
    local mode="${1:-}"

    case "$mode" in
        gui)
            launch_gui
            ;;
        smart)
            launch_smart
            ;;
        quick)
            quick_scan
            ;;
        status)
            show_status
            ;;
        process)
            process_queue
            ;;
        import)
            import_scans
            ;;
        help|--help|-h)
            show_help
            ;;
        "")
            interactive_menu
            ;;
        *)
            echo -e "${RED}Unknown mode: $mode${NC}"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
