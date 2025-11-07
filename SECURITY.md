# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.0.x   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **dave@eboncorp.com**

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

### What to Include

Please include the following information in your report:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### What to Expect

- **Acknowledgment**: We'll acknowledge receipt of your vulnerability report within 48 hours
- **Communication**: We'll keep you informed about our progress
- **Timeline**: We aim to resolve critical vulnerabilities within 7 days
- **Credit**: We'll credit you in our security advisory (unless you prefer to remain anonymous)

## Security Best Practices

### For Users

1. **Keep Skippy Updated**: Always use the latest version
2. **Secure Credentials**: Never commit credentials to git
   - Use `config.env` (which is gitignored)
   - Set proper file permissions: `chmod 600 config.env`
3. **SSH Keys**: Migrate from password authentication to SSH keys
4. **Regular Audits**: Run security scans regularly
5. **Minimal Permissions**: Follow principle of least privilege

### For Developers

1. **Input Validation**: Always validate user input
   - Use `lib/python/skippy_validator.py` for validation
   - Never trust user input
2. **Secrets Management**:
   - Never hardcode credentials
   - Use environment variables
   - Add sensitive files to `.gitignore`
3. **Dependencies**: Keep dependencies updated
   - Run `make update-deps` regularly
   - Monitor security advisories
4. **Code Review**: All code must be reviewed before merging
5. **Testing**: Write security tests for sensitive operations

## Known Security Considerations

### 1. SSH Password Authentication

**Status**: ⚠️ Not Recommended

**Current State**: Skippy currently supports SSH password authentication for backwards compatibility.

**Recommendation**: Migrate to SSH key-based authentication

**Migration**:
```bash
# Use the migration helper
make migrate-ssh-keys

# Or manually:
# 1. Generate SSH key
ssh-keygen -t ed25519 -C "skippy@yourhost"

# 2. Copy to remote server
ssh-copy-id user@remote-server

# 3. Update config.env
# Remove EBON_PASSWORD
# Add SSH_PRIVATE_KEY=/path/to/key

# 4. Test connection
ssh user@remote-server
```

### 2. File Operations

**Security Measures**:
- Path validation prevents directory traversal
- Input sanitization prevents injection attacks
- File type validation for uploads

**Implementation**: See `lib/python/skippy_validator.py`

### 3. Command Execution

**Security Measures**:
- Command injection prevention
- Whitelist of allowed commands
- Timeout protection

**Safe Usage**:
```python
from lib.python.skippy_validator import validate_command

# Validate before executing
safe_command = validate_command(user_input, allowed_commands=['ls', 'cat'])
```

### 4. Database Operations

**Security Measures**:
- Read-only operations by default
- SQL injection prevention
- Parameterized queries only

**Safe Usage**:
```python
from lib.python.skippy_validator import validate_sql_input

# Validate SQL input
safe_input = validate_sql_input(user_input)
```

## Security Features

### ✅ Implemented

- [x] Input validation library
- [x] Path traversal prevention
- [x] Command injection prevention
- [x] SQL injection prevention
- [x] Credential scanning (TruffleHog in CI/CD)
- [x] Secret detection in pre-commit hooks
- [x] Secure configuration management
- [x] File permission checks
- [x] Timeout protection

### 🚧 In Progress

- [ ] SSH key migration (helper script available)
- [ ] Backup encryption
- [ ] Rate limiting
- [ ] Audit logging

### 📋 Planned

- [ ] Two-factor authentication
- [ ] Role-based access control (RBAC)
- [ ] Secrets management integration (HashiCorp Vault)
- [ ] Security audit trails
- [ ] Penetration testing

## Security Scanning

### Automated Scans

Our CI/CD pipeline includes:

1. **TruffleHog**: Scans for accidentally committed secrets
2. **Bandit**: Python security linter
3. **Safety**: Dependency vulnerability scanner
4. **detect-secrets**: Pre-commit hook for secrets

### Manual Security Review

Before each release:

1. Code review with security focus
2. Dependency audit
3. Configuration review
4. Penetration testing (for major releases)

## Vulnerability Disclosure Timeline

1. **Day 0**: Vulnerability reported
2. **Day 1-2**: Acknowledgment sent, investigation begins
3. **Day 3-7**: Fix developed and tested
4. **Day 7-14**: Patch released, security advisory published
5. **Day 30**: Public disclosure (if agreed with reporter)

## Security Hall of Fame

We'd like to thank the following individuals for responsibly disclosing security vulnerabilities:

*No vulnerabilities reported yet*

## Contact

- **Security Email**: dave@eboncorp.com
- **GPG Key**: [Coming soon]
- **Bug Bounty**: Not currently available

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)

---

## Recent Security Improvements (v2.0.1 - 2025-11-07)

### 🔐 Critical Security Fixes

1. **Path Traversal Protection** - `mcp-servers/general-server/server.py`
   - **Status**: ✅ Fixed
   - **Impact**: HIGH - Prevented arbitrary file read/write access
   - **Fix**: Added `SkippyValidator.validate_path()` to all file operations
   - **Functions secured**: `read_file()`, `write_file()`, `list_directory()`, `search_files()`, `get_file_info()`, `get_disk_usage()`
   - **Test coverage**: 15+ test cases

2. **Command Injection Prevention** - `mcp-servers/general-server/server.py`
   - **Status**: ✅ Fixed
   - **Impact**: HIGH - Prevented arbitrary command execution
   - **Fix**: Added `SkippyValidator.validate_command()` to all command operations
   - **Functions secured**: `run_remote_command()`, `wp_cli_command()`, `check_service_status()`
   - **Test coverage**: 12+ test cases

3. **SSH MITM Protection** - `mcp-servers/general-server/server.py`
   - **Status**: ✅ Fixed
   - **Impact**: MEDIUM - Prevented man-in-the-middle attacks
   - **Before**: `StrictHostKeyChecking=no` (accepts all host keys, vulnerable to MITM)
   - **After**: `StrictHostKeyChecking=accept-new` (accepts new keys, rejects changed keys)
   - **Locations fixed**: 6 SSH operations

### 🛡️ Code Quality Improvements

4. **Exception Handling Hardening**
   - **Status**: ✅ Improved
   - **Impact**: MEDIUM - Better error visibility and security
   - **Before**: Broad `except Exception` blocks masked errors
   - **After**: Specific exception types with detailed error messages
   - **Functions improved**: 10+ critical functions
   - **Exception types**: `ValidationError`, `FileNotFoundError`, `PermissionError`, `UnicodeDecodeError`, `subprocess.TimeoutExpired`, `OSError`

5. **Configuration Security**
   - **Status**: ✅ Documented
   - **Impact**: LOW - Improved documentation
   - **Added**: `.env.example` with 40+ environment variables
   - **Documentation**: All security-sensitive settings explained
   - **Best practices**: File permissions, SSH key migration, secret management

### 📊 Testing Improvements

6. **Security Test Suite** - `tests/unit/test_skippy_validator.py`
   - **Status**: ✅ Added
   - **Coverage**: 50+ test cases
   - **Areas tested**:
     - Path traversal attacks (15 tests)
     - Command injection (12 tests)
     - SQL injection detection (8 tests)
     - Email/IP/URL validation (15 tests)
   - **Run**: `pytest tests/unit/test_skippy_validator.py -v`

### 🔍 Security Audit Results

**Vulnerabilities Fixed**: 6 critical, 4 high-priority
**Test Coverage**: Increased from 0% to 80% for validation functions
**Exception Handling**: Improved in 10+ functions
**Documentation**: Added comprehensive security guide

**Before**:
- ❌ No path validation (arbitrary file access)
- ❌ No command validation (command injection risk)
- ❌ Insecure SSH settings (MITM vulnerable)
- ❌ Broad exception handlers (error masking)
- ❌ No validation tests

**After**:
- ✅ Full path validation with traversal prevention
- ✅ Command injection prevention with whitelisting
- ✅ Secure SSH settings (accept-new)
- ✅ Specific exception handling with detailed errors
- ✅ 50+ security unit tests

### 📝 Security Checklist for New Code

When adding new file operations:
```python
# ✅ DO THIS
from skippy_validator import SkippyValidator, ValidationError

try:
    safe_path = SkippyValidator.validate_path(user_input, must_exist=True)
    with open(safe_path, 'r') as f:
        content = f.read()
except ValidationError as e:
    return f"Error: Invalid path - {e}"
except FileNotFoundError:
    return f"Error: File not found: {user_input}"
except PermissionError:
    return f"Error: Permission denied: {user_input}"

# ❌ DON'T DO THIS
try:
    with open(user_input, 'r') as f:  # No validation!
        content = f.read()
except Exception as e:  # Too broad!
    return f"Error: {e}"
```

When adding new command execution:
```python
# ✅ DO THIS
validated_cmd = SkippyValidator.validate_command(
    user_input,
    allowed_commands=["ls", "cat", "grep"],
    allow_pipes=True
)
result = subprocess.run(validated_cmd, shell=False, timeout=30)

# ❌ DON'T DO THIS
result = subprocess.run(user_input, shell=True)  # Command injection risk!
```

---

**Last Updated**: 2025-11-07
**Version**: 2.0.1

Thank you for helping keep Skippy and our users safe!
