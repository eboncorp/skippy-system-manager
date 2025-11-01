#!/bin/bash

# Setup Google Drive sync for Skippy
# Installs rclone and configures automatic sync

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}     Google Drive Sync Setup for Skippy            ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo

# 1. Install rclone
echo -e "${BLUE}Installing rclone...${NC}"
if ! command -v rclone &>/dev/null; then
    curl https://rclone.org/install.sh | sudo bash
    echo -e "${GREEN}[✓] rclone installed${NC}"
else
    echo -e "${GREEN}[✓] rclone already installed ($(rclone version | head -1))${NC}"
fi

# 2. Create sync script
echo -e "${BLUE}Creating Skippy sync script...${NC}"
cat > /home/ebon/Skippy/Scripts/sync_skippy_to_gdrive.sh << 'EOF'
#!/bin/bash
# Sync Skippy data to Google Drive

SKIPPY_HOME="/home/ebon/Skippy"
GDRIVE_DEST="googledrive:Skippy-Backup"
LOG_FILE="/tmp/skippy_gdrive_sync_$(date +%Y%m%d).log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if Google Drive is configured
if ! rclone listremotes | grep -q "googledrive:"; then
    log "Error: Google Drive not configured in rclone"
    log "Run: rclone config"
    exit 1
fi

log "Starting Skippy sync to Google Drive..."

# Sync important directories
DIRS_TO_SYNC=(
    "conversations"
    "Scripts"
    "Documentation"
    "config.yaml"
)

for dir in "${DIRS_TO_SYNC[@]}"; do
    if [ -e "$SKIPPY_HOME/$dir" ]; then
        log "Syncing $dir..."
        rclone sync "$SKIPPY_HOME/$dir" "$GDRIVE_DEST/$dir" \
            --transfers=4 \
            --checkers=8 \
            --fast-list \
            --progress \
            --log-file="$LOG_FILE" \
            --log-level=INFO

        if [ $? -eq 0 ]; then
            log "✓ $dir synced successfully"
        else
            log "✗ Failed to sync $dir"
        fi
    fi
done

# Upload log file
rclone copyto "$LOG_FILE" "$GDRIVE_DEST/logs/sync_$(date +%Y%m%d_%H%M%S).log"

log "Skippy sync completed"

# Show summary
echo ""
echo "Summary:"
rclone size "$GDRIVE_DEST" --json | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"  Files: {data.get('count', 0)}\")
print(f\"  Size: {data.get('bytes', 0) / (1024**2):.2f} MB\")
"
EOF

chmod +x /home/ebon/Skippy/Scripts/sync_skippy_to_gdrive.sh
echo -e "${GREEN}[✓] Sync script created${NC}"

# 3. Create cron job file
echo -e "${BLUE}Creating cron job configuration...${NC}"
cat > /tmp/skippy_gdrive_cron << 'EOF'
# Sync Skippy to Google Drive every 6 hours
0 */6 * * * /home/ebon/Skippy/Scripts/sync_skippy_to_gdrive.sh > /dev/null 2>&1

# Daily sync at 2 AM with full log
0 2 * * * /home/ebon/Skippy/Scripts/sync_skippy_to_gdrive.sh
EOF

echo -e "${GREEN}[✓] Cron configuration created${NC}"

# 4. Instructions
echo
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}           Setup Instructions                       ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo
echo -e "${YELLOW}Step 1: Configure Google Drive in rclone${NC}"
echo "  Run: rclone config"
echo "  - Choose 'n' for new remote"
echo "  - Name it: googledrive"
echo "  - Choose 'Google Drive' from the list"
echo "  - Follow OAuth authentication steps"
echo
echo -e "${YELLOW}Step 2: Test the sync${NC}"
echo "  Run: /home/ebon/Skippy/Scripts/sync_skippy_to_gdrive.sh"
echo
echo -e "${YELLOW}Step 3: Enable automatic sync (optional)${NC}"
echo "  Run: crontab -e"
echo "  Add the contents from: /tmp/skippy_gdrive_cron"
echo "  Or run: (crontab -l; cat /tmp/skippy_gdrive_cron) | crontab -"
echo
echo -e "${BLUE}Manual sync command:${NC}"
echo "  skippy-sync  (will be created after configuration)"

# 5. Create quick sync command
cat > /home/ebon/.local/bin/skippy-sync << 'EOF'
#!/bin/bash
# Quick sync Skippy to Google Drive

if ! rclone listremotes | grep -q "googledrive:"; then
    echo "Error: Google Drive not configured"
    echo "Run: rclone config"
    exit 1
fi

echo "Syncing Skippy to Google Drive..."
/home/ebon/Skippy/Scripts/sync_skippy_to_gdrive.sh
EOF

chmod +x /home/ebon/.local/bin/skippy-sync

echo
echo -e "${GREEN}Script saved as: /home/ebon/setup_gdrive_sync.sh${NC}"