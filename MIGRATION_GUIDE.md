# Migration Guide - v2.0.1

This guide helps you upgrade to Skippy System Manager v2.0.1 with enhanced security features.

## 🎯 Quick Start (5 minutes)

### For Users with Remote Server Access

**Recommended: Migrate to SSH Keys** (Most secure)

```bash
# 1. Run the interactive migration helper
./scripts/utility/migrate_ssh_keys.sh

# That's it! The script will:
# - Generate SSH keys (if needed)
# - Copy keys to remote server
# - Test connection
# - Update your .env configuration
# - Create backups automatically
```

### For Users Without Remote Server Access

**Update your MCP server configuration**

```bash
# 1. Update configuration template
cd mcp-servers/general-server
cp .env.example .env

# 2. Edit with your settings
nano .env

# 3. Secure the file
chmod 600 .env

# 4. Restart MCP server
```

## 📋 Detailed Migration Steps

### Step 1: Backup Current Configuration

```bash
# Backup your current .env file
cp mcp-servers/general-server/.env mcp-servers/general-server/.env.backup-$(date +%Y%m%d)

# Verify backup exists
ls -la mcp-servers/general-server/.env*
```

### Step 2: Choose Authentication Method

#### Option A: SSH Key Authentication (Recommended) 🏆

**Why SSH keys?**
- ✅ More secure than passwords
- ✅ Password not visible in process list
- ✅ No password in environment variables
- ✅ Industry standard for automation

**Migration script does everything:**
```bash
./scripts/utility/migrate_ssh_keys.sh
```

**Or manually:**
```bash
# Generate key
ssh-keygen -t ed25519 -C "skippy@system" -f ~/.ssh/skippy_ed25519

# Copy to remote server
ssh-copy-id -i ~/.ssh/skippy_ed25519.pub ebon@10.0.0.29

# Test connection
ssh -i ~/.ssh/skippy_ed25519 ebon@10.0.0.29 "echo Success"

# Update .env
echo "SSH_KEY_PATH=~/.ssh/skippy_ed25519" >> mcp-servers/general-server/.env
sed -i 's/^EBON_PASSWORD=/# EBON_PASSWORD=/' mcp-servers/general-server/.env
```

#### Option B: Keep Password Authentication

**If you must use passwords:**
```bash
# Just update to new .env.example format
cd mcp-servers/general-server
cp .env.example .env.new

# Copy your EBON_PASSWORD from old .env to new
# Then replace:
mv .env.new .env
chmod 600 .env
```

**⚠️ Security Warning**: Password authentication is less secure. Consider migrating to SSH keys when possible.

### Step 3: Run Security Tests

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run security test suite
pytest tests/unit/test_skippy_validator.py -v

# Expected: All tests should pass
# If any fail, check your configuration
```

### Step 4: Test Remote Operations

```bash
# Test SSH connection
ssh ebon@10.0.0.29 "hostname"

# Test MCP server (if running)
# The server should now use SSH keys automatically
```

### Step 5: Update Custom Scripts (if any)

If you have custom scripts that call the MCP server:

**Before (v2.0.0)**:
```python
# File paths were not validated
with open(user_input, 'r') as f:
    content = f.read()
```

**After (v2.0.1)**:
```python
from skippy_validator import SkippyValidator, ValidationError

# All file paths must be validated
try:
    safe_path = SkippyValidator.validate_path(user_input)
    with open(safe_path, 'r') as f:
        content = f.read()
except ValidationError as e:
    print(f"Invalid path: {e}")
```

## 🔍 Verification Checklist

After migration, verify:

- [ ] SSH key authentication works (if using keys)
- [ ] Remote commands execute successfully
- [ ] File operations work correctly
- [ ] No error messages in logs
- [ ] Security tests pass
- [ ] `.env` file has correct permissions (600)
- [ ] Backup of old configuration exists

## 🐛 Troubleshooting

### SSH Key Authentication Not Working

**Problem**: "Permission denied (publickey)"

**Solutions**:
```bash
# Check SSH key permissions
chmod 600 ~/.ssh/skippy_ed25519
chmod 644 ~/.ssh/skippy_ed25519.pub

# Check SSH key was copied to server
ssh ebon@10.0.0.29 "cat ~/.ssh/authorized_keys | grep skippy"

# Test SSH key manually
ssh -i ~/.ssh/skippy_ed25519 -v ebon@10.0.0.29
```

### MCP Server Not Finding .env File

**Problem**: "Configuration not found"

**Solutions**:
```bash
# Check .env file exists
ls -la mcp-servers/general-server/.env

# Check file permissions
chmod 600 mcp-servers/general-server/.env

# Check file location
pwd
# Should be in skippy-system-manager root
```

### Validation Errors on File Operations

**Problem**: "ValidationError: Path contains dangerous pattern"

**This is working correctly!** The new security prevents:
- Directory traversal: `../../../etc/passwd`
- Home directory: `~/malicious`
- Variable expansion: `/tmp/$USER/file`

**Solution**: Use absolute paths or relative paths within allowed directories.

### Import Error: No module named 'skippy_validator'

**Problem**: `ImportError: No module named 'skippy_validator'`

**Solutions**:
```bash
# Ensure lib/python is in your Python path
export PYTHONPATH="$PYTHONPATH:$(pwd)/lib/python"

# Or install in development mode
pip install -e .
```

## 📚 What Changed in v2.0.1

### Security Improvements
- ✅ Path traversal prevention in all file operations
- ✅ Command injection prevention in all command execution
- ✅ SSH key authentication support (preferred method)
- ✅ URL validation in HTTP operations (SSRF/XSS prevention)
- ✅ SQL injection detection in database operations
- ✅ SSH MITM protection (StrictHostKeyChecking=accept-new)

### Code Quality
- ✅ Specific exception handling (no more broad `except Exception`)
- ✅ Better error messages with context
- ✅ Input validation on all user inputs
- ✅ 50+ security unit tests

### New Features
- ✅ Interactive SSH key migration script
- ✅ Comprehensive `.env.example` template
- ✅ Security test suite
- ✅ Helper function for SSH command building

## 🔐 Security Best Practices

After migration, follow these best practices:

1. **File Permissions**
   ```bash
   chmod 600 mcp-servers/general-server/.env
   chmod 600 ~/.ssh/skippy_ed25519
   chmod 644 ~/.ssh/skippy_ed25519.pub
   chmod 700 ~/.ssh
   ```

2. **Regular Updates**
   ```bash
   # Check for updates monthly
   git fetch origin
   git log HEAD..origin/main --oneline
   ```

3. **Security Monitoring**
   ```bash
   # Check logs for validation errors
   grep "ValidationError" /var/log/skippy.log

   # Review failed authentication attempts
   grep "Permission denied" /var/log/skippy.log
   ```

4. **Test Regularly**
   ```bash
   # Run security tests weekly
   pytest tests/unit/test_skippy_validator.py -v
   ```

## 📞 Need Help?

- **Documentation**: [SECURITY.md](SECURITY.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Issues**: [GitHub Issues](https://github.com/eboncorp/skippy-system-manager/issues)
- **Email**: dave@eboncorp.com

## 🎉 Migration Complete!

Once all checks pass, you're running Skippy v2.0.1 with enhanced security!

**Next Steps**:
1. Review [SECURITY.md](SECURITY.md) for best practices
2. Set up automated testing in your workflow
3. Consider enabling additional security features
4. Share your feedback!

---

**Last Updated**: 2025-11-07
**Version**: 2.0.1
**Migration Support**: See CHANGELOG.md for upgrade details
