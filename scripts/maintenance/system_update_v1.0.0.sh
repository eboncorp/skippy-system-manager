#!/bin/bash

# Update and Upgrade Script for Debian-based Linux systems

# Print start message
echo "Starting system update and maintenance..."

# Update package lists
echo "Updating package lists..."
sudo apt update

# Upgrade installed packages
echo "Upgrading installed packages..."
sudo apt upgrade -y

# Perform full-upgrade (dist-upgrade)
echo "Performing full upgrade..."
sudo apt full-upgrade -y

# Remove unnecessary packages
echo "Removing unnecessary packages..."
sudo apt autoremove -y

# Clean up downloaded package files
echo "Cleaning up downloaded package files..."
sudo apt clean

# Update snap packages if snap is installed
if command -v snap &> /dev/null
then
    echo "Updating snap packages..."
    sudo snap refresh
else
    echo "Snap is not installed. Skipping snap updates."
fi

# Update flatpak packages if flatpak is installed
if command -v flatpak &> /dev/null
then
    echo "Updating flatpak packages..."
    flatpak update -y
else
    echo "Flatpak is not installed. Skipping flatpak updates."
fi

# Print completion message
echo "System update and maintenance completed!"
