#!/bin/bash
# Backup Encryption Script
# Version: 1.0.0
# Purpose: Encrypt backup files using GPG
# Usage: ./encrypt_backup_v1.0.0.sh <backup_file> [recipient_email]

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
DEFAULT_RECIPIENT="${GPG_RECIPIENT:-admin@example.com}"
BACKUP_FILE="${1:-}"
RECIPIENT="${2:-${DEFAULT_RECIPIENT}}"

# Help
if [ "${BACKUP_FILE}" == "--help" ] || [ "${BACKUP_FILE}" == "-h" ]; then
    cat <<EOF
Backup Encryption Script v1.0.0

Usage:
    $0 <backup_file> [recipient_email]

Arguments:
    backup_file      Path to backup file to encrypt
    recipient_email  GPG recipient email (optional, uses GPG_RECIPIENT env var or default)

Examples:
    $0 backup.tar.gz
    $0 backup.tar.gz user@example.com
    GPG_RECIPIENT=admin@example.com $0 backup.tar.gz

Environment Variables:
    GPG_RECIPIENT    Default GPG recipient email

EOF
    exit 0
fi

# Validate input
if [ -z "${BACKUP_FILE}" ]; then
    echo -e "${RED}Error: No backup file specified${NC}"
    echo "Usage: $0 <backup_file> [recipient_email]"
    exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    echo -e "${RED}Error: Backup file not found: ${BACKUP_FILE}${NC}"
    exit 1
fi

# Check if GPG is installed
if ! command -v gpg >/dev/null 2>&1; then
    echo -e "${RED}Error: GPG not installed${NC}"
    echo "Install with: sudo apt-get install gnupg"
    exit 1
fi

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}  Backup Encryption${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""
echo "  File: ${BACKUP_FILE}"
echo "  Size: $(du -h "${BACKUP_FILE}" | cut -f1)"
echo "  Recipient: ${RECIPIENT}"
echo ""

# Check if recipient key exists
echo -e "${YELLOW}Checking GPG keys...${NC}"
if ! gpg --list-keys "${RECIPIENT}" >/dev/null 2>&1; then
    echo -e "${YELLOW}Warning: GPG key for ${RECIPIENT} not found${NC}"
    echo ""
    echo "Would you like to:"
    echo "  1) Generate a new key pair"
    echo "  2) Import an existing key"
    echo "  3) Use symmetric encryption (password-based)"
    echo "  4) Exit"
    read -p "Choice (1-4): " choice

    case ${choice} in
        1)
            echo "Generating new GPG key..."
            gpg --quick-gen-key "${RECIPIENT}" default default 0
            ;;
        2)
            echo "Please import your key first:"
            echo "  gpg --import /path/to/key.asc"
            exit 1
            ;;
        3)
            echo -e "${YELLOW}Using symmetric encryption${NC}"
            SYMMETRIC=true
            ;;
        *)
            echo "Exiting"
            exit 0
            ;;
    esac
fi

# Encrypt the backup
ENCRYPTED_FILE="${BACKUP_FILE}.gpg"

echo -e "${YELLOW}Encrypting backup...${NC}"

if [ "${SYMMETRIC:-false}" == "true" ]; then
    # Symmetric encryption (password-based)
    gpg --symmetric --cipher-algo AES256 --output "${ENCRYPTED_FILE}" "${BACKUP_FILE}"
else
    # Public key encryption
    gpg --encrypt --recipient "${RECIPIENT}" --trust-model always --output "${ENCRYPTED_FILE}" "${BACKUP_FILE}"
fi

if [ -f "${ENCRYPTED_FILE}" ]; then
    echo -e "${GREEN}✓ Encryption successful${NC}"
    echo ""
    echo "Encrypted file: ${ENCRYPTED_FILE}"
    echo "Encrypted size: $(du -h "${ENCRYPTED_FILE}" | cut -f1)"
    echo ""

    # Calculate checksums
    echo -e "${YELLOW}Generating checksums...${NC}"
    sha256sum "${ENCRYPTED_FILE}" > "${ENCRYPTED_FILE}.sha256"
    echo -e "${GREEN}✓ Checksum saved: ${ENCRYPTED_FILE}.sha256${NC}"
    echo ""

    # Test decryption
    read -p "Test decryption? (y/n): " test_decrypt
    if [[ "${test_decrypt}" == "y" ]]; then
        echo -e "${YELLOW}Testing decryption...${NC}"
        TEST_FILE="/tmp/test_decrypt_$$"

        if [ "${SYMMETRIC:-false}" == "true" ]; then
            gpg --decrypt --output "${TEST_FILE}" "${ENCRYPTED_FILE}"
        else
            gpg --decrypt --output "${TEST_FILE}" "${ENCRYPTED_FILE}"
        fi

        if [ -f "${TEST_FILE}" ]; then
            # Verify checksums match
            ORIGINAL_SHA=$(sha256sum "${BACKUP_FILE}" | cut -d' ' -f1)
            DECRYPTED_SHA=$(sha256sum "${TEST_FILE}" | cut -d' ' -f1)

            if [ "${ORIGINAL_SHA}" == "${DECRYPTED_SHA}" ]; then
                echo -e "${GREEN}✓ Decryption test passed - files match${NC}"
            else
                echo -e "${RED}✗ Warning: Decrypted file doesn't match original${NC}"
            fi

            rm -f "${TEST_FILE}"
        fi
    fi

    # Ask to delete original
    echo ""
    read -p "Delete original unencrypted backup? (y/n): " delete_original
    if [[ "${delete_original}" == "y" ]]; then
        echo -e "${YELLOW}Securely deleting original...${NC}"
        shred -u "${BACKUP_FILE}" 2>/dev/null || rm -f "${BACKUP_FILE}"
        echo -e "${GREEN}✓ Original backup deleted${NC}"
    else
        echo -e "${YELLOW}⚠ Original backup retained${NC}"
        echo "Remember to securely delete it later!"
    fi

    echo ""
    echo -e "${BLUE}=================================${NC}"
    echo -e "${BLUE}  Encryption Complete${NC}"
    echo -e "${BLUE}=================================${NC}"
    echo ""
    echo "Files created:"
    echo "  ${ENCRYPTED_FILE}"
    echo "  ${ENCRYPTED_FILE}.sha256"
    echo ""
    echo "To decrypt later:"
    if [ "${SYMMETRIC:-false}" == "true" ]; then
        echo "  gpg --decrypt --output backup.tar.gz ${ENCRYPTED_FILE}"
    else
        echo "  gpg --decrypt --output backup.tar.gz ${ENCRYPTED_FILE}"
    fi
    echo ""
else
    echo -e "${RED}✗ Encryption failed${NC}"
    exit 1
fi
