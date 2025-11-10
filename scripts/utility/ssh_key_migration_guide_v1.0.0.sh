#!/bin/bash
# SSH Key Migration Guide and Setup Tool
# Version: 1.0.0
# Purpose: Migrate from password to SSH key authentication
# Usage: ./ssh_key_migration_guide_v1.0.0.sh [--generate] [--install] [--test]

set -euo pipefail

# Colors
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[1;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_RESET='\033[0m'

# Configuration
SSH_KEY_PATH="${HOME}/.ssh/id_rsa_skippy"
REMOTE_HOST="${EBON_HOST:-}"
MODE="guide"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --generate)
            MODE="generate"
            shift
            ;;
        --install)
            MODE="install"
            shift
            ;;
        --test)
            MODE="test"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--generate] [--install] [--test]"
            exit 1
            ;;
    esac
done

#######################################
# Print colored message
#######################################
print_colored() {
    local color="$1"
    local message="$2"
    echo -e "${color}${message}${COLOR_RESET}"
}

#######################################
# Show migration guide
#######################################
show_guide() {
    print_colored "$COLOR_BLUE" "=================================================="
    print_colored "$COLOR_BLUE" "  SSH Key Migration Guide"
    print_colored "$COLOR_BLUE" "=================================================="
    echo ""
    print_colored "$COLOR_GREEN" "Why migrate to SSH keys?"
    echo "  • More secure than passwords"
    echo "  • No passwords stored in config files"
    echo "  • Easier automation (no password prompts)"
    echo "  • Industry best practice"
    echo ""

    print_colored "$COLOR_BLUE" "=== Step 1: Generate SSH Key ==="
    echo "Run: $0 --generate"
    echo ""
    echo "This will create:"
    echo "  • Private key: $SSH_KEY_PATH"
    echo "  • Public key: ${SSH_KEY_PATH}.pub"
    echo ""

    print_colored "$COLOR_BLUE" "=== Step 2: Install Public Key on Remote Server ==="
    echo "Run: $0 --install"
    echo ""
    echo "This will:"
    echo "  • Copy your public key to $REMOTE_HOST"
    echo "  • Add it to ~/.ssh/authorized_keys"
    echo "  • Set correct permissions"
    echo ""

    print_colored "$COLOR_BLUE" "=== Step 3: Test SSH Connection ==="
    echo "Run: $0 --test"
    echo ""
    echo "This will verify the key-based authentication works"
    echo ""

    print_colored "$COLOR_BLUE" "=== Step 4: Update Configuration ==="
    echo "Add to config.env:"
    echo ""
    print_colored "$COLOR_YELLOW" "  export SSH_PRIVATE_KEY=\"$SSH_KEY_PATH\""
    print_colored "$COLOR_YELLOW" "  # export EBON_PASSWORD=\"...\"  # Comment out or remove"
    echo ""

    print_colored "$COLOR_BLUE" "=== Step 5: Update Scripts ==="
    echo "Update any scripts using password authentication to use key-based auth"
    echo ""
}

#######################################
# Generate SSH key
#######################################
generate_key() {
    print_colored "$COLOR_BLUE" "Generating SSH key..."
    echo ""

    if [[ -f "$SSH_KEY_PATH" ]]; then
        print_colored "$COLOR_YELLOW" "⚠️  SSH key already exists: $SSH_KEY_PATH"
        read -p "Overwrite? (y/n) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_colored "$COLOR_YELLOW" "Aborted"
            exit 0
        fi
    fi

    # Generate key
    ssh-keygen -t rsa -b 4096 -f "$SSH_KEY_PATH" -N "" -C "skippy@$(hostname)"

    # Set permissions
    chmod 600 "$SSH_KEY_PATH"
    chmod 644 "${SSH_KEY_PATH}.pub"

    print_colored "$COLOR_GREEN" "✓ SSH key generated successfully!"
    echo ""
    echo "Private key: $SSH_KEY_PATH"
    echo "Public key:  ${SSH_KEY_PATH}.pub"
    echo ""
    print_colored "$COLOR_YELLOW" "⚠️  Keep your private key secure!"
    print_colored "$COLOR_YELLOW" "⚠️  Never share your private key"
    echo ""
    print_colored "$COLOR_BLUE" "Next step: Run $0 --install"
}

#######################################
# Install public key on remote server
#######################################
install_key() {
    print_colored "$COLOR_BLUE" "Installing public key on remote server..."
    echo ""

    if [[ -z "$REMOTE_HOST" ]]; then
        print_colored "$COLOR_RED" "❌ ERROR: EBON_HOST not set"
        echo "Set EBON_HOST in config.env or export it"
        exit 1
    fi

    if [[ ! -f "${SSH_KEY_PATH}.pub" ]]; then
        print_colored "$COLOR_RED" "❌ ERROR: Public key not found"
        echo "Run: $0 --generate first"
        exit 1
    fi

    print_colored "$COLOR_BLUE" "Remote host: $REMOTE_HOST"
    echo ""
    print_colored "$COLOR_YELLOW" "You will be prompted for your password"
    echo ""

    # Copy public key using ssh-copy-id (recommended)
    if command -v ssh-copy-id >/dev/null 2>&1; then
        ssh-copy-id -i "$SSH_KEY_PATH" "$REMOTE_HOST"
    else
        # Manual method if ssh-copy-id not available
        cat "${SSH_KEY_PATH}.pub" | ssh "$REMOTE_HOST" \
            "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
    fi

    print_colored "$COLOR_GREEN" "✓ Public key installed successfully!"
    echo ""
    print_colored "$COLOR_BLUE" "Next step: Run $0 --test"
}

#######################################
# Test SSH connection
#######################################
test_connection() {
    print_colored "$COLOR_BLUE" "Testing SSH connection..."
    echo ""

    if [[ -z "$REMOTE_HOST" ]]; then
        print_colored "$COLOR_RED" "❌ ERROR: EBON_HOST not set"
        exit 1
    fi

    if [[ ! -f "$SSH_KEY_PATH" ]]; then
        print_colored "$COLOR_RED" "❌ ERROR: Private key not found"
        echo "Run: $0 --generate first"
        exit 1
    fi

    print_colored "$COLOR_BLUE" "Attempting connection to $REMOTE_HOST..."

    if ssh -i "$SSH_KEY_PATH" -o BatchMode=yes -o ConnectTimeout=5 "$REMOTE_HOST" exit 2>/dev/null; then
        print_colored "$COLOR_GREEN" "✓ SSH key authentication successful!"
        echo ""
        print_colored "$COLOR_GREEN" "✅ Migration complete!"
        echo ""
        print_colored "$COLOR_BLUE" "Next steps:"
        echo "1. Add to config.env: export SSH_PRIVATE_KEY=\"$SSH_KEY_PATH\""
        echo "2. Remove or comment out: EBON_PASSWORD"
        echo "3. Update scripts to use key-based authentication"
    else
        print_colored "$COLOR_RED" "❌ SSH key authentication failed"
        echo ""
        print_colored "$COLOR_YELLOW" "Troubleshooting:"
        echo "1. Verify public key is installed: ssh $REMOTE_HOST 'cat ~/.ssh/authorized_keys'"
        echo "2. Check permissions: ssh $REMOTE_HOST 'ls -la ~/.ssh/'"
        echo "3. Try manual connection: ssh -i $SSH_KEY_PATH $REMOTE_HOST"
        exit 1
    fi
}

#######################################
# Main function
#######################################
main() {
    case "$MODE" in
        guide)
            show_guide
            ;;
        generate)
            generate_key
            ;;
        install)
            install_key
            ;;
        test)
            test_connection
            ;;
    esac
}

main
