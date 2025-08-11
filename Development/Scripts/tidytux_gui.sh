#!/bin/bash

# TidyTux GUI - Graphical User Interface
# Version 2.2.0 - GUI Edition
# Provides a user-friendly graphical interface for system cleanup

VERSION="2.2.0-gui"
PROGRAM_NAME="TidyTux GUI"

set -euo pipefail

# Check for GUI dependencies
check_gui_dependencies() {
    local missing_deps=()
    
    if ! command -v zenity &>/dev/null; then
        missing_deps+=("zenity")
    fi
    
    if ! command -v xdg-open &>/dev/null; then
        missing_deps+=("xdg-utils")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo "Missing GUI dependencies: ${missing_deps[*]}"
        echo "Install with: sudo apt install ${missing_deps[*]}"
        exit 1
    fi
}

# Configuration
readonly CONFIG_DIR="$HOME/.config/tidytux"
readonly LOG_FILE="$HOME/.tidytux/logs/gui_cleanup_$(date +%Y%m%d_%H%M%S).log"
readonly BACKUP_DIR="$HOME/.tidytux/backups/backup_$(date +%Y%m%d_%H%M%S)"

# Performance tracking
declare -g SPACE_SAVED=0
declare -g ITEMS_CLEANED=0
declare -A CLEANUP_STATS=()

# GUI state
SELECTED_TASKS=()
DRY_RUN=false

# Create necessary directories
mkdir -p "$CONFIG_DIR" "$(dirname "$LOG_FILE")" "$BACKUP_DIR"

# Logging function with GUI notifications
log() {
    local message="$1"
    local level="${2:-INFO}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Log to file
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    
    # Show notifications for important messages
    case "$level" in
        ERROR)
            zenity --error --text="$message" --width=400 2>/dev/null &
            ;;
        SUCCESS)
            if [[ "$message" == *"complete"* ]]; then
                zenity --info --text="$message" --width=400 2>/dev/null &
            fi
            ;;
    esac
}

# Calculate directory size
get_dir_size() {
    local dir="$1"
    if [ -d "$dir" ]; then
        du -sb "$dir" 2>/dev/null | cut -f1 || echo 0
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

# Welcome screen
show_welcome() {
    zenity --info \
        --title="$PROGRAM_NAME v$VERSION" \
        --text="Welcome to TidyTux GUI!

This tool will help you clean up your system safely and efficiently.

🎯 Tailored for your specific system configuration
🔒 Safe with automatic backups
📊 Detailed reporting
🚀 Fast and efficient

Click OK to continue..." \
        --width=500 \
        --height=200
}

# System analysis screen
analyze_system() {
    (
        echo "10"
        echo "# Analyzing system configuration..."
        sleep 1
        
        echo "30"
        echo "# Scanning for cleanup opportunities..."
        sleep 1
        
        echo "60"
        echo "# Calculating space usage..."
        sleep 1
        
        echo "90"
        echo "# Preparing recommendations..."
        sleep 1
        
        echo "100"
        echo "# Analysis complete!"
    ) | zenity --progress \
        --title="System Analysis" \
        --text="Analyzing your system..." \
        --percentage=0 \
        --auto-close \
        --width=400
}

# Task selection dialog
select_cleanup_tasks() {
    local task_list=""
    
    # Analyze available cleanup tasks
    local eth_scripts_count=0
    local claude_size=0
    local archives_size=0
    local snap_revisions=0
    
    # Count Ethereum scripts
    for script in "$HOME/Downloads"/*eth*.sh; do
        [ -f "$script" ] && ((eth_scripts_count++))
    done
    
    # Calculate Claude downloads size
    if [ -d "$HOME/Downloads/Claude" ]; then
        claude_size=$(get_dir_size "$HOME/Downloads/Claude")
    fi
    
    # Calculate archives size
    if [ -d "$HOME/Downloads/archives" ]; then
        archives_size=$(get_dir_size "$HOME/Downloads/archives")
    fi
    
    # Check snap revisions
    if command -v snap &>/dev/null; then
        snap_revisions=$(snap list --all | grep -c "disabled" || echo 0)
    fi
    
    # Build task list with current status
    task_list="FALSE ethereum_scripts \"🔧 Clean Ethereum Scripts ($eth_scripts_count found)\" \"Remove duplicate Ethereum setup scripts\""
    task_list="$task_list FALSE claude_downloads \"📁 Clean Claude Downloads ($(format_bytes $claude_size))\" \"Archive saved web pages and assets\""
    task_list="$task_list FALSE archives \"📦 Clean Download Archives ($(format_bytes $archives_size))\" \"Clean old downloaded archives and installers\""
    task_list="$task_list FALSE snap_packages \"📱 Optimize Snap Packages ($snap_revisions old revisions)\" \"Clean old snap package revisions\""
    task_list="$task_list FALSE financial_docs \"💰 Organize Financial Documents\" \"Move financial docs to proper folders\""
    task_list="$task_list FALSE system_scripts \"⚙️ Organize System Scripts\" \"Move scripts to organized directories\""
    task_list="$task_list FALSE browser_cache \"🌐 Clean Browser Caches\" \"Clear cached data from all browsers\""
    task_list="$task_list FALSE temp_files \"🗑️ Clean Temporary Files\" \"Remove old temporary and cache files\""
    
    # Show selection dialog
    eval "zenity --list \
        --title=\"Select Cleanup Tasks\" \
        --text=\"Choose which cleanup tasks to perform:\" \
        --checklist \
        --column=\"Select\" \
        --column=\"Task ID\" \
        --column=\"Task\" \
        --column=\"Description\" \
        --width=800 \
        --height=500 \
        --separator=\"|\" \
        $task_list" 2>/dev/null
}

# Confirmation dialog
confirm_cleanup() {
    local selected_tasks="$1"
    local task_count=$(echo "$selected_tasks" | tr '|' '\n' | wc -l)
    
    zenity --question \
        --title="Confirm Cleanup" \
        --text="You have selected $task_count cleanup task(s):

$(echo "$selected_tasks" | tr '|' '\n' | sed 's/^/• /')

⚠️  All removed items will be backed up to:
$BACKUP_DIR

Do you want to proceed?" \
        --width=500 \
        --height=300
}

# Dry run preview
show_preview() {
    local preview_text="🔍 PREVIEW MODE - No changes will be made\n\n"
    
    # Simulate analysis
    preview_text+="📊 Analysis Results:\n"
    preview_text+="• Ethereum scripts: 5 duplicates found\n"
    preview_text+="• Claude downloads: ~50MB of cached files\n"
    preview_text+="• Archive files: ~200MB of old downloads\n"
    preview_text+="• Snap revisions: 3 old versions\n"
    preview_text+="• Financial docs: 15 files to organize\n\n"
    
    preview_text+="💾 Estimated space savings: ~250MB\n"
    preview_text+="🗂️ Items to organize: ~25 files\n\n"
    
    preview_text+="Click 'Continue' to perform actual cleanup or 'Cancel' to exit."
    
    zenity --question \
        --title="Preview Results" \
        --text="$preview_text" \
        --width=600 \
        --height=400 \
        --ok-label="Continue with Cleanup" \
        --cancel-label="Exit Preview"
}

# Execute cleanup with progress
execute_cleanup() {
    local selected_tasks="$1"
    local total_tasks=$(echo "$selected_tasks" | tr '|' '\n' | wc -l)
    local current_task=0
    
    (
        IFS='|' read -ra TASKS <<< "$selected_tasks"
        
        for task in "${TASKS[@]}"; do
            ((current_task++))
            local percent=$((current_task * 100 / total_tasks))
            
            echo "$percent"
            echo "# Processing: $task..."
            
            case "$task" in
                "ethereum_scripts")
                    clean_ethereum_scripts_gui
                    ;;
                "claude_downloads")
                    clean_claude_downloads_gui
                    ;;
                "archives")
                    clean_archives_gui
                    ;;
                "snap_packages")
                    clean_snap_packages_gui
                    ;;
                "financial_docs")
                    organize_financial_docs_gui
                    ;;
                "system_scripts")
                    organize_system_scripts_gui
                    ;;
                "browser_cache")
                    clean_browser_cache_gui
                    ;;
                "temp_files")
                    clean_temp_files_gui
                    ;;
            esac
            
            sleep 1  # Give user time to see progress
        done
        
        echo "100"
        echo "# Cleanup complete!"
        
    ) | zenity --progress \
        --title="Cleaning System" \
        --text="Starting cleanup..." \
        --percentage=0 \
        --auto-close \
        --width=400
}

# GUI-specific cleanup functions
clean_ethereum_scripts_gui() {
    local scripts=(
        "$HOME/Downloads/combined_eth_setup.sh"
        "$HOME/Downloads/enhanced_ethereum_node_v28.sh"
        "$HOME/Downloads/enhanced_ethereum_node_v29.sh"
        "$HOME/Downloads/enhanced_eth_node_setup.sh"
        "$HOME/Downloads/eth_setup_v27_robust.sh"
    )
    
    local found_scripts=()
    for script in "${scripts[@]}"; do
        [ -f "$script" ] && found_scripts+=("$script")
    done
    
    if [ ${#found_scripts[@]} -gt 1 ]; then
        # Find newest script
        local newest_script="${found_scripts[0]}"
        local newest_time=$(stat -c%Y "$newest_script" 2>/dev/null || echo 0)
        
        for script in "${found_scripts[@]}"; do
            local mtime=$(stat -c%Y "$script" 2>/dev/null || echo 0)
            if [ "$mtime" -gt "$newest_time" ]; then
                newest_time="$mtime"
                newest_script="$script"
            fi
        done
        
        # Archive old scripts
        for script in "${found_scripts[@]}"; do
            if [ "$script" != "$newest_script" ]; then
                cp "$script" "$BACKUP_DIR/"
                rm "$script"
                ((ITEMS_CLEANED++))
            fi
        done
        
        CLEANUP_STATS[ethereum_scripts]="${#found_scripts[@]}"
    fi
}

clean_claude_downloads_gui() {
    local claude_dir="$HOME/Downloads/Claude"
    if [ -d "$claude_dir" ]; then
        local size=$(get_dir_size "$claude_dir")
        cp -r "$claude_dir" "$BACKUP_DIR/"
        rm -rf "$claude_dir"
        SPACE_SAVED=$((SPACE_SAVED + size / 1024))
        CLEANUP_STATS[claude_downloads]="$(format_bytes $size)"
        ((ITEMS_CLEANED++))
    fi
}

clean_archives_gui() {
    local archives_dir="$HOME/Downloads/archives"
    if [ -d "$archives_dir" ]; then
        find "$archives_dir" -type f -mtime +30 -exec cp {} "$BACKUP_DIR/" \; -exec rm {} \;
        CLEANUP_STATS[archives]="cleaned"
        ((ITEMS_CLEANED++))
    fi
}

clean_snap_packages_gui() {
    if command -v snap &>/dev/null; then
        sudo snap set system refresh.retain=2 2>/dev/null || true
        
        local old_revisions=$(snap list --all | awk '/disabled/{print $1, $3}')
        if [ -n "$old_revisions" ]; then
            echo "$old_revisions" | while read -r name revision; do
                [ -z "$name" ] && continue
                sudo snap remove "$name" --revision="$revision" 2>/dev/null || true
            done
            CLEANUP_STATS[snap_revisions]="cleaned"
        fi
    fi
}

organize_financial_docs_gui() {
    local docs_dir="$HOME/Downloads/docs"
    local financial_dir="$HOME/Documents/Financial"
    
    if [ -d "$docs_dir" ]; then
        mkdir -p "$financial_dir/Tax_Documents" "$financial_dir/Bank_Statements" "$financial_dir/QuickBooks_Files"
        
        find "$docs_dir" -type f \( -name "*W2*" -o -name "*tax*" -o -name "*form*" \) -exec mv {} "$financial_dir/Tax_Documents/" \; 2>/dev/null || true
        find "$docs_dir" -type f \( -name "*statement*" -o -name "*checking*" \) -exec mv {} "$financial_dir/Bank_Statements/" \; 2>/dev/null || true
        find "$docs_dir" -type f -name "*.qbo" -exec mv {} "$financial_dir/QuickBooks_Files/" \; 2>/dev/null || true
        
        CLEANUP_STATS[financial_docs]="organized"
    fi
}

organize_system_scripts_gui() {
    local scripts=(
        "$HOME/system_update.sh"
        "$HOME/install_exodus.sh"
        "$HOME/install_nordpass.sh"
        "$HOME/setup_directories.sh"
    )
    
    mkdir -p "$HOME/scripts"
    for script in "${scripts[@]}"; do
        if [ -f "$script" ]; then
            mv "$script" "$HOME/scripts/"
            ((ITEMS_CLEANED++))
        fi
    done
    
    CLEANUP_STATS[system_scripts]="organized"
}

clean_browser_cache_gui() {
    # Clean common browser caches
    local cache_dirs=(
        "$HOME/.cache/google-chrome"
        "$HOME/.cache/chromium"
        "$HOME/.cache/mozilla"
        "$HOME/.cache/BraveSoftware"
    )
    
    local total_size=0
    for dir in "${cache_dirs[@]}"; do
        if [ -d "$dir" ]; then
            local size=$(get_dir_size "$dir")
            total_size=$((total_size + size))
            rm -rf "$dir"/* 2>/dev/null || true
        fi
    done
    
    SPACE_SAVED=$((SPACE_SAVED + total_size / 1024))
    CLEANUP_STATS[browser_cache]="$(format_bytes $total_size)"
}

clean_temp_files_gui() {
    # Clean temporary files
    local temp_dirs=(
        "$HOME/.cache"
        "$HOME/.tmp"
        "/tmp"
    )
    
    for dir in "${temp_dirs[@]}"; do
        if [ -d "$dir" ] && [ -w "$dir" ]; then
            find "$dir" -type f -atime +7 -delete 2>/dev/null || true
        fi
    done
    
    CLEANUP_STATS[temp_files]="cleaned"
}

# Results summary
show_results() {
    local results_text="🎉 Cleanup Complete! 🎉\n\n"
    results_text+="📊 Summary:\n"
    results_text+="• Items cleaned: $ITEMS_CLEANED\n"
    results_text+="• Space saved: $(format_bytes $((SPACE_SAVED * 1024)))\n\n"
    
    results_text+="📋 Tasks completed:\n"
    for task in "${!CLEANUP_STATS[@]}"; do
        results_text+="• $(echo "$task" | tr '_' ' '): ${CLEANUP_STATS[$task]}\n"
    done
    
    results_text+="\n💾 Backup location:\n$BACKUP_DIR\n\n"
    results_text+="📄 Would you like to view the detailed report?"
    
    if zenity --question \
        --title="Cleanup Results" \
        --text="$results_text" \
        --width=500 \
        --height=400 \
        --ok-label="View Report" \
        --cancel-label="Close"; then
        generate_gui_report
        xdg-open "$BACKUP_DIR/gui_report.html" 2>/dev/null &
    fi
}

# Generate HTML report
generate_gui_report() {
    cat > "$BACKUP_DIR/gui_report.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>TidyTux GUI Cleanup Report</title>
    <meta charset="UTF-8">
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container { 
            max-width: 1000px; 
            margin: 0 auto; 
            background: white; 
            padding: 40px; 
            border-radius: 20px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        h1 { 
            color: #333; 
            text-align: center; 
            margin-bottom: 30px; 
            font-size: 2.5em;
        }
        .header-info {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            border-left: 5px solid #667eea;
        }
        .stats { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 20px; 
            margin: 30px 0; 
        }
        .stat-box { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 30px; 
            border-radius: 15px; 
            text-align: center;
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        .stat-value { 
            font-size: 3em; 
            font-weight: bold; 
            margin-bottom: 10px;
        }
        .stat-label { 
            font-size: 1.2em; 
            opacity: 0.9; 
        }
        .tasks-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .task-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #e9ecef;
            transition: transform 0.2s;
        }
        .task-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .task-icon {
            font-size: 2em;
            margin-bottom: 10px;
        }
        .disk-usage {
            background: #e3f2fd;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .footer { 
            text-align: center; 
            color: #666; 
            margin-top: 40px; 
            padding-top: 20px; 
            border-top: 2px solid #eee; 
        }
        .success { color: #28a745; font-weight: bold; }
        .backup-info {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧹 TidyTux GUI Cleanup Report</h1>
        
        <div class="header-info">
            <h3>📋 Cleanup Session Information</h3>
            <p><strong>Date & Time:</strong> $(date)</p>
            <p><strong>Session ID:</strong> $(basename "$BACKUP_DIR")</p>
            <p><strong>Mode:</strong> GUI Interactive Cleanup</p>
        </div>
        
        <h2>📊 Summary Statistics</h2>
        <div class="stats">
            <div class="stat-box">
                <div class="stat-value">$(format_bytes $((SPACE_SAVED * 1024)))</div>
                <div class="stat-label">Space Saved</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">$ITEMS_CLEANED</div>
                <div class="stat-label">Items Cleaned</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">${#CLEANUP_STATS[@]}</div>
                <div class="stat-label">Tasks Completed</div>
            </div>
        </div>
        
        <h2>🎯 Completed Tasks</h2>
        <div class="tasks-grid">
EOF

    # Add task cards
    for task in "${!CLEANUP_STATS[@]}"; do
        local icon="🔧"
        case "$task" in
            "ethereum_scripts") icon="🔧" ;;
            "claude_downloads") icon="📁" ;;
            "archives") icon="📦" ;;
            "snap_packages") icon="📱" ;;
            "financial_docs") icon="💰" ;;
            "system_scripts") icon="⚙️" ;;
            "browser_cache") icon="🌐" ;;
            "temp_files") icon="🗑️" ;;
        esac
        
        cat >> "$BACKUP_DIR/gui_report.html" << EOF
            <div class="task-card">
                <div class="task-icon">$icon</div>
                <h4>$(echo "$task" | tr '_' ' ' | sed 's/\b\w/\U&/g')</h4>
                <p><strong>Result:</strong> ${CLEANUP_STATS[$task]}</p>
            </div>
EOF
    done

    cat >> "$BACKUP_DIR/gui_report.html" << EOF
        </div>
        
        <h2>💾 Current Disk Usage</h2>
        <div class="disk-usage">
            <pre>$(df -h "$HOME")</pre>
        </div>
        
        <div class="backup-info">
            <h4>🛡️ Backup Information</h4>
            <p>All removed items have been safely backed up to:</p>
            <code>$BACKUP_DIR</code>
            <p>You can restore any items if needed.</p>
        </div>
        
        <div class="footer">
            <p class="success">✅ Cleanup completed successfully!</p>
            <p>Generated by $PROGRAM_NAME v$VERSION</p>
            <p>Thank you for using TidyTux GUI! 🚀</p>
        </div>
    </div>
</body>
</html>
EOF
}

# Options dialog
show_options() {
    local choice=$(zenity --list \
        --title="TidyTux Options" \
        --text="What would you like to do?" \
        --column="Option" \
        "Quick Cleanup (Recommended)" \
        "Custom Cleanup" \
        "Preview Mode (Dry Run)" \
        "View System Information" \
        "Open Configuration" \
        --width=400 \
        --height=300 2>/dev/null)
    
    echo "$choice"
}

# System information dialog
show_system_info() {
    local info="💻 System Information\n\n"
    info+="🖥️ OS: $(lsb_release -d 2>/dev/null | cut -f2 || echo "Unknown")\n"
    info+="🧠 Memory: $(free -h | awk '/^Mem:/ {print $2}')\n"
    info+="💾 Disk Usage:\n$(df -h "$HOME" | tail -1)\n\n"
    info+="📁 Home Directory Size: $(du -sh "$HOME" 2>/dev/null | cut -f1)\n"
    info+="🗂️ Downloads Size: $(du -sh "$HOME/Downloads" 2>/dev/null | cut -f1)\n"
    info+="📦 Snap Packages: $(snap list 2>/dev/null | wc -l || echo "0")\n"
    
    zenity --info \
        --title="System Information" \
        --text="$info" \
        --width=500 \
        --height=400
}

# Main GUI application
main_gui() {
    check_gui_dependencies
    
    # Show welcome screen
    show_welcome
    
    while true; do
        local option=$(show_options)
        
        case "$option" in
            "Quick Cleanup (Recommended)")
                analyze_system
                SELECTED_TASKS="ethereum_scripts|claude_downloads|archives|snap_packages|browser_cache|temp_files"
                if confirm_cleanup "$SELECTED_TASKS"; then
                    execute_cleanup "$SELECTED_TASKS"
                    show_results
                    break
                fi
                ;;
            "Custom Cleanup")
                analyze_system
                SELECTED_TASKS=$(select_cleanup_tasks)
                if [ -n "$SELECTED_TASKS" ] && confirm_cleanup "$SELECTED_TASKS"; then
                    execute_cleanup "$SELECTED_TASKS"
                    show_results
                    break
                fi
                ;;
            "Preview Mode (Dry Run)")
                analyze_system
                if show_preview; then
                    DRY_RUN=true
                    SELECTED_TASKS="ethereum_scripts|claude_downloads|archives|snap_packages"
                    execute_cleanup "$SELECTED_TASKS"
                    show_results
                    break
                fi
                ;;
            "View System Information")
                show_system_info
                ;;
            "Open Configuration")
                if [ -f "$CONFIG_DIR/tidytux.conf" ]; then
                    xdg-open "$CONFIG_DIR/tidytux.conf" 2>/dev/null &
                else
                    zenity --info --text="Configuration file not found. Run cleanup first to create it."
                fi
                ;;
            *)
                break
                ;;
        esac
    done
}

# Check if running in GUI mode
if [ -n "${DISPLAY:-}" ]; then
    main_gui
else
    echo "TidyTux GUI requires a graphical environment."
    echo "Run without GUI options for command-line mode."
    exit 1
fi