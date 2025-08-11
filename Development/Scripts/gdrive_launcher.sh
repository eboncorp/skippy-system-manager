#!/bin/bash

# Google Drive Manager GUI Launcher
# This script launches the GUI interface for Google Drive Manager

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed."
        echo "Please install Python 3:"
        echo "  Ubuntu/Debian: sudo apt install python3 python3-tk"
        echo "  Fedora: sudo dnf install python3 python3-tkinter"
        echo "  Arch: sudo pacman -S python python-tk"
        return 1
    fi
    
    # Check if tkinter is available
    if ! python3 -c "import tkinter" &> /dev/null; then
        print_error "tkinter is not installed."
        echo "Please install tkinter:"
        echo "  Ubuntu/Debian: sudo apt install python3-tk"
        echo "  Fedora: sudo dnf install python3-tkinter"
        echo "  Arch: sudo pacman -S tk"
        return 1
    fi
    
    print_status "Python 3 and tkinter are available"
    return 0
}

# Check if the bash script exists
check_bash_script() {
    local script_path="$HOME/gdrive-manager.sh"
    
    if [ ! -f "$script_path" ]; then
        print_error "Google Drive Manager script not found at $script_path"
        echo
        echo "Please ensure you have:"
        echo "1. Downloaded the gdrive-manager.sh script"
        echo "2. Placed it in your home directory ($HOME)"
        echo "3. Made it executable: chmod +x $HOME/gdrive-manager.sh"
        echo
        echo "You can create the script by running the setup instructions provided."
        return 1
    fi
    
    # Check if script is executable
    if [ ! -x "$script_path" ]; then
        print_warning "Script is not executable. Making it executable..."
        chmod +x "$script_path"
    fi
    
    print_status "Google Drive Manager script found and executable"
    return 0
}

# Check if the GUI script exists
check_gui_script() {
    local gui_path="$HOME/gdrive-manager-gui.py"
    
    if [ ! -f "$gui_path" ]; then
        print_error "GUI script not found at $gui_path"
        echo
        echo "Please ensure you have:"
        echo "1. Downloaded the gdrive-manager-gui.py script"
        echo "2. Placed it in your home directory ($HOME)"
        echo
        echo "You can create the script by copying the provided Python code."
        return 1
    fi
    
    print_status "GUI script found"
    return 0
}

# Create desktop entry
create_desktop_entry() {
    local desktop_dir="$HOME/.local/share/applications"
    local desktop_file="$desktop_dir/gdrive-manager.desktop"
    
    # Create directory if it doesn't exist
    mkdir -p "$desktop_dir"
    
    # Create desktop entry
    cat > "$desktop_file" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Google Drive Manager
Comment=Manage Google Drive with rclone
Exec=$HOME/gdrive-launcher.sh
Icon=drive-harddisk
Terminal=false
Categories=System;FileManager;
StartupNotify=true
EOF
    
    # Make it executable
    chmod +x "$desktop_file"
    
    print_status "Desktop entry created at $desktop_file"
    
    # Update desktop database if available
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$desktop_dir"
    fi
}

# Main launcher function
launch_gui() {
    print_status "Starting Google Drive Manager GUI..."
    
    # Change to home directory
    cd "$HOME"
    
    # Launch the GUI
    python3 gdrive-manager-gui.py
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_status "GUI closed successfully"
    else
        print_error "GUI exited with error code $exit_code"
    fi
    
    return $exit_code
}

# Handle command line arguments
case "${1:-}" in
    "--setup")
        echo "Setting up Google Drive Manager GUI..."
        
        # Check prerequisites
        if ! check_python; then
            exit 1
        fi
        
        if ! check_bash_script; then
            exit 1
        fi
        
        if ! check_gui_script; then
            exit 1
        fi
        
        # Create desktop entry
        create_desktop_entry
        
        print_status "Setup complete! You can now launch the GUI from:"
        echo "  - Command line: $HOME/gdrive-launcher.sh"
        echo "  - Applications menu: Google Drive Manager"
        echo "  - Or run: python3 $HOME/gdrive-manager-gui.py"
        ;;
        
    "--check")
        echo "Checking Google Drive Manager GUI prerequisites..."
        
        local all_good=true
        
        if ! check_python; then
            all_good=false
        fi
        
        if ! check_bash_script; then
            all_good=false
        fi
        
        if ! check_gui_script; then
            all_good=false
        fi
        
        if [ "$all_good" = true ]; then
            print_status "All prerequisites met! Ready to launch GUI."
            exit 0
        else
            print_error "Some prerequisites are missing. Please fix the issues above."
            exit 1
        fi
        ;;
        
    "--help"|"-h")
        echo "Google Drive Manager GUI Launcher"
        echo
        echo "Usage: $0 [OPTION]"
        echo
        echo "Options:"
        echo "  --setup    Setup the GUI launcher and desktop entry"
        echo "  --check    Check if all prerequisites are met"
        echo "  --help     Show this help message"
        echo
        echo "Without options, launches the GUI directly."
        ;;
        
    *)
        # Default: launch GUI
        
        # Quick prerequisite check
        if ! check_python; then
            exit 1
        fi
        
        if ! check_bash_script; then
            exit 1
        fi
        
        if ! check_gui_script; then
            exit 1
        fi
        
        # Launch GUI
        launch_gui
        ;;
esac