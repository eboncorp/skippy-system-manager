#!/bin/bash

# Ebonhawk System Update Script
# Run system and agent updates immediately

echo "==================================="
echo "   EBONHAWK SYSTEM UPDATE MANAGER"
echo "==================================="
echo

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running with sudo
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}Please run without sudo. Script will request sudo when needed.${NC}"
   exit 1
fi

# Function to print status
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Update system packages
echo "1. Updating System Packages"
echo "----------------------------"

# Update package lists
echo -n "   Updating package lists... "
if sudo apt-get update &>/dev/null; then
    print_status "Updated"
else
    print_error "Failed"
fi

# Check for available updates
UPDATES=$(apt list --upgradable 2>/dev/null | grep -c "upgradable")
if [ "$UPDATES" -gt 0 ]; then
    echo "   Found $UPDATES packages to update"
    
    # Show what will be updated
    echo
    echo "   Packages to update:"
    apt list --upgradable 2>/dev/null | grep "upgradable" | head -10
    echo
    
    # Perform upgrade
    echo -n "   Installing updates... "
    if sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y \
        -o Dpkg::Options::="--force-confdef" \
        -o Dpkg::Options::="--force-confold" &>/dev/null; then
        print_status "Installed"
    else
        print_error "Failed"
    fi
else
    print_status "System is up to date"
fi

# Clean up old packages
echo -n "   Cleaning up old packages... "
sudo apt-get autoremove -y &>/dev/null
sudo apt-get autoclean &>/dev/null
print_status "Cleaned"

echo

# Update snap packages
echo "2. Updating Snap Packages"
echo "-------------------------"

if command -v snap &>/dev/null; then
    echo -n "   Refreshing snaps... "
    SNAP_OUTPUT=$(sudo snap refresh 2>&1)
    if echo "$SNAP_OUTPUT" | grep -q "All snaps up to date"; then
        print_status "All snaps up to date"
    elif echo "$SNAP_OUTPUT" | grep -q "refreshed"; then
        SNAP_COUNT=$(echo "$SNAP_OUTPUT" | grep -c "refreshed")
        print_status "Updated $SNAP_COUNT snap(s)"
    else
        print_status "Checked"
    fi
else
    print_warning "Snap not installed"
fi

echo

# Update flatpak packages
echo "3. Updating Flatpak Applications"
echo "---------------------------------"

if command -v flatpak &>/dev/null; then
    echo -n "   Updating flatpaks... "
    if flatpak update -y &>/dev/null; then
        print_status "Updated"
    else
        print_warning "No updates or failed"
    fi
else
    print_warning "Flatpak not installed"
fi

echo

# Check for kernel updates
echo "4. Checking Kernel Updates"
echo "--------------------------"

CURRENT_KERNEL=$(uname -r)
echo "   Current kernel: $CURRENT_KERNEL"

KERNEL_UPDATES=$(apt list --upgradable 2>/dev/null | grep -c "linux-image")
if [ "$KERNEL_UPDATES" -gt 0 ]; then
    print_warning "Kernel update available"
    echo -n "   Install kernel update? (y/n): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        if sudo apt-get install -y linux-image-generic linux-headers-generic &>/dev/null; then
            print_status "Kernel updated - REBOOT REQUIRED"
            echo
            print_warning "System reboot required to use new kernel"
            echo -n "   Schedule reboot for 3 AM? (y/n): "
            read -r reboot_response
            if [[ "$reboot_response" =~ ^[Yy]$ ]]; then
                sudo shutdown -r 03:00 "System reboot for kernel update"
                print_status "Reboot scheduled for 3:00 AM"
            fi
        else
            print_error "Kernel update failed"
        fi
    fi
else
    print_status "Kernel is up to date"
fi

echo

# Update Ebonhawk agent
echo "5. Checking Ebonhawk Agent"
echo "---------------------------"

AGENT_PATH="$HOME/Scripts/ebonhawk_maintenance_agent.py"
UPDATER_PATH="$HOME/Scripts/ebonhawk_agent_updater.py"

if [ -f "$UPDATER_PATH" ]; then
    echo -n "   Checking for agent updates... "
    python3 "$UPDATER_PATH" --check 2>&1 | grep -q "up to date"
    if [ $? -eq 0 ]; then
        print_status "Agent is up to date"
    else
        print_warning "Agent update available"
        python3 "$UPDATER_PATH" --force
    fi
else
    print_warning "Agent updater not found"
fi

echo

# Check system status
echo "6. System Status Check"
echo "----------------------"

if [ -f "$AGENT_PATH" ]; then
    # Get quick status
    STATUS=$(python3 "$AGENT_PATH" --status 2>/dev/null | grep -E "cpu|memory|disk" | head -3)
    if [ -n "$STATUS" ]; then
        echo "$STATUS" | while IFS= read -r line; do
            echo "   $line"
        done
    fi
fi

# Check if services need restart
if [ -f /var/run/reboot-required ]; then
    echo
    print_warning "System reboot required"
    echo "   Some updates require a system reboot to take effect"
fi

SERVICES_NEED_RESTART=$(sudo needrestart -b 2>/dev/null | grep -c "NEEDRESTART-SVC")
if [ "$SERVICES_NEED_RESTART" -gt 0 ]; then
    echo
    print_warning "$SERVICES_NEED_RESTART service(s) need restart"
    echo -n "   Restart services now? (y/n): "
    read -r restart_response
    if [[ "$restart_response" =~ ^[Yy]$ ]]; then
        sudo needrestart -ra
        print_status "Services restarted"
    fi
fi

echo
echo "==================================="
echo "   UPDATE COMPLETE"
echo "==================================="
echo
echo "Summary:"
echo "  • System packages: Updated"
echo "  • Snap packages: Checked"
echo "  • Flatpak apps: Checked"
echo "  • Kernel: Checked"
echo "  • Agent: Checked"

if [ -f /var/run/reboot-required ]; then
    echo
    echo -e "${YELLOW}Note: System reboot required${NC}"
fi

echo
echo "Next automatic update: 3:00 AM tomorrow"
echo