#!/bin/bash

# Simplified NordPass Direct Download and Installation Script for Ubuntu

# Check if script is run with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
fi

echo "NordPass Installation Script"
echo "============================"

# Use a known version and download link
DOWNLOAD_URL="https://downloads.npass.app/linux/deb/amd64/nordpass_4.51.0_amd64.deb"

# Download NordPass
echo "Downloading NordPass..."
if wget -O nordpass.deb "$DOWNLOAD_URL"; then
    echo "Download complete."
else
    echo "Failed to download NordPass. Please check your internet connection and try again."
    exit 1
fi

# Install NordPass
echo "Installing NordPass..."
if dpkg -i nordpass.deb; then
    echo "NordPass has been successfully installed."
else
    echo "Installation failed. Attempting to resolve dependencies..."
    apt-get update
    apt-get -f install -y
    if dpkg -i nordpass.deb; then
        echo "NordPass has been successfully installed after resolving dependencies."
    else
        echo "Installation failed. Please check the error messages above."
        exit 1
    fi
fi

# Clean up
echo "Cleaning up..."
rm nordpass.deb

echo "Installation complete! You can now launch NordPass from your application menu."
echo "Note: You may need to log out and log back in for NordPass to appear in your menu."
