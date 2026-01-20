# MCP Server Health Check

Monitor and test all MCP server endpoints, integrations, and tool availability.

## Instructions

When this skill is invoked, perform a comprehensive MCP server health check:

### 1. Server Configuration
```bash
MCP_SERVER_PATH="/home/dave/skippy/mcp-servers/general-server"
MCP_CONFIG_PATH="/home/dave/.claude/claude_desktop_config.json"

# Current version
CURRENT_VERSION="v2.4.0"
TOTAL_TOOLS=133
```

### 2. Check Server Status
```bash
# Verify server files exist
ls -la "$MCP_SERVER_PATH/server.py"
ls -la "$MCP_SERVER_PATH/requirements.txt"

# Check if server process is running (if applicable)
pgrep -f "mcp-servers/general-server" || echo "Server not running as standalone process"

# Verify Python environment
python3 --version
pip3 list | grep -E "google-api|pexels|slack"
```

### 3. Test Individual Integrations

**Pexels Stock Photos (4 tools) - SHOULD BE OPERATIONAL:**
```bash
# Check API key
grep -q "PEXELS_API_KEY" ~/.bashrc || echo "WARNING: Pexels API key not in environment"

# Test tools:
# - search_photos
# - get_photo
# - download_photo
# - curated_photos
```

**Google Drive (13 tools) - SHOULD BE OPERATIONAL:**
```bash
# Check credentials
ls -la ~/.config/claude-code/google_credentials.json
ls -la ~/.config/claude-code/google_token.json

# Test tools:
# - gdrive_list_files
# - gdrive_get_file_metadata
# - gdrive_read_file
# - gdrive_create_file
# - gdrive_update_file
# - gdrive_delete_file
# - gdrive_create_folder
# - gdrive_move_file
# - gdrive_copy_file
# - gdrive_search_files
# - gdrive_share_file
# - gdrive_get_file_revisions
# - gdrive_export_file
```

**Google Photos (6 tools) - OAUTH 403 ISSUE PENDING:**
```bash
# Check OAuth status
ls -la ~/.config/claude-code/google_photos_token.json

# Known issue: OAuth 403 error
# Status: Code complete, OAuth propagation pending

# Tools (when working):
# - gphotos_list_albums
# - gphotos_get_album
# - gphotos_list_media_items
# - gphotos_get_media_item
# - gphotos_search_media
# - gphotos_download_media
```

**GitHub (3 tools) - SHOULD BE OPERATIONAL:**
```bash
# Check gh CLI authentication
gh auth status

# Tools:
# - github_create_issue
# - github_list_issues
# - github_create_pr
```

**Slack (2 tools) - SHOULD BE OPERATIONAL:**
```bash
# Check Slack token
grep -q "SLACK_BOT_TOKEN" ~/.bashrc || echo "WARNING: Slack token not in environment"

# Tools:
# - slack_send_message
# - slack_list_channels
```

### 4. Generate Health Report
```bash
HEALTH_DIR="/home/dave/skippy/work/mcp/$(date +%Y%m%d_%H%M%S)_health_check"
mkdir -p "$HEALTH_DIR"

cat > "$HEALTH_DIR/MCP_HEALTH_REPORT.md" <<EOF
# MCP Server Health Report
**Date:** $(date)
**Server Version:** $CURRENT_VERSION
**Total Tools:** $TOTAL_TOOLS

## Integration Status

### Pexels Stock Photos
- **Status:** ✅ OPERATIONAL / ❌ FAILED / ⚠️ DEGRADED
- **Tools Available:** 4/4
- **API Key:** Valid / Missing / Expired
- **Last Test:** $(date)

### Google Drive
- **Status:** ✅ OPERATIONAL / ❌ FAILED / ⚠️ DEGRADED
- **Tools Available:** 13/13
- **OAuth Token:** Valid / Expired / Missing
- **Last Test:** $(date)

### Google Photos
- **Status:** ⚠️ PENDING OAUTH FIX
- **Tools Available:** 0/6 (OAuth 403 error)
- **Issue:** OAuth propagation delay
- **Action Required:** Wait for OAuth to propagate, then retest

### GitHub
- **Status:** ✅ OPERATIONAL / ❌ FAILED / ⚠️ DEGRADED
- **Tools Available:** 3/3
- **gh CLI Auth:** Valid / Expired
- **Last Test:** $(date)

### Slack
- **Status:** ✅ OPERATIONAL / ❌ FAILED / ⚠️ DEGRADED
- **Tools Available:** 2/2
- **Bot Token:** Valid / Missing / Expired
- **Last Test:** $(date)

## Overall Health Score
- **Operational Tools:** XX/133
- **Health Percentage:** XX%
- **Critical Issues:** {count}
- **Warnings:** {count}

## Recommendations
1. {Any fixes needed}
2. {Token renewals required}
3. {Pending issues to monitor}

## Next Steps
- Google Photos: Retry OAuth after propagation
- Token expiration monitoring
- Regular health checks (weekly recommended)
EOF
```

### 5. Check Dependencies
```bash
# Verify all required Python packages
pip3 freeze > "$HEALTH_DIR/installed_packages.txt"

REQUIRED_PACKAGES=(
  "google-api-python-client"
  "google-auth-oauthlib"
  "pexels-api"
  "slack-sdk"
  "requests"
)

for pkg in "${REQUIRED_PACKAGES[@]}"; do
  pip3 show "$pkg" > /dev/null 2>&1 && echo "✅ $pkg" || echo "❌ $pkg MISSING"
done
```

### 6. Test Tool Execution
For each integration, attempt a simple read-only operation:
```python
# Pexels: Search for a single photo
# Google Drive: List root folder
# GitHub: List recent issues
# Slack: List channels
```

### 7. OAuth Token Management
```bash
# Check token expiration dates
python3 <<EOF
import json
from datetime import datetime

# Google Drive token
try:
    with open('~/.config/claude-code/google_token.json') as f:
        token = json.load(f)
        expiry = token.get('expiry', 'Unknown')
        print(f"Google Drive token expires: {expiry}")
except Exception as e:
    print(f"Cannot read Google Drive token: {e}")

# Similar for other OAuth tokens
EOF
```

## Usage
- `/mcp-health` - Run comprehensive health check
- Reports saved to `/home/dave/skippy/work/mcp/`
- Monitors 133 tools across 6 MCP servers
- Tracks OAuth status and token expiration
- Identifies degraded or failed services

## Troubleshooting Guide

**OAuth 403 Error (Google Photos):**
- Wait 24-48 hours for OAuth propagation
- Verify app is in "Testing" mode in Google Cloud Console
- Ensure email is added as test user

**Token Expired:**
```bash
# Re-authenticate
cd $MCP_SERVER_PATH
python3 auth_google.py
```

**Missing API Keys:**
- Add to ~/.bashrc: `export PEXELS_API_KEY="your_key"`
- Source: `source ~/.bashrc`

**Server Not Responding:**
- Check logs: `tail -f $MCP_SERVER_PATH/logs/server.log`
- Restart: `pkill -f mcp-servers && python3 $MCP_SERVER_PATH/server.py`
