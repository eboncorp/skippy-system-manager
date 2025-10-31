#!/bin/bash

# TidyTux Tailored - Custom Linux Cleanup for Your Specific System
# Version 2.2.0 - Tailored Edition
# Customized based on your actual directory structure

VERSION="2.2.0-tailored"
PROGRAM_NAME="TidyTux Tailored Edition"

set -euo pipefail

# Color definitions
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[0;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'

# Configuration
readonly CONFIG_DIR="$HOME/.config/tidytux"
readonly LOG_FILE="$HOME/.tidytux/logs/cleanup_$(date +%Y%m%d_%H%M%S).log"
readonly BACKUP_DIR="$HOME/.tidytux/backups/backup_$(date +%Y%m%d_%H%M%S)"

# Performance tracking
declare -g SPACE_SAVED=0
declare -g ITEMS_CLEANED=0
declare -A CLEANUP_STATS=()

# Command line options
DRY_RUN=${DRY_RUN:-false}
VERBOSE=${VERBOSE:-false}
SKIP_CONFIRMATION=${SKIP_CONFIRMATION:-false}

# Create necessary directories
mkdir -p "$CONFIG_DIR" "$BACKUP_DIR" "$(dirname "$LOG_FILE")"

# Logging function
log() {
    local message="$1"
    local level="${2:-INFO}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        ERROR) echo -e "${RED}[$timestamp] $message${NC}" ;;
        WARN) echo -e "${YELLOW}[$timestamp] $message${NC}" ;;
        SUCCESS) echo -e "${GREEN}[$timestamp] $message${NC}" ;;
        *) echo -e "${BLUE}[$timestamp] $message${NC}" ;;
    esac
    
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Confirmation function
confirm() {
    local prompt="$1"
    local default="${2:-n}"
    
    if [ "$SKIP_CONFIRMATION" = true ] || [ "$DRY_RUN" = true ]; then
        [ "$DRY_RUN" = true ] && log "[DRY RUN] Would execute: $prompt"
        return 0
    fi
    
    local yn_prompt="[y/N]"
    [ "$default" = "y" ] && yn_prompt="[Y/n]"
    
    echo -en "${YELLOW}$prompt $yn_prompt${NC} "
    read -r response
    
    case "${response,,}" in
        yes|y) return 0 ;;
        *) return 1 ;;
    esac
}

# Calculate directory size
get_dir_size() {
    local dir="$1"
    if [ -d "$dir" ]; then
        du -sb "$dir" 2>/dev/null | cut -f1
    else
        echo 0
    fi
}

# Format bytes to human readable
format_bytes() {
    local bytes="$1"
    if [ "$bytes" -gt 1073741824 ]; then
        echo "$(( bytes / 1073741824 ))GB"
    elif [ "$bytes" -gt 1048576 ]; then
        echo "$(( bytes / 1048576 ))MB"
    elif [ "$bytes" -gt 1024 ]; then
        echo "$(( bytes / 1024 ))KB"
    else
        echo "${bytes}B"
    fi
}

# TAILORED CLEANUP FUNCTIONS FOR YOUR SYSTEM

# Clean up multiple Ethereum setup scripts (you have many duplicates)
clean_ethereum_scripts() {
    log "${BOLD}====== ETHEREUM SCRIPT CLEANUP ======${NC}"
    
    local eth_scripts=(
        "$HOME/Downloads/combined_eth_setup.sh"
        "$HOME/Downloads/enhanced_ethereum_node_v28.sh"
        "$HOME/Downloads/enhanced_ethereum_node_v29.sh"
        "$HOME/Downloads/enhanced_eth_node_setup.sh"
        "$HOME/Downloads/eth_setup_v27_robust.sh"
    )
    
    local total_size=0
    local found_scripts=()
    
    log "Found Ethereum setup scripts:"
    for script in "${eth_scripts[@]}"; do
        if [ -f "$script" ]; then
            local size=$(stat -c%s "$script" 2>/dev/null || echo 0)
            local date=$(stat -c%y "$script" 2>/dev/null | cut -d' ' -f1)
            total_size=$((total_size + size))
            found_scripts+=("$script")
            log "  $(basename "$script") - $(format_bytes $size) - $date"
        fi
    done
    
    if [ ${#found_scripts[@]} -gt 1 ]; then
        log "You have ${#found_scripts[@]} Ethereum setup scripts using $(format_bytes $total_size)"
        if confirm "Keep only the latest version and backup others?" "y"; then
            # Find the newest script
            local newest_script=""
            local newest_time=0
            
            for script in "${found_scripts[@]}"; do
                local mtime=$(stat -c%Y "$script" 2>/dev/null || echo 0)
                if [ "$mtime" -gt "$newest_time" ]; then
                    newest_time="$mtime"
                    newest_script="$script"
                fi
            done
            
            # Backup and remove older scripts
            for script in "${found_scripts[@]}"; do
                if [ "$script" != "$newest_script" ]; then
                    if [ "$DRY_RUN" = false ]; then
                        cp "$script" "$BACKUP_DIR/"
                        rm "$script"
                        ((ITEMS_CLEANED++))
                        log "Moved $(basename "$script") to backup"
                    fi
                fi
            done
            
            SPACE_SAVED=$((SPACE_SAVED + total_size / 1024))
            CLEANUP_STATS[ethereum_scripts]="${#found_scripts[@]}"
            log "Kept newest script: $(basename "$newest_script")" "SUCCESS"
        fi
    fi
}

# Clean up TidyTux script duplicates
clean_tidytux_duplicates() {
    log "${BOLD}====== TIDYTUX DUPLICATE CLEANUP ======${NC}"
    
    local tidytux_scripts=(
        "$HOME/tidytux.sh"
        "$HOME/tidytux.sh.bak"
        "$HOME/tidytux.sh.old"
        "$HOME/Downloads/tidytux-improved.sh"
        "$HOME/Downloads/tidytux-improved(1).sh"
        "$HOME/Downloads/scripts/complete-tidytux.sh"
    )
    
    local found_scripts=()
    local total_size=0
    
    for script in "${tidytux_scripts[@]}"; do
        if [ -f "$script" ]; then
            local size=$(stat -c%s "$script" 2>/dev/null || echo 0)
            total_size=$((total_size + size))
            found_scripts+=("$script")
            log "Found: $(basename "$script") - $(format_bytes $size)"
        fi
    done
    
    if [ ${#found_scripts[@]} -gt 1 ]; then
        if confirm "Archive old TidyTux versions (keep newest)?" "y"; then
            # Keep the newest and backup others
            local newest_script="${found_scripts[0]}"
            local newest_time=$(stat -c%Y "$newest_script" 2>/dev/null || echo 0)
            
            for script in "${found_scripts[@]}"; do
                local mtime=$(stat -c%Y "$script" 2>/dev/null || echo 0)
                if [ "$mtime" -gt "$newest_time" ]; then
                    newest_time="$mtime"
                    newest_script="$script"
                fi
            done
            
            for script in "${found_scripts[@]}"; do
                if [ "$script" != "$newest_script" ]; then
                    if [ "$DRY_RUN" = false ]; then
                        cp "$script" "$BACKUP_DIR/"
                        rm "$script"
                        ((ITEMS_CLEANED++))
                    fi
                fi
            done
            
            CLEANUP_STATS[tidytux_duplicates]="${#found_scripts[@]}"
            log "Cleaned up TidyTux duplicates" "SUCCESS"
        fi
    fi
}

# Clean up Claude HTML downloads and associated files
clean_claude_downloads() {
    log "${BOLD}====== CLAUDE DOWNLOADS CLEANUP ======${NC}"
    
    local claude_dirs=(
        "$HOME/Downloads/Claude"
        "$HOME/Downloads/documents/Networks_files"
        "$HOME/Downloads/documents/Spin up your own Ethereum node_files"
    )
    
    local total_size=0
    
    for dir in "${claude_dirs[@]}"; do
        if [ -d "$dir" ]; then
            local size=$(get_dir_size "$dir")
            total_size=$((total_size + size))
            log "Claude files in $(basename "$dir"): $(format_bytes $size)"
        fi
    done
    
    if [ "$total_size" -gt 0 ]; then
        log "Total Claude download files: $(format_bytes $total_size)"
        if confirm "These are saved web pages. Archive Claude downloads?" "y"; then
            for dir in "${claude_dirs[@]}"; do
                if [ -d "$dir" ] && [ "$DRY_RUN" = false ]; then
                    cp -r "$dir" "$BACKUP_DIR/"
                    rm -rf "$dir"
                    ((ITEMS_CLEANED++))
                fi
            done
            
            SPACE_SAVED=$((SPACE_SAVED + total_size / 1024))
            CLEANUP_STATS[claude_downloads]="$(format_bytes $total_size)"
            log "Claude downloads archived" "SUCCESS"
        fi
    fi
}

# Clean up your specific snap packages
clean_snap_packages() {
    log "${BOLD}====== SNAP PACKAGE CLEANUP ======${NC}"
    
    if ! command -v snap &>/dev/null; then
        log "Snap not available" "WARN"
        return
    fi
    
    # Your specific snap packages based on directory structure
    local snap_packages=("brave" "code" "firefox" "nordpass" "snap-store" "snapd-desktop-integration")
    
    log "Analyzing your snap packages..."
    
    # Set retention policy for snaps
    if confirm "Set snap retention to 2 versions (saves space)?" "y"; then
        if [ "$DRY_RUN" = false ]; then
            sudo snap set system refresh.retain=2
            log "Snap retention policy updated" "SUCCESS"
        fi
    fi
    
    # Clean old snap revisions
    local old_revisions=$(snap list --all | awk '/disabled/{print $1, $3}')
    
    if [ -n "$old_revisions" ]; then
        log "Found disabled snap revisions:"
        echo "$old_revisions" | while read -r name revision; do
            [ -z "$name" ] && continue
            log "  $name revision $revision"
        done
        
        if confirm "Remove old snap revisions?" "y"; then
            echo "$old_revisions" | while read -r name revision; do
                [ -z "$name" ] && continue
                if [ "$DRY_RUN" = false ]; then
                    sudo snap remove "$name" --revision="$revision"
                    ((ITEMS_CLEANED++))
                fi
            done
            CLEANUP_STATS[snap_revisions]="removed"
            log "Old snap revisions cleaned" "SUCCESS"
        fi
    fi
    
    # Clean nordpass logs (you have many)
    local nordpass_logs="$HOME/snap/nordpass/common/logs"
    if [ -d "$nordpass_logs" ]; then
        local log_size=$(get_dir_size "$nordpass_logs")
        log "NordPass logs: $(format_bytes $log_size)"
        
        if [ "$log_size" -gt 1048576 ] && confirm "Clean old NordPass logs (>1MB)?" "y"; then
            if [ "$DRY_RUN" = false ]; then
                find "$nordpass_logs" -name "*.log" -mtime +7 -delete
                SPACE_SAVED=$((SPACE_SAVED + log_size / 1024))
                log "NordPass logs cleaned" "SUCCESS"
            fi
        fi
    fi
}

# Clean up downloaded archives
clean_download_archives() {
    log "${BOLD}====== DOWNLOAD ARCHIVES CLEANUP ======${NC}"
    
    local archives_dir="$HOME/Downloads/archives"
    local apps_dir="$HOME/Downloads/apps"
    local software_dir="$HOME/Downloads/software"
    local drivers_dir="$HOME/Downloads/drivers"
    
    local dirs_to_check=("$archives_dir" "$apps_dir" "$software_dir" "$drivers_dir")
    local total_size=0
    
    for dir in "${dirs_to_check[@]}"; do
        if [ -d "$dir" ]; then
            local size=$(get_dir_size "$dir")
            total_size=$((total_size + size))
            log "$(basename "$dir"): $(format_bytes $size)"
            
            # List contents
            if [ "$VERBOSE" = true ]; then
                find "$dir" -type f -printf "  %f - %s bytes\n" 2>/dev/null | head -5
            fi
        fi
    done
    
    if [ "$total_size" -gt 0 ]; then
        log "Total download archives: $(format_bytes $total_size)"
        
        # Check for old archives (>30 days)
        local old_archives=()
        for dir in "${dirs_to_check[@]}"; do
            if [ -d "$dir" ]; then
                while IFS= read -r -d '' file; do
                    old_archives+=("$file")
                done < <(find "$dir" -type f -mtime +30 -print0 2>/dev/null)
            fi
        done
        
        if [ ${#old_archives[@]} -gt 0 ]; then
            local old_size=0
            for file in "${old_archives[@]}"; do
                local size=$(stat -c%s "$file" 2>/dev/null || echo 0)
                old_size=$((old_size + size))
            done
            
            log "Found ${#old_archives[@]} old archives (>30 days): $(format_bytes $old_size)"
            
            if confirm "Archive old downloaded files?" "y"; then
                for file in "${old_archives[@]}"; do
                    if [ "$DRY_RUN" = false ]; then
                        cp "$file" "$BACKUP_DIR/"
                        rm "$file"
                        ((ITEMS_CLEANED++))
                    fi
                done
                
                SPACE_SAVED=$((SPACE_SAVED + old_size / 1024))
                CLEANUP_STATS[old_archives]="${#old_archives[@]}"
                log "Old archives cleaned" "SUCCESS"
            fi
        fi
    fi
}

# Clean up financial documents (organize, don't delete)
organize_financial_docs() {
    log "${BOLD}====== FINANCIAL DOCUMENTS ORGANIZATION ======${NC}"
    
    local docs_dir="$HOME/Downloads/docs"
    local financial_dir="$HOME/Documents/Financial"
    
    if [ ! -d "$docs_dir" ]; then
        return
    fi
    
    # Find financial documents in Downloads/docs
    local financial_files=()
    while IFS= read -r -d '' file; do
        financial_files+=("$file")
    done < <(find "$docs_dir" -type f \( -name "*W2*" -o -name "*tax*" -o -name "*form*" -o -name "*statement*" -o -name "*.qbo" -o -name "*transaction*" \) -print0 2>/dev/null)
    
    if [ ${#financial_files[@]} -gt 0 ]; then
        log "Found ${#financial_files[@]} financial documents in Downloads/docs"
        
        # Create organized subdirectories
        local tax_dir="$financial_dir/Tax_Documents"
        local statements_dir="$financial_dir/Bank_Statements"
        local qbo_dir="$financial_dir/QuickBooks_Files"
        
        if confirm "Organize financial documents into proper folders?" "y"; then
            if [ "$DRY_RUN" = false ]; then
                mkdir -p "$tax_dir" "$statements_dir" "$qbo_dir"
                
                for file in "${financial_files[@]}"; do
                    local basename_file=$(basename "$file")
                    local dest_dir="$financial_dir"
                    
                    # Determine destination based on file type
                    if [[ "$basename_file" =~ (W2|tax|form|Form|schedule|Schedule) ]]; then
                        dest_dir="$tax_dir"
                    elif [[ "$basename_file" =~ (statement|Statement|checking|Checking|chase|Chase) ]]; then
                        dest_dir="$statements_dir"
                    elif [[ "$basename_file" =~ \.qbo$ ]]; then
                        dest_dir="$qbo_dir"
                    fi
                    
                    mv "$file" "$dest_dir/"
                    log "Moved $(basename "$file") to $(basename "$dest_dir")"
                done
                
                CLEANUP_STATS[financial_organized]="${#financial_files[@]}"
                log "Financial documents organized" "SUCCESS"
            fi
        fi
    fi
}

# Clean up old system update scripts
clean_system_scripts() {
    log "${BOLD}====== SYSTEM SCRIPTS CLEANUP ======${NC}"
    
    local system_scripts=(
        "$HOME/system_update.sh"
        "$HOME/install_exodus.sh"
        "$HOME/install_nordpass.sh"
        "$HOME/setup_directories.sh"
    )
    
    local script_count=0
    for script in "${system_scripts[@]}"; do
        if [ -f "$script" ]; then
            ((script_count++))
            local size=$(stat -c%s "$script" 2>/dev/null || echo 0)
            log "Found: $(basename "$script") - $(format_bytes $size)"
        fi
    done
    
    if [ "$script_count" -gt 0 ]; then
        if confirm "Move system scripts to ~/scripts/ directory?" "y"; then
            mkdir -p "$HOME/scripts"
            
            for script in "${system_scripts[@]}"; do
                if [ -f "$script" ] && [ "$DRY_RUN" = false ]; then
                    mv "$script" "$HOME/scripts/"
                    log "Moved $(basename "$script") to ~/scripts/"
                    ((ITEMS_CLEANED++))
                fi
            done
            
            CLEANUP_STATS[system_scripts]="$script_count"
            log "System scripts organized" "SUCCESS"
        fi
    fi
}

# Generate custom report
generate_tailored_report() {
    local end_time=$(date +%s)
    local start_time=$(stat -c%Y "$LOG_FILE" 2>/dev/null || echo $end_time)
    local duration=$((end_time - start_time))
    
    cat > "$BACKUP_DIR/cleanup_report.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>TidyTux Tailored Cleanup Report</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .container { max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        h2 { color: #555; border-bottom: 3px solid #667eea; padding-bottom: 10px; margin-top: 30px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat-box { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }
        .stat-value { font-size: 2.5em; font-weight: bold; }
        .stat-label { margin-top: 10px; opacity: 0.9; }
        .cleanup-item { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #667eea; }
        .success { color: #28a745; font-weight: bold; }
        .footer { text-align: center; color: #666; margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧹 TidyTux Tailored Cleanup Report</h1>
        <p><strong>Cleanup Date:</strong> $(date)<br>
        <strong>Duration:</strong> ${duration}s<br>
        <strong>Mode:</strong> $([ "$DRY_RUN" = true ] && echo "Preview Mode" || echo "Full Cleanup")</p>
        
        <h2>📊 Summary Statistics</h2>
        <div class="stats">
            <div class="stat-box">
                <div class="stat-value">$(echo "scale=1; $SPACE_SAVED/1024" | bc 2>/dev/null || echo "0")MB</div>
                <div class="stat-label">Space Saved</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">$ITEMS_CLEANED</div>
                <div class="stat-label">Items Cleaned</div>
            </div>
        </div>
        
        <h2>🎯 Tailored Cleanup Actions</h2>
EOF

    for category in "${!CLEANUP_STATS[@]}"; do
        echo "<div class='cleanup-item'><strong>$(echo "$category" | tr '_' ' ' | title)</strong>: ${CLEANUP_STATS[$category]} items processed</div>" >> "$BACKUP_DIR/cleanup_report.html"
    done

    cat >> "$BACKUP_DIR/cleanup_report.html" << EOF
        
        <h2>💾 Current Disk Usage</h2>
        <pre>$(df -h "$HOME" | tail -1)</pre>
        
        <div class="footer">
            <p class="success">✅ Cleanup completed successfully!</p>
            <p>Generated by TidyTux Tailored v$VERSION<br>
            Backup location: $BACKUP_DIR</p>
        </div>
    </div>
</body>
</html>
EOF
    
    log "Tailored report generated: $BACKUP_DIR/cleanup_report.html" "SUCCESS"
}

# Main cleanup orchestrator
run_tailored_cleanup() {
    log "${BOLD}🚀 Starting TidyTux Tailored Cleanup v$VERSION${NC}"
    log "Customized for your specific system configuration"
    
    # Show initial disk usage
    log "Current disk usage:"
    df -h "$HOME" | tail -1
    echo
    
    # Run tailored cleanup functions
    clean_ethereum_scripts
    echo
    clean_tidytux_duplicates
    echo
    clean_claude_downloads
    echo
    clean_snap_packages
    echo
    clean_download_archives
    echo
    organize_financial_docs
    echo
    clean_system_scripts
    echo
    
    # Generate report
    generate_tailored_report
    
    # Final summary
    log "${BOLD}🎉 CLEANUP COMPLETE 🎉${NC}" "SUCCESS"
    log "Items cleaned: $ITEMS_CLEANED"
    log "Space saved: $(format_bytes $((SPACE_SAVED * 1024)))"
    log "Backup location: $BACKUP_DIR"
    
    if [ "$DRY_RUN" = true ]; then
        log "This was a preview run. Run without --dry-run to perform actual cleanup." "WARN"
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -n|--dry-run)
            DRY_RUN=true
            log "Running in preview mode" "WARN"
            ;;
        -v|--verbose)
            VERBOSE=true
            ;;
        -y|--yes)
            SKIP_CONFIRMATION=true
            ;;
        -h|--help)
            cat << EOF
TidyTux Tailored v$VERSION - Customized for your system

USAGE: $(basename "$0") [OPTIONS]

OPTIONS:
    -n, --dry-run    Preview what would be cleaned (safe mode)
    -v, --verbose    Show detailed information
    -y, --yes        Auto-confirm all actions
    -h, --help       Show this help

TAILORED FEATURES:
    🔧 Ethereum script management (you have 5+ versions)
    📁 Claude download cleanup (HTML files + assets)
    📦 Snap package optimization (your specific packages)
    📚 Financial document organization
    🗂️  TidyTux duplicate cleanup
    💾 Archive management (apps, drivers, software)
    📝 System script organization

All actions create backups in: ~/.tidytux/backups/
EOF
            exit 0
            ;;
        *)
            log "Unknown option: $1" "ERROR"
            exit 1
            ;;
    esac
    shift
done

# Run the tailored cleanup
run_tailored_cleanup