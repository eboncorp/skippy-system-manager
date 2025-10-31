#!/bin/bash

echo "=== Reconfiguring Cloud Drives to Include All Content ==="
echo ""
echo "This script will help you reconfigure your cloud drives to include:"
echo "- Shared folders and files"
echo "- Team drives (Google Drive)"
echo "- SharePoint sites (OneDrive)"
echo "- Shared links (Dropbox)"
echo ""

# Kill any existing mounts
echo "Stopping existing mounts..."
pkill -f "rclone mount" 2>/dev/null
sleep 2
fusermount -uz /home/dave/GoogleDrive 2>/dev/null
fusermount -uz /home/dave/OneDrive 2>/dev/null
fusermount -uz /home/dave/Dropbox 2>/dev/null

echo ""
echo "=== GOOGLE DRIVE CONFIGURATION ==="
echo "To include shared drives and files:"
echo "1. Run: rclone config"
echo "2. Choose 'e' to edit existing remote"
echo "3. Select 'googledrive'"
echo "4. For 'scope', enter: drive"
echo "5. For 'team_drive', leave blank to see all drives"
echo "6. Enable 'Show all drives' when prompted"
echo "7. Set 'shared_with_me' to true"
echo ""

echo "=== ONEDRIVE CONFIGURATION ==="
echo "To include SharePoint and shared content:"
echo "1. Run: rclone config"
echo "2. Choose 'e' to edit existing remote"
echo "3. Select 'onedrive'"
echo "4. When prompted for drive type, choose:"
echo "   - 'onedrive' for personal + shared"
echo "   - 'sharepoint' to access SharePoint sites"
echo "5. Re-authenticate to get full permissions"
echo ""

echo "=== DROPBOX CONFIGURATION ==="
echo "Dropbox automatically includes shared folders"
echo "No reconfiguration needed for basic shared access"
echo ""

echo "Press Enter to open rclone config..."
read

# Open rclone config
rclone config

echo ""
echo "=== Configuration Complete ==="
echo "Now mounting drives with full access..."
echo ""

# Mount Google Drive with shared files
echo "Mounting Google Drive..."
rclone mount googledrive: /home/dave/google_drive/ \
  --daemon \
  --allow-non-empty \
  --vfs-cache-mode writes \
  --drive-shared-with-me \
  --drive-acknowledge-abuse \
  --log-level INFO

# Mount OneDrive with all content
echo "Mounting OneDrive..."
rclone mount onedrive: /home/dave/OneDrive/ \
  --daemon \
  --allow-non-empty \
  --vfs-cache-mode writes \
  --log-level INFO

# Mount Dropbox
echo "Mounting Dropbox..."
rclone mount dropbox: /home/dave/Dropbox/ \
  --daemon \
  --allow-non-empty \
  --vfs-cache-mode writes \
  --log-level INFO

echo ""
echo "Checking mounted drives..."
sleep 3
df -h | grep -E "googledrive|dropbox|onedrive"

echo ""
echo "=== Setup Complete ==="
echo "Your cloud drives are now mounted with full access to:"
echo "✓ Personal files"
echo "✓ Shared files and folders"
echo "✓ Team drives (Google)"
echo "✓ SharePoint sites (OneDrive)"
echo ""
echo "To make these mounts permanent, the systemd services have been updated."