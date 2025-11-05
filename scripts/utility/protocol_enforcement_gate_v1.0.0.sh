#!/bin/bash
# Protocol Enforcement Gate v1.0.0
# Blocks operations that don't follow protocols
# Part of: Skippy Enhancement Project - TIER 1
# Created: 2025-11-04

set -euo pipefail

OPERATION="$1"
SKIPPY_BASE="/home/dave/skippy"
PROTOCOL_DIR="${SKIPPY_BASE}/conversations"
LOG_FILE="${SKIPPY_BASE}/logs/protocol_enforcement.log"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

case "$OPERATION" in
    "wordpress-deploy")
        echo "Enforcing WordPress deployment protocol..."

        # Check pre-deployment validator was run
        LATEST_VALIDATION=$(find "${SKIPPY_BASE}/conversations/deployment_validation_reports" -name "*.md" -mmin -60 | wc -l)

        if [ "$LATEST_VALIDATION" -eq 0 ]; then
            echo "❌ BLOCKED: Pre-deployment validator not run in last hour"
            echo "Required: Run /home/dave/skippy/scripts/wordpress/pre_deployment_validator_v1.0.0.sh"
            log "BLOCKED wordpress-deploy: No recent validation report"
            exit 1
        fi

        # Check validation passed
        LATEST_REPORT=$(find "${SKIPPY_BASE}/conversations/deployment_validation_reports" -name "*.md" -mmin -60 | head -1)
        if grep -q "DEPLOYMENT BLOCKED" "$LATEST_REPORT"; then
            echo "❌ BLOCKED: Pre-deployment validation failed"
            echo "Fix errors in: $LATEST_REPORT"
            log "BLOCKED wordpress-deploy: Validation failed"
            exit 1
        fi

        echo "✓ Protocol check passed"
        log "ALLOWED wordpress-deploy: Validation passed"
        ;;

    "git-commit")
        echo "Enforcing git commit protocol..."

        # Check pre-commit hook exists
        if [ ! -f "${SKIPPY_BASE}/.git/hooks/pre-commit" ]; then
            echo "⚠️  WARNING: Pre-commit hook not installed"
        fi

        echo "✓ Protocol check passed"
        log "ALLOWED git-commit"
        ;;

    *)
        echo "Unknown operation: $OPERATION"
        exit 1
        ;;
esac

exit 0
