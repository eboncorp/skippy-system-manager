#!/bin/bash
# Development Environment Setup Tool v1.0.0
# One-command setup for new development environments
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

usage() {
    cat <<EOF
Development Environment Setup Tool v1.0.0

USAGE:
    $0 <command> [options]

COMMANDS:
    init                         Initialize new development environment
    check                        Check current environment setup
    fix                          Fix common environment issues
    install-tools                Install all required development tools
    configure-wordpress          Configure WordPress development site
    setup-secrets                Initialize secrets management
    setup-git                    Configure git settings
    setup-cron                   Install all cron jobs
    full-setup                   Complete setup (all of the above)

OPTIONS:
    --skip-install               Skip package installation
    --skip-wordpress             Skip WordPress setup
    --dry-run                    Show what would be done

EXAMPLES:
    # Check current environment
    $0 check

    # Full setup on new machine
    $0 full-setup

    # Fix issues
    $0 fix

    # Just install tools
    $0 install-tools

REQUIREMENTS:
    - Ubuntu/Debian Linux
    - sudo access
    - Internet connection

EOF
    exit 1
}

# Parse options
SKIP_INSTALL=false
SKIP_WORDPRESS=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-install)
            SKIP_INSTALL=true
            shift
            ;;
        --skip-wordpress)
            SKIP_WORDPRESS=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            break
            ;;
    esac
done

COMMAND="${1:-}"

if [ -z "$COMMAND" ]; then
    usage
fi

echo -e "${CYAN}"
cat <<'EOF'
╔═══════════════════════════════════════════╗
║   Dev Environment Setup v1.0.0            ║
║   Run Dave Run Campaign Infrastructure    ║
╚═══════════════════════════════════════════╝
EOF
echo -e "${NC}"

log() {
    echo -e "${BLUE}▶ $1${NC}"
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if command exists
check_command() {
    local cmd="$1"
    local name="$2"

    if command -v "$cmd" &> /dev/null; then
        success "$name installed ($(command -v "$cmd"))"
        return 0
    else
        warning "$name NOT installed"
        return 1
    fi
}

# Check environment
check_environment() {
    log "Checking development environment..."
    echo

    local issues=0

    # Essential tools
    echo "Essential Tools:"
    check_command "bash" "Bash" || ((issues++))
    check_command "git" "Git" || ((issues++))
    check_command "curl" "cURL" || ((issues++))
    check_command "jq" "jq (JSON processor)" || ((issues++))
    echo

    # WordPress tools
    echo "WordPress Tools:"
    check_command "wp" "WP-CLI" || ((issues++))
    check_command "php" "PHP" || ((issues++))
    check_command "mysql" "MySQL" || ((issues++))
    echo

    # Python tools
    echo "Python Tools:"
    check_command "python3" "Python 3" || ((issues++))
    check_command "pip3" "pip3" || ((issues++))
    echo

    # Security tools
    echo "Security Tools:"
    check_command "gpg" "GPG (for secrets)" || ((issues++))
    check_command "ssh" "SSH" || ((issues++))
    echo

    # Skippy structure
    echo "Skippy Structure:"

    local dirs=(
        "$SKIPPY_BASE/scripts"
        "$SKIPPY_BASE/conversations"
        "$SKIPPY_BASE/logs"
        "$SKIPPY_BASE/backups"
        "$SKIPPY_BASE/work"
        "$SKIPPY_BASE/documentation"
    )

    for dir in "${dirs[@]}"; do
        if [ -d "$dir" ]; then
            success "$(basename "$dir")/ exists"
        else
            warning "$(basename "$dir")/ missing"
            ((issues++))
        fi
    done

    echo
    echo "════════════════════════════════════"

    if [ $issues -eq 0 ]; then
        success "Environment check passed!"
        return 0
    else
        warning "Found $issues issues"
        echo
        echo "Run: $0 fix"
        return 1
    fi
}

# Install required tools
install_tools() {
    if [ "$SKIP_INSTALL" = true ]; then
        warning "Skipping package installation"
        return
    fi

    log "Installing development tools..."

    if [ "$DRY_RUN" = true ]; then
        warning "DRY RUN: Would install packages"
        return
    fi

    # Check for sudo
    if ! sudo -n true 2>/dev/null; then
        error "This requires sudo access"
        echo "Run: sudo -v"
        exit 1
    fi

    # Update package list
    log "Updating package list..."
    sudo apt update

    # Essential packages
    local packages=(
        git
        curl
        wget
        jq
        gnupg
        ca-certificates
        openssh-client
        rsync
        zip
        unzip
        python3
        python3-pip
        php
        php-cli
        php-mysql
        php-xml
        php-mbstring
        mysql-client
    )

    for pkg in "${packages[@]}"; do
        if dpkg -l | grep -q "^ii  $pkg "; then
            success "$pkg already installed"
        else
            log "Installing $pkg..."
            sudo apt install -y "$pkg"
        fi
    done

    # Install WP-CLI if not present
    if ! command -v wp &> /dev/null; then
        log "Installing WP-CLI..."
        curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
        chmod +x wp-cli.phar
        sudo mv wp-cli.phar /usr/local/bin/wp
        success "WP-CLI installed"
    else
        success "WP-CLI already installed"
    fi

    success "All tools installed"
}

# Fix common issues
fix_issues() {
    log "Fixing common environment issues..."

    # Create missing directories
    local dirs=(
        "$SKIPPY_BASE/scripts"
        "$SKIPPY_BASE/conversations"
        "$SKIPPY_BASE/logs/security"
        "$SKIPPY_BASE/logs/alerts"
        "$SKIPPY_BASE/backups"
        "$SKIPPY_BASE/work/active"
        "$SKIPPY_BASE/work/archive"
        "$SKIPPY_BASE/documentation"
        "$SKIPPY_BASE/.secrets"
        "$SKIPPY_BASE/conversations/error_logs"
        "$SKIPPY_BASE/conversations/deployment_validation_reports"
        "$SKIPPY_BASE/conversations/security_reports"
        "$SKIPPY_BASE/conversations/backup_reports"
    )

    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            if [ "$DRY_RUN" = false ]; then
                mkdir -p "$dir"
                success "Created: $dir"
            else
                warning "Would create: $dir"
            fi
        fi
    done

    # Fix permissions
    if [ "$DRY_RUN" = false ]; then
        chmod 700 "$SKIPPY_BASE/.secrets" 2>/dev/null || true
        success "Fixed permissions on .secrets/"
    fi

    success "Issues fixed"
}

# Setup secrets management
setup_secrets() {
    log "Setting up secrets management..."

    local secrets_mgr="${SKIPPY_BASE}/scripts/security/secrets_manager_v1.0.0.sh"

    if [ ! -x "$secrets_mgr" ]; then
        error "Secrets manager not found: $secrets_mgr"
        return 1
    fi

    if [ -f "${SKIPPY_BASE}/.secrets/vault.gpg" ]; then
        success "Secrets vault already initialized"
    else
        if [ "$DRY_RUN" = false ]; then
            log "Initializing secrets vault..."
            "$secrets_mgr" init
        else
            warning "Would initialize secrets vault"
        fi
    fi

    success "Secrets management ready"
}

# Setup git configuration
setup_git() {
    log "Configuring git..."

    # Check if git configured
    if git config --global user.name &> /dev/null; then
        local name=$(git config --global user.name)
        success "Git already configured: $name"
    else
        if [ "$DRY_RUN" = false ]; then
            echo
            read -p "Git user name: " git_name
            read -p "Git user email: " git_email

            git config --global user.name "$git_name"
            git config --global user.email "$git_email"

            success "Git configured"
        else
            warning "Would configure git"
        fi
    fi

    # Recommended git settings
    if [ "$DRY_RUN" = false ]; then
        git config --global core.editor "nano"
        git config --global init.defaultBranch "main"
        git config --global pull.rebase false
        success "Git settings optimized"
    fi
}

# Setup cron jobs
setup_cron() {
    log "Setting up cron jobs..."

    # Check if cron jobs already exist
    if crontab -l 2>/dev/null | grep -q "skippy"; then
        success "Skippy cron jobs already installed"
        return
    fi

    if [ "$DRY_RUN" = true ]; then
        warning "Would install cron jobs"
        return
    fi

    # Backup existing crontab
    crontab -l > /tmp/crontab_backup 2>/dev/null || true

    # Add skippy cron jobs
    (crontab -l 2>/dev/null; cat <<'CRON'

# Skippy Enhancement System Automation
# Added by dev_environment_setup v1.0.0

# Work files cleanup - 3:30 AM daily
30 3 * * * /home/dave/skippy/development/scripts/scripts/cleanup_work_files.sh >/dev/null 2>&1

# Security scan - 2 AM Sundays
0 2 * * 0 /home/dave/skippy/development/scripts/scripts/security/vulnerability_scanner_v1.0.0.sh >/dev/null 2>&1

# Backup verification - 4 AM on 1st of month
0 4 1 * * /home/dave/skippy/development/scripts/scripts/backup/backup_verification_test_v1.0.0.sh >/dev/null 2>&1

CRON
) | crontab -

    success "Cron jobs installed"
}

# Configure WordPress
configure_wordpress() {
    if [ "$SKIP_WORDPRESS" = true ]; then
        warning "Skipping WordPress configuration"
        return
    fi

    log "Configuring WordPress development site..."

    local wp_path="/home/dave/Local Sites/rundaverun-local/app/public"

    if [ ! -d "$wp_path" ]; then
        warning "WordPress site not found at: $wp_path"
        warning "Install Local by Flywheel and create 'rundaverun-local' site"
        return
    fi

    cd "$wp_path" || return 1

    # Check if WP installed
    if wp core is-installed 2>/dev/null; then
        success "WordPress installed and configured"
    else
        warning "WordPress not fully configured"
        if [ "$DRY_RUN" = false ]; then
            echo
            read -p "Configure WordPress now? (yes/no): " confirm
            if [ "$confirm" = "yes" ]; then
                wp core install \
                    --url="http://rundaverun.local" \
                    --title="Run Dave Run (Development)" \
                    --admin_user="admin" \
                    --admin_email="dave@rundaverun.org" \
                    --skip-email

                success "WordPress configured"
            fi
        fi
    fi
}

# Initialize new environment
init_environment() {
    log "Initializing development environment..."

    # Create base structure
    fix_issues

    success "Environment initialized"
}

# Full setup
full_setup() {
    log "Starting full development environment setup..."
    echo

    echo -e "${CYAN}Step 1: Initialize structure${NC}"
    init_environment
    echo

    echo -e "${CYAN}Step 2: Install tools${NC}"
    install_tools
    echo

    echo -e "${CYAN}Step 3: Setup git${NC}"
    setup_git
    echo

    echo -e "${CYAN}Step 4: Setup secrets management${NC}"
    setup_secrets
    echo

    echo -e "${CYAN}Step 5: Configure WordPress${NC}"
    configure_wordpress
    echo

    echo -e "${CYAN}Step 6: Setup cron jobs${NC}"
    setup_cron
    echo

    echo -e "${GREEN}═══════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ Full setup complete!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════${NC}"
    echo
    echo "Next steps:"
    echo "1. Review cron jobs: crontab -l"
    echo "2. Add production credentials to secrets manager"
    echo "3. Test deployment: cd $SKIPPY_BASE && scripts/wordpress/pre_deployment_validator_v1.0.0.sh"
}

# Main command dispatcher
case "$COMMAND" in
    check)
        check_environment
        ;;
    init)
        init_environment
        ;;
    fix)
        fix_issues
        ;;
    install-tools)
        install_tools
        ;;
    configure-wordpress)
        configure_wordpress
        ;;
    setup-secrets)
        setup_secrets
        ;;
    setup-git)
        setup_git
        ;;
    setup-cron)
        setup_cron
        ;;
    full-setup)
        full_setup
        ;;
    *)
        echo "Unknown command: $COMMAND"
        usage
        ;;
esac

exit 0
