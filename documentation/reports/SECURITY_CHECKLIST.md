# Security Development Checklist
**Skippy System Manager - Secure Coding Guidelines**
**Version**: 2.0
**Updated**: 2025-11-12

---

## 📋 Pre-Development Checklist

Before writing any new code that handles user input or executes commands:

### Input Validation
- [ ] Identify all user input points
- [ ] Determine validation type needed (command, path, URL, SQL, etc.)
- [ ] Import appropriate validators from `skippy_validator`
- [ ] Plan fallback validation if skippy libs unavailable

### Security Assessment
- [ ] Review for potential command injection
- [ ] Review for potential path traversal
- [ ] Review for potential SSRF (if HTTP)
- [ ] Review for potential SQL injection (if database)
- [ ] Review for potential XSS (if web interface)

---

## 🔒 Validation Implementation Checklist

### Command Execution

When executing commands with subprocess:

```python
from skippy_validator import validate_command, ValidationError

# ✅ DO THIS:
ALLOWED_COMMANDS = ['ls', 'pwd', 'cat', 'grep']  # Whitelist
try:
    safe_command = validate_command(
        user_input,
        allowed_commands=ALLOWED_COMMANDS,
        allow_pipes=False,  # Usually False for security
        allow_redirects=False  # Usually False for security
    )
    logger.info(f"Executing validated command: {safe_command}")
    result = subprocess.run(safe_command.split(), ...)
except ValidationError as e:
    logger.warning(f"Command validation failed: {e}")
    return f"Security validation failed: {str(e)}"

# ❌ NEVER DO THIS:
subprocess.run(user_input, shell=True, ...)  # VULNERABLE!
```

**Checklist**:
- [ ] Command whitelist defined
- [ ] validate_command() used
- [ ] ValidationError handled
- [ ] Audit logging added
- [ ] Fallback validation for missing libs
- [ ] shell=True avoided (or input fully validated)

---

### File Operations

When reading/writing files:

```python
from skippy_validator import validate_path, ValidationError

# ✅ DO THIS:
try:
    safe_path = validate_path(
        user_path,
        must_exist=True,  # For reads
        allow_create=True,  # For writes
        base_dir="/safe/directory"  # Optional restriction
    )
    logger.info(f"Reading file: {safe_path}")
    with open(safe_path, 'r') as f:
        content = f.read()
except ValidationError as e:
    logger.warning(f"Path validation failed: {e}")
    return f"Security validation failed: {str(e)}"

# ❌ NEVER DO THIS:
with open(user_path, 'r') as f:  # VULNERABLE to path traversal!
    content = f.read()
```

**Checklist**:
- [ ] validate_path() used
- [ ] Path existence checked appropriately
- [ ] Base directory restriction considered
- [ ] ValidationError handled
- [ ] Audit logging added
- [ ] Fallback validation for missing libs

---

### HTTP Requests

When making HTTP requests:

```python
from skippy_validator import validate_url, ValidationError

# ✅ DO THIS:
try:
    safe_url = validate_url(
        user_url,
        allowed_schemes=['http', 'https']
    )
    logger.info(f"Making HTTP request to: {safe_url[:100]}")
    response = httpx.get(safe_url, timeout=30)
except ValidationError as e:
    logger.warning(f"URL validation failed: {e}")
    return f"Security validation failed: {str(e)}"

# ❌ NEVER DO THIS:
response = httpx.get(user_url)  # VULNERABLE to SSRF!
```

**Checklist**:
- [ ] validate_url() used
- [ ] Protocol whitelist defined
- [ ] ValidationError handled
- [ ] Audit logging added
- [ ] Timeout configured
- [ ] Response size limited

---

### Database Queries

When querying databases:

```python
from skippy_validator import validate_sql_input, ValidationError

# ✅ DO THIS (Parameterized):
safe_username = validate_sql_input(user_input)
cursor.execute(
    "SELECT * FROM users WHERE username = ?",
    (safe_username,)  # Parameterized query
)

# ✅ ALSO GOOD (Use WP-CLI):
wp_cli_command(f"user get {user_id}")  # WP-CLI handles parameterization

# ❌ NEVER DO THIS:
cursor.execute(f"SELECT * FROM users WHERE username = '{user_input}'")  # SQL INJECTION!
```

**Checklist**:
- [ ] Parameterized queries used (preferred)
- [ ] validate_sql_input() used for input
- [ ] No string concatenation in queries
- [ ] ORM or WP-CLI used when possible
- [ ] ValidationError handled
- [ ] Audit logging added

---

## 🧪 Testing Checklist

### Security Tests Required

For each new feature with user input:

```python
# tests/security/test_my_feature.py

def test_command_injection_blocked():
    """Test that command injection is blocked."""
    with pytest.raises(ValidationError):
        my_function("ls; rm -rf /")

def test_path_traversal_blocked():
    """Test that path traversal is blocked."""
    with pytest.raises(ValidationError):
        my_function("../../../etc/passwd")

def test_safe_input_allowed():
    """Test that safe input works."""
    result = my_function("safe_input")
    assert result is not None
```

**Checklist**:
- [ ] Test malicious command injection
- [ ] Test path traversal attempts
- [ ] Test URL injection (if applicable)
- [ ] Test SQL injection (if applicable)
- [ ] Test safe input allowed
- [ ] Test edge cases (empty, whitespace, special chars)
- [ ] Mark tests with `@pytest.mark.security`

---

## 📝 Documentation Checklist

### Code Documentation

- [ ] Function docstring includes "SECURITY:" section
- [ ] Security features listed in docstring
- [ ] Validation approach documented
- [ ] Examples of blocked attacks provided

### Example Docstring:

```python
def my_secure_function(user_input: str) -> str:
    """Process user input with security validation.

    SECURITY: Input is validated to prevent command injection attacks.
    Only whitelisted commands are allowed.

    Args:
        user_input: User-provided command (will be validated)

    Returns:
        Command output or error message

    Security Features:
        - Command whitelist enforcement
        - Dangerous character blocking
        - Audit logging
        - Timeout protection

    Example:
        >>> my_secure_function("ls -la")  # Safe
        'file1\nfile2\n'

        >>> my_secure_function("ls; rm -rf /")  # Blocked
        'Security validation failed: Command contains dangerous character: ;'
    """
```

---

## 🔍 Code Review Checklist

### Reviewer Checklist

When reviewing security-sensitive code:

#### Input Validation
- [ ] All user input validated before use
- [ ] Appropriate validator used (command/path/URL/SQL)
- [ ] ValidationError properly handled
- [ ] Fallback validation present if needed

#### Command Execution
- [ ] Command whitelist defined and enforced
- [ ] No shell=True without validation
- [ ] No string concatenation for commands
- [ ] Timeout configured

#### File Operations
- [ ] No path traversal vulnerabilities
- [ ] Base directory restriction used if needed
- [ ] File existence checked appropriately
- [ ] Dangerous paths blocked (e.g., /etc/passwd)

#### HTTP Requests
- [ ] URLs validated before requests
- [ ] Protocol whitelist enforced
- [ ] SSRF risks mitigated
- [ ] Timeout configured
- [ ] Response size limited

#### Database Queries
- [ ] Parameterized queries used
- [ ] No string concatenation
- [ ] Input validated before queries
- [ ] ORM/WP-CLI preferred

#### Audit Logging
- [ ] Security-sensitive operations logged
- [ ] Validation failures logged
- [ ] Include relevant context (sanitized)
- [ ] Appropriate log level used

#### Testing
- [ ] Security tests present
- [ ] Malicious input tested
- [ ] Safe input tested
- [ ] Edge cases covered

---

## 🚀 Pre-Commit Checklist

Before committing code:

### Automated Checks
- [ ] Run pre-commit hooks: `pre-commit run --all-files`
- [ ] Run security tests: `pytest tests/security/ -v -m security`
- [ ] Run Bandit scan: `bandit -r mcp-servers/ lib/python/ -ll`
- [ ] Check for secrets: `detect-secrets scan`

### Manual Checks
- [ ] Review diff for hardcoded credentials
- [ ] Review diff for debug print statements
- [ ] Review diff for commented-out security code
- [ ] Verify no sensitive data in logs

---

## 🎯 Deployment Checklist

Before deploying to production:

### Pre-Deployment
- [ ] All security tests passing
- [ ] Bandit scan passing (or issues justified)
- [ ] No secrets in code/config
- [ ] Environment variables configured
- [ ] Audit logging configured

### Post-Deployment
- [ ] Monitor audit logs for validation failures
- [ ] Monitor error rates
- [ ] Monitor performance impact
- [ ] Verify security features active
- [ ] Check for unexpected errors

---

## 📚 Resources

### Validation Library
- **Location**: `lib/python/skippy_validator.py`
- **Documentation**: `SECURITY.md`
- **Tests**: `tests/unit/test_skippy_validator.py`

### Security Tests
- **Location**: `tests/security/`
- **Run**: `pytest tests/security/ -v -m security`

### Security Documentation
- **Policy**: `SECURITY.md`
- **Phase 1 Summary**: `PHASE1_IMPLEMENTATION_SUMMARY.md`
- **Phase 2 Summary**: `PHASE2_IMPLEMENTATION_SUMMARY.md`

### CI/CD
- **Pipeline**: `.github/workflows/ci.yml`
- **Pre-commit**: `.pre-commit-config.yaml`

---

## ⚠️ Common Vulnerabilities to Avoid

### 1. Command Injection
```python
# ❌ BAD
os.system(user_input)
subprocess.run(user_input, shell=True)
subprocess.call(f"command {user_input}", shell=True)

# ✅ GOOD
safe = validate_command(user_input, allowed_commands=['ls', 'pwd'])
subprocess.run(safe.split(), shell=False)
```

### 2. Path Traversal
```python
# ❌ BAD
open(user_path, 'r')
Path(user_path).read_text()

# ✅ GOOD
safe_path = validate_path(user_path, base_dir="/safe/dir")
open(safe_path, 'r')
```

### 3. SSRF
```python
# ❌ BAD
httpx.get(user_url)
requests.get(user_url)

# ✅ GOOD
safe_url = validate_url(user_url, allowed_schemes=['http', 'https'])
httpx.get(safe_url, timeout=30)
```

### 4. SQL Injection
```python
# ❌ BAD
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# ✅ GOOD
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

---

## 📞 Getting Help

If unsure about security:

1. **Review existing code** - See how similar functions handle security
2. **Check SECURITY.md** - Comprehensive security documentation
3. **Run security tests** - See what attacks are blocked
4. **Ask for review** - Security review recommended for sensitive code

---

**Remember**: Security is not optional. Every input is potentially malicious until proven safe through validation.

*Last Updated: 2025-11-12 | Version 2.0*
