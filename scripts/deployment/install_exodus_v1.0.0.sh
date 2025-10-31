#!/bin/bash

# Exodus Wallet Installation Script for Ubuntu (.deb version)

# Check if script is run with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
fi

EXODUS_FILE="/home/dave/Downloads/apps/exodus-linux-x64-24.37.2.deb"

echo "Exodus Wallet Installation Script"
echo "================================="

if [ ! -f "$EXODUS_FILE" ]; then
    echo "Exodus .deb file not found at $EXODUS_FILE"
    echo "Please make sure the file exists and the path is correct."
    exit 1
fi

echo "Found Exodus file: $EXODUS_FILE"
echo "Starting installation..."

# Install the .deb package
echo "Installing .deb package..."
if dpkg -i "$EXODUS_FILE"; then
    echo "Exodus wallet has been successfully installed."
    echo "You can now launch Exodus from your application menu."
else
    echo "Installation failed. Please check the error messages above."
    exit 1
fi

# Update the desktop database to ensure the application shows up in the menu
update-desktop-database

echo "Installation complete! You can now launch Exodus from your application menu."
