#!/bin/bash
# Google Photos Setup Script
# Completes the OAuth authentication for Google Photos access

echo "================================================"
echo "         Google Photos Setup"
echo "================================================"
echo
echo "Setting up Google Photos access..."
echo

# Check if googlephotos remote exists
if ! rclone config show googlephotos >/dev/null 2>&1; then
    echo "Creating Google Photos remote..."
    rclone config create googlephotos googlephotos
else
    echo "✓ Google Photos remote exists"
fi

echo
echo "To complete setup, you need to authenticate with Google:"
echo "1. Run: rclone config"
echo "2. Choose 'e' to edit existing remote"
echo "3. Select 'googlephotos'"
echo "4. Choose 'y' to edit the token"
echo "5. Choose 'y' to use auto config (if you have a browser)"
echo "6. Complete OAuth in your browser"
echo
echo "Or run this command directly:"
echo "rclone config reconnect googlephotos:"
echo
echo "After authentication, test with:"
echo "rclone lsd googlephotos:"
echo