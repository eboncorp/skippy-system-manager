#!/bin/bash

# Interactive Google Drive configuration helper for rclone

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}     Google Drive Configuration Helper             ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo

# Check if already configured
if rclone listremotes 2>/dev/null | grep -q "googledrive:"; then
    echo -e "${GREEN}✓ Google Drive is already configured!${NC}"
    echo
    echo "Testing connection..."
    if rclone lsd googledrive: --max-depth 1 &>/dev/null; then
        echo -e "${GREEN}✓ Connection successful!${NC}"
        echo
        echo "Available commands:"
        echo "  skippy-sync         - Sync Skippy to Google Drive"
        echo "  rclone lsd googledrive:  - List directories"
        echo
        exit 0
    else
        echo -e "${RED}✗ Connection failed. Reconfiguring...${NC}"
    fi
fi

echo -e "${YELLOW}This will guide you through setting up Google Drive with rclone.${NC}"
echo
echo "You will need:"
echo "1. A Google account"
echo "2. A web browser (for authentication)"
echo
echo -e "${YELLOW}Press Enter to continue or Ctrl+C to cancel...${NC}"
read

# Create a template config
cat > /tmp/rclone_gdrive_setup.txt << 'EOF'
INSTRUCTIONS:

When rclone config opens, follow these steps:

1. Type 'n' for new remote
2. Name: googledrive
3. Storage: Choose 'Google Drive' (usually option 18)
4. client_id: Press Enter (leave blank)
5. client_secret: Press Enter (leave blank)
6. scope: Choose option 1 (Full access)
7. service_account_file: Press Enter (leave blank)
8. Edit advanced config: n
9. Auto config: y (if on this machine) or n (if remote)
10. Follow the browser authentication
11. Team drive: n (unless using team drive)
12. Confirm: y
13. Quit: q

EOF

echo -e "${BLUE}Opening rclone configuration...${NC}"
echo -e "${YELLOW}Follow the instructions above (also saved to /tmp/rclone_gdrive_setup.txt)${NC}"
echo

# Run rclone config
rclone config

# Test the configuration
echo
echo -e "${BLUE}Testing Google Drive connection...${NC}"

if rclone listremotes 2>/dev/null | grep -q "googledrive:"; then
    if rclone lsd googledrive: --max-depth 1 &>/dev/null; then
        echo -e "${GREEN}✓ Google Drive configured successfully!${NC}"

        # Create initial backup directory
        echo -e "${BLUE}Creating Skippy-Backup directory in Google Drive...${NC}"
        rclone mkdir googledrive:Skippy-Backup

        echo
        echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}            Setup Complete!                        ${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
        echo
        echo "Google Drive is now configured!"
        echo
        echo "Automatic sync schedule:"
        echo "  - Every 6 hours"
        echo "  - Daily at 2 AM with full logs"
        echo
        echo "Manual commands:"
        echo "  skippy-sync              - Sync Skippy now"
        echo "  rclone lsd googledrive:  - List Google Drive contents"
        echo
        echo -e "${YELLOW}Running initial sync...${NC}"
        /home/ebon/Skippy/Scripts/sync_skippy_to_gdrive.sh
    else
        echo -e "${RED}✗ Connection test failed${NC}"
        echo "Please check your configuration and try again"
        exit 1
    fi
else
    echo -e "${RED}✗ Google Drive remote not found${NC}"
    echo "Configuration may have failed. Please try again."
    exit 1
fi