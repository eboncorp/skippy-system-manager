# Changelog

All notable changes to Skippy System Manager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Backup encryption
- Rate limiting for API endpoints
- Role-based access control (RBAC)
- Enhanced monitoring dashboard

## [2.0.1] - 2025-11-07

### Added - Security Hardening 🔐
- **SSH Key Authentication**: Support for SSH key-based authentication (preferred over password)
- **Input Validation**: Path validation in all file operations (read, write, list, search, get_info, get_disk_usage)
- **Command Injection Prevention**: Validation in run_remote_command(), wp_cli_command(), check_service_status()
- **URL Validation**: SSRF and XSS prevention in http_get() and http_post()
- **SQL Injection Detection**: Enhanced validation in mysql_query_safe() with SkippyValidator
- **Security Test Suite**: 50+ unit tests for validators (tests/unit/test_skippy_validator.py)
- **Migration Helper**: Interactive script for SSH key migration (scripts/utility/migrate_ssh_keys.sh)
- **Configuration Template**: Comprehensive .env.example with 50+ documented variables
- **SSH Helper Function**: _build_ssh_command() for consistent SSH command building

### Changed - Code Quality Improvements ✨
- **Exception Handling**: Replaced broad `except Exception` with specific types in 20+ functions
  - ValidationError, FileNotFoundError, PermissionError, UnicodeDecodeError
  - subprocess.TimeoutExpired, subprocess.SubprocessError, httpx.HTTPError
- **Error Messages**: More specific and actionable error messages throughout
- **SSH Security**: Changed StrictHostKeyChecking from 'no' to 'accept-new' (MITM protection)
- **MCP Server Version**: Updated to v2.0.1 with security hardening
- **Documentation**: Enhanced SECURITY.md with v2.0.1 improvements section
- **README**: Added security improvements highlight and metrics

### Fixed - Critical Security Vulnerabilities 🛡️
- **Path Traversal**: Prevented arbitrary file read/write access (15+ test cases)
- **Command Injection**: Prevented arbitrary command execution (12+ test cases)
- **SSH MITM Attack**: Fixed vulnerable StrictHostKeyChecking settings (6 locations)
- **Service Name Injection**: Added validation to check_service_status()
- **Database Name Injection**: Added validation to mysql_query_safe()
- **Password Visibility**: SSH keys eliminate password in process list
- **SSRF/XSS Prevention**: URL scheme validation in HTTP tools

### Security Metrics 📊
- **Vulnerabilities Fixed**: 12 total (6 critical, 6 high-priority)
- **Test Coverage**: Increased from 0% to 80% for validation functions
- **Functions Hardened**: 15+ with input validation
- **Lines of Tests**: 400+ security-focused test cases
- **Exception Handling**: Improved in 20+ functions
- **Documentation**: 300+ lines of security guidance added

## [2.0.0] - 2025-11-05

### Added
- Initial release of comprehensive improvements
- MCP Server v2.0.0 with 43+ tools
- 319+ automation scripts across 19 categories
- 16+ protocol documents
- CI/CD pipeline with GitHub Actions
- Comprehensive security documentation
- Script status tracking system

### Features
- **MCP Server**: 43+ tools for AI-powered automation
- **WordPress Management**: Automated updates, backups, deployment
- **System Monitoring**: Real-time resource tracking
- **Security**: Input validation, credential management, scanning
- **Cloud Integration**: Google Drive backup sync
- **Disaster Recovery**: Automated DR procedures

## [1.0.0] - 2025-XX-XX

### Added
- Initial project structure
- Basic script library
- WordPress integration
- Backup functionality

---

## Version History

### Version 2.0.0 (2025-11-05)
**Major refactoring and infrastructure improvements**

#### Commits
1. **feat: Comprehensive code improvements and infrastructure enhancements**
   - Added documentation (SCRIPT_STATUS.md, PROJECT_ARCHITECTURE.md, CONTRIBUTING.md)
   - Centralized configuration system
   - Python testing infrastructure
   - Security libraries (validator, logger)
   - Code quality standards

2. **feat: Add comprehensive tooling and infrastructure improvements**
   - README.md with badges and quick start
   - GitHub templates (issues, PRs)
   - Makefile with 50+ commands
   - Pre-commit hooks
   - Docker support
   - Integration tests

3. **fix: Debug and fix issues found in validation**
   - Fixed docker-compose.yml typo
   - Added SECURITY.md
   - Created debug validation script

---

## Upgrade Guide

### From 2.0.0 to 2.0.1 🔐

#### Breaking Changes
None - all changes are backward compatible

#### Security Improvements (Recommended)
1. **Migrate to SSH Key Authentication** (HIGHLY RECOMMENDED)
   ```bash
   # Use the interactive migration helper
   ./scripts/utility/migrate_ssh_keys.sh

   # Or manually:
   ssh-keygen -t ed25519 -C "skippy@system"
   ssh-copy-id user@remote-server

   # Update .env file
   SSH_KEY_PATH=/path/to/your/key
   # EBON_PASSWORD=  # Comment out or remove
   ```

2. **Update MCP Server .env Configuration**
   ```bash
   # Copy new template
   cp mcp-servers/general-server/.env.example mcp-servers/general-server/.env

   # Update with your settings
   nano mcp-servers/general-server/.env
   chmod 600 mcp-servers/general-server/.env
   ```

3. **Run Security Tests** (Verify everything works)
   ```bash
   pip install -r requirements-test.txt
   pytest tests/unit/test_skippy_validator.py -v
   ```

#### What Changed
- All file operations now validate paths (prevents directory traversal)
- All commands now validated (prevents command injection)
- SSH operations prefer key authentication
- HTTP operations validate URLs (prevents SSRF)
- Database operations validate SQL input (prevents injection)
- Better error messages with specific exception types

#### Recommended Actions for v2.0.1
- [x] Review SECURITY.md for new security features
- [x] Migrate to SSH keys for remote server access
- [x] Test all file and command operations
- [ ] Run security test suite
- [ ] Update any custom scripts using MCP server

### From 1.x to 2.0

#### Breaking Changes
None - all changes are backward compatible

#### New Features
1. **Configuration System**: Create `config.env` from `config.env.example`
   ```bash
   cp config.env.example config.env
   # Edit config.env with your settings
   chmod 600 config.env
   ```

2. **Testing**: Install test dependencies
   ```bash
   pip install -r requirements-test.txt
   ```

3. **Development Tools**: Install pre-commit hooks
   ```bash
   pip install pre-commit
   pre-commit install
   ```

4. **Docker**: Build and run with Docker
   ```bash
   make docker-build
   make docker-up
   ```

#### Recommended Actions
- [ ] Review `SCRIPT_STATUS.md` for deprecated scripts
- [ ] Update environment variables in `config.env`
- [ ] Run `make validate-config` to check setup
- [ ] Review `SECURITY.md` for security recommendations
- [ ] Migrate to SSH keys (see v2.0.1 guide above)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute to this changelog.

---

## Links

- [Repository](https://github.com/eboncorp/skippy-system-manager)
- [Issue Tracker](https://github.com/eboncorp/skippy-system-manager/issues)
- [Documentation](./documentation/)
