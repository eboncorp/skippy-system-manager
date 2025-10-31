#!/bin/bash
# Browser Certificate Fix Script
# Attempts to fix SSL certificate issues in browsers

echo "=================================="
echo "Browser Certificate Fix Tool"
echo "=================================="
echo ""
echo "WARNING: This will close your browser and reset certificate databases"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

set -e

echo ""
echo "Step 1: Checking for running browsers..."
if pgrep -f "chrome|chromium|firefox" > /dev/null; then
    echo "Found running browser processes. Please close all browser windows."
    echo "Waiting for browsers to close..."
    while pgrep -f "chrome|chromium|firefox" > /dev/null; do
        sleep 2
        echo -n "."
    done
    echo ""
    echo "Browsers closed."
else
    echo "No browsers running."
fi

echo ""
echo "Step 2: Backing up certificate databases..."

# Backup Chrome/Chromium certs
if [ -d ~/.pki/nssdb ]; then
    BACKUP_DIR=~/.pki/nssdb_backup_$(date +%Y%m%d_%H%M%S)
    cp -r ~/.pki/nssdb "$BACKUP_DIR"
    echo "Chrome/Chromium certs backed up to: $BACKUP_DIR"
fi

# Backup Firefox certs
if [ -d ~/.mozilla/firefox ]; then
    for profile in ~/.mozilla/firefox/*.default*; do
        if [ -d "$profile" ]; then
            BACKUP_DIR="${profile}_backup_$(date +%Y%m%d_%H%M%S)"
            cp -r "$profile" "$BACKUP_DIR"
            echo "Firefox profile backed up to: $BACKUP_DIR"
        fi
    done
fi

echo ""
echo "Step 3: Updating system CA certificates..."
sudo update-ca-certificates --fresh

echo ""
echo "Step 4: Reset Chrome/Chromium certificate database..."
if [ -f ~/.pki/nssdb/cert9.db ]; then
    mv ~/.pki/nssdb/cert9.db ~/.pki/nssdb/cert9.db.old
    echo "Chrome/Chromium cert database reset (old file renamed)"
fi

echo ""
echo "Step 5: Reset Firefox certificate database (if exists)..."
for profile in ~/.mozilla/firefox/*.default*/cert9.db; do
    if [ -f "$profile" ]; then
        mv "$profile" "${profile}.old"
        echo "Firefox cert database reset: $profile"
    fi
done

echo ""
echo "=================================="
echo "Certificate databases have been reset!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Restart your browser"
echo "2. The browser will automatically recreate the certificate database"
echo "3. Try accessing https://claude.ai again"
echo ""
echo "If you need to restore backups, they are saved in:"
echo "  ~/.pki/nssdb_backup_* (Chrome/Chromium)"
echo "  ~/.mozilla/firefox/*_backup_* (Firefox)"
echo ""
