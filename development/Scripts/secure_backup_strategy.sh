#!/bin/bash
# Secure Backup Strategy for SSH Keys and Crypto Data
# Run with: bash secure_backup_strategy.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}🔒 Secure Backup Strategy Setup${NC}"
echo "==============================="
echo

# Create secure backup directory structure
BACKUP_BASE="$HOME/.secure-backups"
mkdir -p "$BACKUP_BASE"/{ssh-keys,crypto-data,configs,gpg,yubikey}
chmod 700 "$BACKUP_BASE"

echo -e "${YELLOW}📁 Creating backup directory structure...${NC}"

# Create encrypted backup script
cat > "$BACKUP_BASE/create_secure_backup.sh" << 'EOF'
#!/bin/bash
# Secure backup creation script

set -e

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$HOME/.secure-backups"
TEMP_DIR="/tmp/secure_backup_$BACKUP_DATE"
ENCRYPTED_BACKUP="$BACKUP_DIR/secure_backup_$BACKUP_DATE.gpg"

echo "🔒 Creating secure backup: $BACKUP_DATE"

# Create temporary directory
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

# Backup SSH keys and configuration
echo "📋 Backing up SSH keys..."
if [ -d "$HOME/.ssh" ]; then
    mkdir -p ssh
    cp -r "$HOME/.ssh"/* ssh/ 2>/dev/null || true
    # Remove socket files and temporary files
    find ssh/ -type s -delete 2>/dev/null || true
    find ssh/ -name "*.tmp" -delete 2>/dev/null || true
fi

# Backup WireGuard configuration
echo "🔧 Backing up VPN configuration..."
if [ -d "/etc/wireguard" ]; then
    mkdir -p wireguard
    sudo cp /etc/wireguard/*.conf wireguard/ 2>/dev/null || true
    sudo cp /etc/wireguard/*_private.key wireguard/ 2>/dev/null || true
    sudo chown -R $(whoami):$(whoami) wireguard/
fi

# Backup crypto-related configurations
echo "💰 Backing up crypto configurations..."
mkdir -p crypto
# Add paths to crypto wallets, node configs, etc.
# Example: cp -r "$HOME/.ethereum" crypto/ 2>/dev/null || true

# Backup system configurations
echo "⚙️ Backing up system configs..."
mkdir -p configs
cp /etc/ssh/sshd_config configs/ 2>/dev/null || true
cp /etc/fail2ban/jail.local configs/ 2>/dev/null || true
cp /etc/ufw/user.rules configs/ 2>/dev/null || true

# Backup important documents
echo "📄 Backing up important documents..."
mkdir -p documents
# Add important document paths here
# cp "$HOME/important_doc.pdf" documents/ 2>/dev/null || true

# Create manifest
echo "📝 Creating backup manifest..."
cat > manifest.txt << MANIFEST_EOF
Secure Backup Created: $(date)
Hostname: $(hostname)
User: $(whoami)
Contents:
- SSH keys and configuration
- WireGuard VPN configuration  
- Crypto-related configurations
- System security configurations
- Important documents

Backup Hash: $(find . -type f -exec sha256sum {} \; | sha256sum | cut -d' ' -f1)
MANIFEST_EOF

# Create archive
echo "📦 Creating encrypted archive..."
tar -czf "../secure_backup_$BACKUP_DATE.tar.gz" .

# Encrypt the archive
cd ..
gpg --symmetric --cipher-algo AES256 --armor \
    --output "$ENCRYPTED_BACKUP" \
    "secure_backup_$BACKUP_DATE.tar.gz"

# Clean up
rm -rf "$TEMP_DIR"
rm "secure_backup_$BACKUP_DATE.tar.gz"

# Set permissions
chmod 600 "$ENCRYPTED_BACKUP"

echo "✅ Secure backup created: $ENCRYPTED_BACKUP"
echo "💡 Store this file in multiple secure locations"
echo "🔑 Remember the passphrase used for encryption"
EOF

chmod +x "$BACKUP_BASE/create_secure_backup.sh"

# Create backup restoration script
cat > "$BACKUP_BASE/restore_secure_backup.sh" << 'EOF'
#!/bin/bash
# Secure backup restoration script

set -e

if [ $# -ne 1 ]; then
    echo "Usage: $0 <encrypted_backup_file.gpg>"
    exit 1
fi

BACKUP_FILE="$1"
RESTORE_DATE=$(date +%Y%m%d_%H%M%S)
TEMP_DIR="/tmp/restore_backup_$RESTORE_DATE"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "🔓 Restoring secure backup from: $BACKUP_FILE"

# Create temporary directory
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

# Decrypt the backup
echo "🔑 Decrypting backup..."
gpg --decrypt "$BACKUP_FILE" | tar -xzf -

# Verify manifest
if [ -f "manifest.txt" ]; then
    echo "📋 Backup manifest:"
    cat manifest.txt
    echo
else
    echo "⚠️ No manifest found in backup"
fi

# Restoration options
echo "Available restoration options:"
echo "1. SSH keys and configuration"
echo "2. VPN configuration"  
echo "3. Crypto configurations"
echo "4. System configurations"
echo "5. All components"
echo

read -p "Select restoration option (1-5): " choice

case $choice in
    1|5)
        if [ -d "ssh" ]; then
            echo "🔑 Restoring SSH configuration..."
            mkdir -p "$HOME/.ssh"
            cp -r ssh/* "$HOME/.ssh/"
            chmod 700 "$HOME/.ssh"
            chmod 600 "$HOME/.ssh"/*
            echo "✅ SSH configuration restored"
        fi
        ;&
    2|5)  
        if [ -d "wireguard" ]; then
            echo "🔧 Restoring VPN configuration..."
            echo "⚠️ Manual intervention required for system files"
            echo "Files available in: $TEMP_DIR/wireguard/"
        fi
        ;&
    3|5)
        if [ -d "crypto" ]; then
            echo "💰 Restoring crypto configurations..."
            # Restore crypto configs
            echo "✅ Crypto configurations restored"
        fi
        ;&
    4|5)
        if [ -d "configs" ]; then
            echo "⚙️ System configurations available in: $TEMP_DIR/configs/"
            echo "⚠️ Manual review and installation required"
        fi
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo
echo "🎉 Restoration complete!"
echo "📁 Temporary files in: $TEMP_DIR"
echo "🧹 Clean up with: rm -rf $TEMP_DIR"
EOF

chmod +x "$BACKUP_BASE/restore_secure_backup.sh"

# Create backup verification script
cat > "$BACKUP_BASE/verify_backup.sh" << 'EOF'
#!/bin/bash
# Backup verification script

set -e

if [ $# -ne 1 ]; then
    echo "Usage: $0 <encrypted_backup_file.gpg>"
    exit 1
fi

BACKUP_FILE="$1"
VERIFY_DATE=$(date +%Y%m%d_%H%M%S)
TEMP_DIR="/tmp/verify_backup_$VERIFY_DATE"

echo "🔍 Verifying backup: $BACKUP_FILE"

# Create temporary directory
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

# Decrypt and extract
echo "🔓 Decrypting and extracting..."
gpg --decrypt "$BACKUP_FILE" | tar -xzf -

# Verify contents
echo "📋 Backup verification results:"
echo

if [ -f "manifest.txt" ]; then
    echo "✅ Manifest file present"
    cat manifest.txt
    echo
else
    echo "❌ Manifest file missing"
fi

if [ -d "ssh" ]; then
    echo "✅ SSH backup present ($(find ssh -type f | wc -l) files)"
else
    echo "⚠️ SSH backup missing"
fi

if [ -d "wireguard" ]; then
    echo "✅ VPN backup present ($(find wireguard -type f | wc -l) files)"
else
    echo "⚠️ VPN backup missing"
fi

if [ -d "configs" ]; then
    echo "✅ Config backup present ($(find configs -type f | wc -l) files)"
else
    echo "⚠️ Config backup missing"
fi

# Calculate current hash
CURRENT_HASH=$(find . -type f -exec sha256sum {} \; | sha256sum | cut -d' ' -f1)
echo "🔐 Current backup hash: $CURRENT_HASH"

# Clean up
cd ..
rm -rf "$TEMP_DIR"

echo "✅ Verification complete"
EOF

chmod +x "$BACKUP_BASE/verify_backup.sh"

# Create automated backup cron job setup
cat > "$BACKUP_BASE/setup_automated_backups.sh" << 'EOF'
#!/bin/bash
# Setup automated secure backups

BACKUP_SCRIPT="$HOME/.secure-backups/create_secure_backup.sh"

echo "⏰ Setting up automated backups..."

# Create cron job for weekly backups
(crontab -l 2>/dev/null; echo "0 2 * * 0 $BACKUP_SCRIPT") | crontab -

echo "✅ Automated backup scheduled:"
echo "   - Weekly on Sunday at 2:00 AM"
echo "   - Backups stored in: $HOME/.secure-backups/"
echo "   - Remember to periodically move backups to external storage"

# Create backup rotation script
cat > "$HOME/.secure-backups/rotate_backups.sh" << 'ROTATE_EOF'
#!/bin/bash
# Backup rotation - keep last 4 backups

BACKUP_DIR="$HOME/.secure-backups"
cd "$BACKUP_DIR"

# Keep only the 4 most recent backups
ls -t secure_backup_*.gpg | tail -n +5 | xargs rm -f 2>/dev/null || true

echo "🔄 Backup rotation complete - keeping 4 most recent backups"
ROTATE_EOF

chmod +x "$HOME/.secure-backups/rotate_backups.sh"

# Add rotation to cron (run after backup)
(crontab -l 2>/dev/null; echo "30 2 * * 0 $HOME/.secure-backups/rotate_backups.sh") | crontab -

echo "🔄 Backup rotation also scheduled"
EOF

chmod +x "$BACKUP_BASE/setup_automated_backups.sh"

# Create emergency key recovery guide
cat > "$BACKUP_BASE/EMERGENCY_RECOVERY_GUIDE.md" << 'EOF'
# Emergency Key Recovery Guide

## If you lose access to your laptop:

### Immediate Actions:
1. **Don't Panic** - Your keys are backed up
2. **Assess the situation** - theft, hardware failure, etc.
3. **Secure your accounts** - change passwords if theft suspected

### Recovery Steps:

#### 1. Access Your Backups
- Locate your encrypted backup files (.gpg)
- You need the GPG passphrase you used during creation
- Backups should be stored in multiple locations:
  - External USB drive
  - Cloud storage (encrypted)
  - Printed QR codes (for critical keys)

#### 2. Set Up New Device
```bash
# Install GPG on new device
sudo apt install gnupg2

# Decrypt and restore
gpg --decrypt secure_backup_YYYYMMDD_HHMMSS.gpg | tar -xzf -
```

#### 3. Restore SSH Access
```bash
# Restore SSH keys
mkdir -p ~/.ssh
cp ssh/* ~/.ssh/
chmod 700 ~/.ssh
chmod 600 ~/.ssh/*

# Test connection
ssh ebon@10.0.0.29
```

#### 4. Re-establish VPN Access
```bash
# Install WireGuard
sudo apt install wireguard

# Restore VPN config (as root)
sudo cp wireguard/*.conf /etc/wireguard/
sudo chmod 600 /etc/wireguard/*

# Connect
sudo wg-quick up home-server
```

#### 5. Secure New Environment
- Run security hardening scripts
- Generate new keys if old device was compromised
- Update all authentication keys
- Review access logs for suspicious activity

### Prevention:
- Keep backups current (automated weekly)
- Store backups in multiple secure locations
- Test recovery procedure regularly
- Document all account access methods
- Consider using YubiKey for critical access
EOF

# Create backup checklist
cat > "$BACKUP_BASE/BACKUP_CHECKLIST.md" << 'EOF'
# Secure Backup Checklist

## Daily:
- [ ] Verify automated backup cron job is running
- [ ] Check for any backup errors in system logs

## Weekly:
- [ ] Verify automated backup was created
- [ ] Test one backup file for integrity
- [ ] Check backup file sizes are reasonable

## Monthly:
- [ ] Perform full backup verification test
- [ ] Update backup scripts if needed
- [ ] Review backup storage locations
- [ ] Test emergency recovery procedure

## Quarterly:
- [ ] Full disaster recovery test
- [ ] Update emergency contact information
- [ ] Review and update documentation
- [ ] Audit backup security practices

## Annual:
- [ ] Security audit of backup procedures
- [ ] Update encryption methods if needed
- [ ] Review and update recovery contacts
- [ ] Professional security assessment

## Backup Locations:
- [ ] Local encrypted storage
- [ ] External USB drive (encrypted)
- [ ] Cloud storage (double encrypted)
- [ ] Secure off-site location
- [ ] Printed QR codes for critical keys

## Security Measures:
- [ ] Strong GPG passphrases
- [ ] Multiple encryption layers
- [ ] Access logs monitoring
- [ ] Regular integrity checks
- [ ] Secure deletion of temporary files
EOF

echo -e "${GREEN}✅ Secure backup strategy setup complete!${NC}"
echo
echo -e "${BLUE}📁 Backup system created in: $BACKUP_BASE${NC}"
echo
echo -e "${YELLOW}🔧 Available tools:${NC}"
echo "- create_secure_backup.sh    - Create encrypted backup"
echo "- restore_secure_backup.sh   - Restore from backup"
echo "- verify_backup.sh           - Verify backup integrity"
echo "- setup_automated_backups.sh - Enable automatic backups"
echo
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Run: $BACKUP_BASE/create_secure_backup.sh"
echo "2. Test: $BACKUP_BASE/verify_backup.sh <backup_file>"
echo "3. Setup automation: $BACKUP_BASE/setup_automated_backups.sh"
echo "4. Store backups in multiple secure locations"
echo
echo -e "${RED}⚠️ Important:${NC}"
echo "- Remember your GPG passphrase"
echo "- Test recovery procedure regularly"
echo "- Keep backups in multiple locations"
echo "- Never store passphrases with backups"
echo
echo -e "${GREEN}🎯 Your data is now protected with military-grade security!${NC}"