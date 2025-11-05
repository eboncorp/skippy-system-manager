#!/bin/bash
# Template Generator v1.0.0
# Generate script templates quickly
# Part of: Skippy Enhancement Project - TIER 2
# Created: 2025-11-04

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SKIPPY_BASE="/home/dave/skippy"

usage() {
    cat <<EOF
Template Generator v1.0.0

USAGE:
    $0 <template_type> <output_file> [options]

TEMPLATE TYPES:
    bash-script              Basic bash script with error handling
    wordpress-tool           WordPress automation script
    backup-script            Backup script with rotation
    deployment-script        Deployment automation
    monitoring-script        Monitoring/health check script
    security-scanner         Security scanning script
    cron-job                 Cron-compatible script
    python-script            Python script with logging
    validation-script        Pre-deployment validation
    sync-script              Content sync script

OPTIONS:
    --name <name>            Script name/title
    --description <desc>     Script description
    --author <author>        Author name (default: Dave Biggers Campaign)

EXAMPLES:
    # Generate basic bash script
    $0 bash-script my_script.sh --name "My Tool"

    # Generate WordPress tool
    $0 wordpress-tool wp_tool.sh --description "WordPress automation"

    # Generate backup script
    $0 backup-script backup_daily.sh --name "Daily Backup"

EOF
    exit 1
}

# Parse options
SCRIPT_NAME=""
DESCRIPTION=""
AUTHOR="Dave Biggers Campaign"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --name)
            SCRIPT_NAME="$2"
            shift 2
            ;;
        --description)
            DESCRIPTION="$2"
            shift 2
            ;;
        --author)
            AUTHOR="$2"
            shift 2
            ;;
        *)
            break
            ;;
    esac
done

TEMPLATE_TYPE="${1:-}"
OUTPUT_FILE="${2:-}"

if [ -z "$TEMPLATE_TYPE" ] || [ -z "$OUTPUT_FILE" ]; then
    usage
fi

# Get script name if not provided
if [ -z "$SCRIPT_NAME" ]; then
    SCRIPT_NAME=$(basename "$OUTPUT_FILE" .sh | tr '_' ' ' | tr '-' ' ' | sed 's/\b\(.\)/\u\1/g')
fi

# Get description if not provided
if [ -z "$DESCRIPTION" ]; then
    DESCRIPTION="$SCRIPT_NAME"
fi

# Template: Basic bash script
template_bash_script() {
    cat > "$OUTPUT_FILE" <<EOF
#!/bin/bash
# $SCRIPT_NAME v1.0.0
# $DESCRIPTION
# Created: $(date +%Y-%m-%d)
# Author: $AUTHOR

set -euo pipefail

# Colors
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m'

# Configuration
SKIPPY_BASE="/home/dave/skippy"
LOG_FILE="\${SKIPPY_BASE}/logs/$(basename "$OUTPUT_FILE" .sh).log"

# Logging functions
log() {
    echo -e "\${BLUE}\$1\${NC}"
    echo "[\$(date '+%Y-%m-%d %H:%M:%S')] \$1" >> "\$LOG_FILE"
}

success() {
    echo -e "\${GREEN}✓ \$1\${NC}"
    echo "[\$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: \$1" >> "\$LOG_FILE"
}

warning() {
    echo -e "\${YELLOW}⚠ \$1\${NC}"
    echo "[\$(date '+%Y-%m-%d %H:%M:%S')] WARNING: \$1" >> "\$LOG_FILE"
}

error() {
    echo -e "\${RED}✗ \$1\${NC}"
    echo "[\$(date '+%Y-%m-%d %H:%M:%S')] ERROR: \$1" >> "\$LOG_FILE"
}

# Usage
usage() {
    cat <<USAGE
$SCRIPT_NAME v1.0.0

USAGE:
    \$0 [options]

OPTIONS:
    --help                   Show this help message

EXAMPLES:
    \$0

USAGE
    exit 1
}

# Main function
main() {
    log "Starting $SCRIPT_NAME..."

    # Your code here

    success "$SCRIPT_NAME complete"
}

# Parse arguments
while [[ \$# -gt 0 ]]; do
    case "\$1" in
        --help|-h)
            usage
            ;;
        *)
            error "Unknown option: \$1"
            usage
            ;;
    esac
done

# Run main
main

exit 0
EOF
}

# Template: WordPress tool
template_wordpress_tool() {
    cat > "$OUTPUT_FILE" <<EOF
#!/bin/bash
# $SCRIPT_NAME v1.0.0
# $DESCRIPTION
# Created: $(date +%Y-%m-%d)
# Author: $AUTHOR

set -euo pipefail

# Colors
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m'

WP_PATH="/home/dave/Local Sites/rundaverun-local/app/public"
SKIPPY_BASE="/home/dave/skippy"
LOG_FILE="\${SKIPPY_BASE}/logs/$(basename "$OUTPUT_FILE" .sh).log"

# Check WP-CLI
if ! command -v wp &> /dev/null; then
    echo -e "\${RED}✗ WP-CLI not found\${NC}"
    exit 1
fi

# Change to WP directory
cd "\$WP_PATH" || exit 1

log() {
    echo -e "\${BLUE}\$1\${NC}"
    echo "[\$(date '+%Y-%m-%d %H:%M:%S')] \$1" >> "\$LOG_FILE"
}

success() {
    echo -e "\${GREEN}✓ \$1\${NC}"
    echo "[\$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: \$1" >> "\$LOG_FILE"
}

# Main
log "Starting $SCRIPT_NAME..."

# Example: Get all posts
POST_COUNT=\$(wp post list --post_type=post --format=count)
log "Found \$POST_COUNT posts"

# Your WordPress operations here

success "$SCRIPT_NAME complete"

exit 0
EOF
}

# Template: Backup script
template_backup_script() {
    cat > "$OUTPUT_FILE" <<EOF
#!/bin/bash
# $SCRIPT_NAME v1.0.0
# $DESCRIPTION
# Created: $(date +%Y-%m-%d)
# Author: $AUTHOR

set -euo pipefail

# Configuration
BACKUP_DIR="/home/dave/skippy/backups"
BACKUP_NAME="backup_\$(date +%Y%m%d_%H%M%S)"
KEEP_DAYS=30
LOG_FILE="/home/dave/skippy/logs/backups.log"

# Colors
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m'

log() {
    echo -e "\${BLUE}\$1\${NC}"
    echo "[\$(date '+%Y-%m-%d %H:%M:%S')] \$1" >> "\$LOG_FILE"
}

success() {
    echo -e "\${GREEN}✓ \$1\${NC}"
    echo "[\$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: \$1" >> "\$LOG_FILE"
}

error() {
    echo -e "\${RED}✗ \$1\${NC}"
    echo "[\$(date '+%Y-%m-%d %H:%M:%S')] ERROR: \$1" >> "\$LOG_FILE"
}

# Create backup directory
mkdir -p "\$BACKUP_DIR"

log "Starting backup: \$BACKUP_NAME"

# Create backup
# TODO: Add your backup commands here
# Example:
# tar -czf "\${BACKUP_DIR}/\${BACKUP_NAME}.tar.gz" /path/to/data

success "Backup created: \${BACKUP_DIR}/\${BACKUP_NAME}.tar.gz"

# Rotate old backups
log "Rotating old backups (keeping last \${KEEP_DAYS} days)..."
find "\$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +\$KEEP_DAYS -delete
success "Rotation complete"

log "Backup complete"

exit 0
EOF
}

# Template: Deployment script
template_deployment_script() {
    cat > "$OUTPUT_FILE" <<EOF
#!/bin/bash
# $SCRIPT_NAME v1.0.0
# $DESCRIPTION
# Created: $(date +%Y-%m-%d)
# Author: $AUTHOR

set -euo pipefail

# Colors
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
CYAN='\\033[0;36m'
NC='\\033[0m'

SKIPPY_BASE="/home/dave/skippy"
SECRETS_MGR="\${SKIPPY_BASE}/scripts/security/secrets_manager_v1.0.0.sh"

log() {
    echo -e "\${BLUE}\$1\${NC}"
}

success() {
    echo -e "\${GREEN}✓ \$1\${NC}"
}

error() {
    echo -e "\${RED}✗ \$1\${NC}"
}

# Get credentials
PROD_HOST=\$(\$SECRETS_MGR get prod_ssh_host 2>/dev/null || echo "")
PROD_USER=\$(\$SECRETS_MGR get prod_ssh_user 2>/dev/null || echo "")

if [ -z "\$PROD_HOST" ] || [ -z "\$PROD_USER" ]; then
    error "Production credentials not configured"
    exit 1
fi

echo -e "\${CYAN}═══ $SCRIPT_NAME ═══\${NC}"
echo

# Step 1: Pre-deployment checks
log "Step 1: Pre-deployment checks"
# Add your pre-deployment validation here

# Step 2: Create backup
log "Step 2: Creating backup"
# Add backup creation here

# Step 3: Deploy
log "Step 3: Deploying to production"
# Add deployment commands here

# Step 4: Verify
log "Step 4: Verifying deployment"
# Add verification here

success "Deployment complete"

exit 0
EOF
}

# Template: Monitoring script
template_monitoring_script() {
    cat > "$OUTPUT_FILE" <<EOF
#!/bin/bash
# $SCRIPT_NAME v1.0.0
# $DESCRIPTION
# Created: $(date +%Y-%m-%d)
# Author: $AUTHOR

set -euo pipefail

# Configuration
SKIPPY_BASE="/home/dave/skippy"
ALERT_SCRIPT="\${SKIPPY_BASE}/scripts/monitoring/critical_alerter_v1.0.0.sh"
REPORT_FILE="\${SKIPPY_BASE}/conversations/monitoring/health_\$(date +%Y%m%d_%H%M%S).md"

# Colors
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m'

ISSUES=0

check() {
    local name="\$1"
    local command="\$2"

    if eval "\$command" &> /dev/null; then
        echo -e "\${GREEN}✓ \$name\${NC}"
        return 0
    else
        echo -e "\${RED}✗ \$name\${NC}"
        ((ISSUES++))
        return 1
    fi
}

echo "═══ Health Check ═══"
echo

# Add your health checks here
# Example:
# check "Database accessible" "mysql -e 'SELECT 1' &>/dev/null"
# check "Website responding" "curl -s https://rundaverun.org | grep -q 'Dave'"

echo
if [ \$ISSUES -eq 0 ]; then
    echo -e "\${GREEN}All checks passed\${NC}"
    exit 0
else
    echo -e "\${RED}Found \$ISSUES issues\${NC}"

    # Send alert
    if [ -x "\$ALERT_SCRIPT" ]; then
        "\$ALERT_SCRIPT" "HEALTH_CHECK_FAILED" "Found \$ISSUES issues"
    fi

    exit 1
fi
EOF
}

# Template: Security scanner
template_security_scanner() {
    cat > "$OUTPUT_FILE" <<EOF
#!/bin/bash
# $SCRIPT_NAME v1.0.0
# $DESCRIPTION
# Created: $(date +%Y-%m-%d)
# Author: $AUTHOR

set -euo pipefail

# Configuration
SKIPPY_BASE="/home/dave/skippy"
SCAN_REPORT="\${SKIPPY_BASE}/conversations/security_reports/scan_\$(date +%Y%m%d_%H%M%S).md"

# Colors
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m'

VULNERABILITIES=0

log() {
    echo -e "\${BLUE}\$1\${NC}"
}

warning() {
    echo -e "\${YELLOW}⚠ \$1\${NC}"
    ((VULNERABILITIES++))
}

error() {
    echo -e "\${RED}✗ \$1\${NC}"
    ((VULNERABILITIES++))
}

# Start report
mkdir -p "\$(dirname "\$SCAN_REPORT")"
cat > "\$SCAN_REPORT" <<REPORT
# Security Scan Report

**Date:** \$(date)
**Scanner:** $SCRIPT_NAME

---

## Findings

REPORT

log "Starting security scan..."

# Add your security checks here
# Example:
# if find /var/www -type f -perm 0777; then
#     error "World-writable files found"
# fi

# Summary
echo
if [ \$VULNERABILITIES -eq 0 ]; then
    echo -e "\${GREEN}✓ No vulnerabilities found\${NC}"
else
    echo -e "\${YELLOW}⚠ Found \$VULNERABILITIES issues\${NC}"
    echo "Report: \$SCAN_REPORT"
fi

exit 0
EOF
}

# Template: Python script
template_python_script() {
    cat > "$OUTPUT_FILE" <<'EOF'
#!/usr/bin/env python3
"""
$SCRIPT_NAME v1.0.0
$DESCRIPTION

Created: $(date +%Y-%m-%d)
Author: $AUTHOR
"""

import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/dave/skippy/logs/python_script.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main function"""
    logger.info("Starting $SCRIPT_NAME...")

    try:
        # Your code here
        pass

        logger.info("$SCRIPT_NAME completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF
}

# Generate template
echo -e "${BLUE}Generating template: $TEMPLATE_TYPE${NC}"

case "$TEMPLATE_TYPE" in
    bash-script)
        template_bash_script
        ;;
    wordpress-tool)
        template_wordpress_tool
        ;;
    backup-script)
        template_backup_script
        ;;
    deployment-script)
        template_deployment_script
        ;;
    monitoring-script)
        template_monitoring_script
        ;;
    security-scanner)
        template_security_scanner
        ;;
    cron-job)
        template_bash_script  # Same as basic bash but suitable for cron
        ;;
    python-script)
        template_python_script
        ;;
    validation-script)
        template_monitoring_script  # Similar structure
        ;;
    sync-script)
        template_deployment_script  # Similar structure
        ;;
    *)
        echo -e "${RED}Unknown template type: $TEMPLATE_TYPE${NC}"
        usage
        ;;
esac

# Make executable
chmod +x "$OUTPUT_FILE"

echo -e "${GREEN}✓ Template generated: $OUTPUT_FILE${NC}"
echo
echo "Details:"
echo "  Name: $SCRIPT_NAME"
echo "  Description: $DESCRIPTION"
echo "  Type: $TEMPLATE_TYPE"
echo
echo "Next steps:"
echo "  1. Edit $OUTPUT_FILE"
echo "  2. Add your custom logic"
echo "  3. Test the script"
echo "  4. Use in production"

exit 0
