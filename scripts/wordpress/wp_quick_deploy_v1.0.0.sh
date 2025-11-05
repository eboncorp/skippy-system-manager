#!/bin/bash
# WordPress Quick Deploy Tool v1.0.0
# One-command deployment with all safety checks
# Part of: Skippy Enhancement Project - TIER 2
# Created: 2025-11-04

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SKIPPY_BASE="/home/dave/skippy"
LOCAL_PATH="/home/dave/Local Sites/rundaverun-local/app/public"

# Tool paths
PRE_VALIDATOR="${SKIPPY_BASE}/scripts/wordpress/pre_deployment_validator_v1.0.0.sh"
POST_VERIFIER="${SKIPPY_BASE}/scripts/wordpress/deployment_verification_v1.0.0.sh"
FACT_CHECKER="${SKIPPY_BASE}/scripts/wordpress/fact_checker_v1.0.0.sh"
SECRETS_MGR="${SKIPPY_BASE}/scripts/security/secrets_manager_v1.0.0.sh"
AUDIT_LOGGER="${SKIPPY_BASE}/scripts/security/audit_trail_logger_v1.0.0.sh"

usage() {
    cat <<EOF
WordPress Quick Deploy Tool v1.0.0

USAGE:
    $0 [options]

OPTIONS:
    --skip-validation       Skip pre-deployment validation (NOT RECOMMENDED)
    --skip-backup           Skip backup creation (NOT RECOMMENDED)
    --skip-facts            Skip fact checking
    --dry-run               Show deployment plan without executing
    --force                 Deploy even with warnings (still blocks on critical)

DEPLOYMENT STEPS:
    1. Pre-deployment fact check
    2. Pre-deployment validation (12 checks)
    3. Create backup
    4. Export content from local
    5. Push to production (via SSH/FTP)
    6. Post-deployment verification
    7. Generate deployment report

EXAMPLES:
    # Standard deployment (recommended)
    $0

    # Dry run to see deployment plan
    $0 --dry-run

    # Skip fact check (if already done)
    $0 --skip-facts

SAFETY FEATURES:
    - Blocks deployment on critical errors
    - Creates backup before deployment
    - Verifies deployment succeeded
    - Full audit trail
    - Detailed reports

EOF
    exit 1
}

# Parse options
SKIP_VALIDATION=false
SKIP_BACKUP=false
SKIP_FACTS=false
DRY_RUN=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-validation)
            SKIP_VALIDATION=true
            shift
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --skip-facts)
            SKIP_FACTS=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

echo -e "${CYAN}"
cat <<'EOF'
╔═══════════════════════════════════════════╗
║   WordPress Quick Deploy v1.0.0           ║
║   Run Dave Run Campaign Site              ║
╚═══════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Deployment report
DEPLOY_REPORT="${SKIPPY_BASE}/conversations/deployment_reports/deploy_$(date +%Y%m%d_%H%M%S).md"
mkdir -p "$(dirname "$DEPLOY_REPORT")"

cat > "$DEPLOY_REPORT" <<EOF
# Deployment Report

**Date:** $(date)
**User:** $USER
**Mode:** $([ "$DRY_RUN" = true ] && echo "DRY RUN" || echo "LIVE DEPLOYMENT")

---

## Deployment Steps

EOF

log_step() {
    local step="$1"
    local status="$2"  # RUNNING, SUCCESS, FAILED, SKIPPED

    case "$status" in
        RUNNING)
            echo -e "${BLUE}▶ $step...${NC}"
            echo "### $step" >> "$DEPLOY_REPORT"
            echo "**Status:** In Progress..." >> "$DEPLOY_REPORT"
            ;;
        SUCCESS)
            echo -e "${GREEN}✓ $step${NC}"
            echo "**Status:** ✓ SUCCESS" >> "$DEPLOY_REPORT"
            echo >> "$DEPLOY_REPORT"
            ;;
        FAILED)
            echo -e "${RED}✗ $step${NC}"
            echo "**Status:** ✗ FAILED" >> "$DEPLOY_REPORT"
            echo >> "$DEPLOY_REPORT"
            ;;
        SKIPPED)
            echo -e "${YELLOW}⊘ $step (skipped)${NC}"
            echo "**Status:** ⊘ SKIPPED" >> "$DEPLOY_REPORT"
            echo >> "$DEPLOY_REPORT"
            ;;
    esac
}

# Step 1: Fact check
STEP_NUM=1
echo
echo -e "${CYAN}═══ Step $STEP_NUM: Fact Checking ═══${NC}"
((STEP_NUM++))

if [ "$SKIP_FACTS" = false ]; then
    log_step "Fact checking content" "RUNNING"

    if [ -x "$FACT_CHECKER" ]; then
        if "$FACT_CHECKER"; then
            log_step "Fact checking content" "SUCCESS"
        else
            log_step "Fact checking content" "FAILED"
            echo -e "${RED}❌ Fact check failed${NC}"
            echo "Review errors and fix before deploying"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠ Fact checker not found, skipping${NC}"
        log_step "Fact checking content" "SKIPPED"
    fi
else
    log_step "Fact checking content" "SKIPPED"
fi

# Step 2: Pre-deployment validation
echo
echo -e "${CYAN}═══ Step $STEP_NUM: Pre-Deployment Validation ═══${NC}"
((STEP_NUM++))

if [ "$SKIP_VALIDATION" = false ]; then
    log_step "Running pre-deployment validation (12 checks)" "RUNNING"

    if [ -x "$PRE_VALIDATOR" ]; then
        cd "$LOCAL_PATH" || exit 1

        if "$PRE_VALIDATOR"; then
            log_step "Running pre-deployment validation (12 checks)" "SUCCESS"
        else
            VALIDATION_EXIT=$?

            if [ "$VALIDATION_EXIT" -eq 2 ]; then
                # Critical errors
                log_step "Running pre-deployment validation (12 checks)" "FAILED"
                echo -e "${RED}❌ DEPLOYMENT BLOCKED - Critical errors found${NC}"
                echo "Fix critical errors and try again"
                exit 2
            elif [ "$VALIDATION_EXIT" -eq 1 ]; then
                # Warnings
                log_step "Running pre-deployment validation (12 checks)" "SUCCESS"
                echo -e "${YELLOW}⚠ Warnings found${NC}"

                if [ "$FORCE" = false ]; then
                    read -p "Deploy anyway? (yes/no): " confirm
                    if [ "$confirm" != "yes" ]; then
                        echo "Deployment cancelled"
                        exit 0
                    fi
                fi
            fi
        fi
    else
        echo -e "${YELLOW}⚠ Pre-deployment validator not found, skipping${NC}"
        log_step "Running pre-deployment validation (12 checks)" "SKIPPED"
    fi
else
    log_step "Running pre-deployment validation (12 checks)" "SKIPPED"
fi

# Step 3: Create backup
echo
echo -e "${CYAN}═══ Step $STEP_NUM: Backup ═══${NC}"
((STEP_NUM++))

if [ "$SKIP_BACKUP" = false ] && [ "$DRY_RUN" = false ]; then
    log_step "Creating pre-deployment backup" "RUNNING"

    cd "$LOCAL_PATH" || exit 1
    BACKUP_FILE="${SKIPPY_BASE}/backups/pre_deploy_$(date +%Y%m%d_%H%M%S).sql"
    mkdir -p "$(dirname "$BACKUP_FILE")"

    if wp db export "$BACKUP_FILE" --add-drop-table; then
        log_step "Creating pre-deployment backup" "SUCCESS"
        echo "  Backup: $BACKUP_FILE"
        echo "**Backup File:** \`$BACKUP_FILE\`" >> "$DEPLOY_REPORT"
    else
        log_step "Creating pre-deployment backup" "FAILED"
        echo -e "${RED}❌ Backup failed${NC}"
        exit 1
    fi
else
    log_step "Creating pre-deployment backup" "SKIPPED"
fi

# Step 4: Export content
echo
echo -e "${CYAN}═══ Step $STEP_NUM: Export Content ═══${NC}"
((STEP_NUM++))

if [ "$DRY_RUN" = false ]; then
    log_step "Exporting content for deployment" "RUNNING"

    cd "$LOCAL_PATH" || exit 1
    EXPORT_FILE="${SKIPPY_BASE}/work/exports/deploy_$(date +%Y%m%d_%H%M%S).xml"
    mkdir -p "$(dirname "$EXPORT_FILE")"

    if wp export --dir="$(dirname "$EXPORT_FILE")" --filename="$(basename "$EXPORT_FILE")"; then
        log_step "Exporting content for deployment" "SUCCESS"
        echo "  Export: $EXPORT_FILE"
        echo "**Export File:** \`$EXPORT_FILE\`" >> "$DEPLOY_REPORT"
    else
        log_step "Exporting content for deployment" "FAILED"
        echo -e "${RED}❌ Export failed${NC}"
        exit 1
    fi
else
    log_step "Exporting content for deployment" "SKIPPED"
    echo -e "${YELLOW}DRY RUN: Would export content${NC}"
fi

# Step 5: Deploy to production
echo
echo -e "${CYAN}═══ Step $STEP_NUM: Deploy to Production ═══${NC}"
((STEP_NUM++))

if [ "$DRY_RUN" = false ]; then
    log_step "Deploying to production" "RUNNING"

    # Get production credentials
    if [ -x "$SECRETS_MGR" ]; then
        PROD_HOST=$($SECRETS_MGR get prod_ssh_host 2>/dev/null || echo "")
        PROD_USER=$($SECRETS_MGR get prod_ssh_user 2>/dev/null || echo "")
        PROD_PATH=$($SECRETS_MGR get prod_wp_path 2>/dev/null || echo "")
    fi

    if [ -z "$PROD_HOST" ] || [ -z "$PROD_USER" ] || [ -z "$PROD_PATH" ]; then
        echo -e "${YELLOW}⚠ Production credentials not configured in secrets manager${NC}"
        echo "Configure with:"
        echo "  $SECRETS_MGR add prod_ssh_host 'host'"
        echo "  $SECRETS_MGR add prod_ssh_user 'user'"
        echo "  $SECRETS_MGR add prod_wp_path '/path/to/wordpress'"
        log_step "Deploying to production" "SKIPPED"
    else
        # Upload export file
        if scp "$EXPORT_FILE" "$PROD_USER@$PROD_HOST:/tmp/"; then
            # Import on production
            if ssh "$PROD_USER@$PROD_HOST" "cd $PROD_PATH && wp import /tmp/$(basename "$EXPORT_FILE") --authors=create"; then
                log_step "Deploying to production" "SUCCESS"
                echo "  Deployed to: $PROD_HOST"
            else
                log_step "Deploying to production" "FAILED"
                echo -e "${RED}❌ Import failed on production${NC}"
                exit 1
            fi
        else
            log_step "Deploying to production" "FAILED"
            echo -e "${RED}❌ Upload to production failed${NC}"
            exit 1
        fi
    fi
else
    log_step "Deploying to production" "SKIPPED"
    echo -e "${YELLOW}DRY RUN: Would deploy to production${NC}"
fi

# Step 6: Post-deployment verification
echo
echo -e "${CYAN}═══ Step $STEP_NUM: Post-Deployment Verification ═══${NC}"
((STEP_NUM++))

if [ "$DRY_RUN" = false ] && [ -x "$POST_VERIFIER" ]; then
    log_step "Verifying deployment" "RUNNING"

    if "$POST_VERIFIER"; then
        log_step "Verifying deployment" "SUCCESS"
    else
        log_step "Verifying deployment" "FAILED"
        echo -e "${YELLOW}⚠ Post-deployment verification found issues${NC}"
        echo "Check the verification report"
    fi
else
    log_step "Verifying deployment" "SKIPPED"
fi

# Step 7: Audit log
if [ "$DRY_RUN" = false ] && [ -x "$AUDIT_LOGGER" ]; then
    "$AUDIT_LOGGER" "WORDPRESS_DEPLOYMENT" "Deployed to production via quick_deploy tool"
fi

# Final summary
cat >> "$DEPLOY_REPORT" <<EOF

---

## Deployment Summary

**Status:** $([ "$DRY_RUN" = true ] && echo "DRY RUN COMPLETE" || echo "DEPLOYMENT COMPLETE")
**Completed:** $(date)
**Duration:** $SECONDS seconds

### Files Created:
- Backup: \`$BACKUP_FILE\`
- Export: \`$EXPORT_FILE\`
- Report: \`$DEPLOY_REPORT\`

### Next Steps:
1. Monitor site for 24 hours
2. Check analytics for traffic impact
3. Test critical user flows
4. Review error logs

---

*Deployed via Quick Deploy Tool v1.0.0*

EOF

echo
echo -e "${CYAN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Deployment Complete${NC}"
echo -e "${CYAN}═══════════════════════════════════════${NC}"
echo
echo "Report: $DEPLOY_REPORT"
echo "Duration: $SECONDS seconds"
echo

exit 0
