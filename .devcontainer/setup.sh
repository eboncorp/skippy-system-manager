#!/bin/bash
# Development Container Setup Script
# Runs after container is created

set -e

echo "═══════════════════════════════════════════════════"
echo "  Skippy Development Container Setup"
echo "═══════════════════════════════════════════════════"
echo ""

# Update system
echo "Updating system packages..."
apt-get update
apt-get install -y \
    curl \
    wget \
    jq \
    sqlite3 \
    shellcheck \
    bc \
    time

# Install WP-CLI
echo "Installing WP-CLI..."
curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
chmod +x wp-cli.phar
mv wp-cli.phar /usr/local/bin/wp

# Install Python dependencies
if [[ -f /workspace/requirements.txt ]]; then
    echo "Installing Python dependencies..."
    pip install -r /workspace/requirements.txt
else
    echo "Installing common Python packages..."
    pip install pylint black pytest
fi

# Set up bash aliases
echo "Setting up bash aliases..."
cat >> ~/.bashrc <<'EOF'

# Skippy aliases
alias skippy-script="/workspace/bin/skippy-script"
alias health-dashboard="/workspace/bin/health-dashboard"
alias generate-docs="/workspace/bin/generate-docs"
alias wplocal="wp --path=/workspace/websites/rundaverun/local_site/app/public"

# Development aliases
alias ll='ls -lah'
alias gs='git status'
alias gd='git diff'
alias gl='git log --oneline -10'

# Load environment profile if available
if [[ -f /workspace/bin/skippy-profile ]]; then
    echo "Skippy tools available:"
    echo "  skippy-script - Script management"
    echo "  health-dashboard - System health"
    echo "  generate-docs - Documentation"
fi
EOF

# Make all bin scripts executable
if [[ -d /workspace/bin ]]; then
    echo "Making bin scripts executable..."
    chmod +x /workspace/bin/*
fi

# Initialize history database
if [[ -f /workspace/bin/history-enhanced ]]; then
    echo "Initializing command history..."
    /workspace/bin/history-enhanced init
fi

# Create necessary directories
mkdir -p /workspace/{work,documentation/runbooks,development/tests/results}

echo ""
echo "✅ Development environment ready!"
echo ""
echo "Quick Start:"
echo "  health-dashboard     - Check system status"
echo "  skippy-script stats  - View script statistics"
echo "  generate-docs        - Generate documentation"
echo ""
