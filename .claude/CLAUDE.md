# Skippy System Manager - Claude Code Instructions

**Version:** 2.1.0
**Last Updated:** 2025-11-26
**Status:** Production Ready

---

## Project Overview

Skippy System Manager is a comprehensive automation and management suite for:
- Infrastructure automation and monitoring
- WordPress website management (rundaverun.org campaign site)
- System administration and backup operations
- Security auditing and compliance
- MCP server integration for Claude AI

### Key Statistics

| Category | Count |
|----------|-------|
| Scripts | 319+ (Python: 156, Bash: 163) |
| MCP Tools | 52+ across 6 categories |
| Slash Commands | 27 custom commands |
| Test Suites | Unit, Integration, Security, WordPress |
| CI/CD Jobs | 8 automated pipeline stages |

---

## Directory Structure

```
skippy-system-manager/
├── .claude/                    # Claude Code configuration
│   ├── commands/               # 27 slash commands
│   ├── hooks/                  # Pre/post execution hooks
│   ├── workflows/              # Documented workflows
│   ├── protocols/              # Standard procedures
│   └── settings.json           # Claude Code settings
├── scripts/                    # 319+ automation scripts
│   ├── automation/             # General automation (27 scripts)
│   ├── backup/                 # Backup operations (9 scripts)
│   ├── data_processing/        # Data tools
│   ├── deployment/             # Deployment automation
│   ├── gdrive/                 # Google Drive integration
│   ├── maintenance/            # System maintenance
│   ├── monitoring/             # System monitoring
│   ├── security/               # Security tools
│   ├── utility/                # General utilities
│   ├── wordpress/              # WordPress management
│   └── legacy_system_managers/ # Legacy scripts (maintenance mode)
├── bin/                        # CLI tools (PATH executable)
├── mcp-servers/                # MCP server implementations
│   ├── general-server/         # Main MCP server (52+ tools)
│   └── wordpress-validator/    # WordPress validation
├── tests/                      # Test framework
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   ├── security/               # Security tests
│   └── performance/            # Performance tests
├── documentation/              # Project documentation
│   ├── protocols/              # 16+ protocol documents
│   └── guides/                 # User guides
├── conversations/              # Session logs and transcripts
├── .github/workflows/          # CI/CD pipelines
└── lib/python/                 # Python library modules
```

---

## Critical Conventions

### File Naming Standards

**ALL files must follow these rules:**

```
Format: {purpose}_{specific_task}_v{version}.{ext}
```

| Rule | Correct | Wrong |
|------|---------|-------|
| Lowercase only | `my_script_v1.0.0.sh` | `My-Script.sh` |
| Underscores for spaces | `backup_wordpress_v1.0.0.sh` | `backup-wordpress.sh` |
| Semantic versioning | `tool_v1.2.3.py` | `tool.py` |

### Script Header Template

All scripts must include:

```bash
#!/bin/bash
# Script Name v1.0.0
# Brief description
#
# Usage:
#   script_name [options] arguments
#
# Dependencies:
#   - dependency1
#   - dependency2
#
# Created: YYYY-MM-DD
```

### Before Creating Any Script

**ALWAYS check if similar functionality exists:**

```bash
# Search by keyword
grep -r "keyword" scripts/

# Or use skippy-script (if available)
skippy-script search "backup"
```

---

## Development Workflow

### Git Branching

```
main
├── develop (integration)
├── feature/* (new features)
├── bugfix/* (bug fixes)
├── hotfix/* (urgent fixes)
└── claude/* (Claude Code sessions)
```

### Commit Message Convention

```
type: description

Types:
- feat:     New feature
- fix:      Bug fix
- docs:     Documentation
- test:     Add/update tests
- chore:    Maintenance
- refactor: Code restructuring
```

### Testing Requirements

1. **ShellCheck** for shell scripts
2. **Pylint/flake8** for Python
3. **pytest** for unit tests
4. **Pre-commit hooks** auto-validate

```bash
# Run tests
pytest tests/ -v

# Run specific test suite
pytest tests/unit/ -v
pytest tests/security/ -v -m security
```

---

## Available Slash Commands

### System & Health

| Command | Description |
|---------|-------------|
| `/mcp-status` | Check MCP server status |
| `/ebon-status` | Remote server health check |
| `/git-branches` | Manage git branches |
| `/system-cleanup` | Clean up temporary files |

### Content & WordPress

| Command | Description |
|---------|-------------|
| `/fact-check` | Validate campaign data against source of truth |
| `/content-approve` | Approve WordPress content updates |
| `/wp-deploy` | Deploy WordPress changes |
| `/validate-content` | Comprehensive content validation |

### Files & Media

| Command | Description |
|---------|-------------|
| `/screenshot` | Read recent screenshots |
| `/stock-photo` | Search Pexels stock photos |
| `/gdrive-upload` | Upload to Google Drive |
| `/check-downloads` | Check downloads directory |

### Session & Documentation

| Command | Description |
|---------|-------------|
| `/session-summary` | Generate session summary |
| `/transcript` | Create session transcript |
| `/recover-session` | Recover from auto-compact |

---

## MCP Server Integration

### Available Tools (52+)

**Google Drive (13 tools):**
- File management, uploads, sharing, organization

**Pexels (4 tools):**
- Stock photo search and download

**System Monitoring:**
- CPU, disk, memory, process monitoring

**Remote Server (Ebon):**
- SSH commands, health checks

**File Operations:**
- Advanced file management

**Web Requests:**
- HTTP GET/POST operations

### Checking MCP Status

```bash
# Via slash command
/mcp-status

# Or manually
claude mcp list
```

---

## CI/CD Pipeline

### GitHub Actions Jobs

| Job | Trigger | Purpose |
|-----|---------|---------|
| ShellCheck | Push/PR | Lint shell scripts |
| Test | Push/PR | Run test suites |
| Security Scan | Push/PR | Bandit, TruffleHog, Safety |
| WordPress Validation | Main only | WP-CLI tests |
| Dashboard | After tests | Generate system dashboard |
| Deploy | Main push | Production deployment |
| Backup Check | Weekly | Verify backups |
| Notify | Always | Pipeline notifications |

### Security Scanning

- **Bandit** - Python security linting
- **TruffleHog** - Secret detection
- **Safety** - Dependency vulnerability scanning

---

## WordPress Management

### Work Session Protocol

**CRITICAL: All WordPress work requires a session directory**

```bash
# 1. Create session directory
SESSION_DIR="work/wordpress/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"

# 2. Save original state BEFORE changes
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_before.html"

# 3. Make edits, save iterations
cat "$SESSION_DIR/page_105_before.html" | sed 's/old/new/' > "$SESSION_DIR/page_105_v1.html"

# 4. Save final version
cp "$SESSION_DIR/page_105_v1.html" "$SESSION_DIR/page_105_final.html"

# 5. Apply update
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_final.html")"

# 6. VERIFY update succeeded
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_after.html"
diff "$SESSION_DIR/page_105_final.html" "$SESSION_DIR/page_105_after.html"

# 7. Document changes
cat > "$SESSION_DIR/README.md" <<EOF
# Session: Description
Date: $(date)
Status: Completed
EOF
```

### Fact-Checking (CRITICAL)

**Campaign data MUST be verified before use:**

| Topic | CORRECT Value | WRONG Values |
|-------|---------------|--------------|
| Total Budget | $81M | $110.5M, $110M |
| Wellness ROI | $2-3 per $1 | $1.80, $1.8 |
| JCPS Reading | 34-35% | 44%, 45% |
| JCPS Math | 27-28% | 41%, 40% |

**Source of truth:** `QUICK_FACTS_SHEET.md`

---

## Key Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python project config, dependencies, tool settings |
| `.pre-commit-config.yaml` | Pre-commit hook configuration |
| `.github/workflows/ci.yml` | CI/CD pipeline definition |
| `pytest.ini` | Pytest configuration |
| `.pylintrc` | Pylint settings |
| `.flake8` | Flake8 settings |
| `.claude/settings.json` | Claude Code permissions |

---

## Testing

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Fast, isolated unit tests
├── integration/             # External service tests
├── security/                # Security-focused tests
└── performance/             # Performance benchmarks
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# By marker
pytest -m unit           # Unit tests only
pytest -m security       # Security tests
pytest -m integration    # Integration tests

# With coverage
pytest --cov=lib/python --cov-report=html
```

### Test Markers

- `@pytest.mark.unit` - Fast, isolated
- `@pytest.mark.integration` - Require external services
- `@pytest.mark.security` - Security-focused
- `@pytest.mark.slow` - Long-running
- `@pytest.mark.wordpress` - WordPress-specific
- `@pytest.mark.ssh` - Require SSH connectivity

---

## Security Considerations

### Never Commit

- API keys, tokens, passwords
- `.env` files (use `.env.example`)
- Private keys (`.pem`, `.key`)
- Personal/business documents
- Credentials of any kind

### Always

- Use `.gitignore` properly
- Store secrets in environment variables
- Run credential scans (pre-commit handles this)
- Use read-only permissions where possible

### Sensitive File Protection

Claude Code settings restrict access to:
- `.env*` files
- `.ssh/` directory
- Credentials files
- Business/personal directories

---

## Troubleshooting

### Common Issues

**MCP servers disconnected:**
```bash
# Check status
/mcp-status

# Restart Claude Code to reconnect
```

**Pre-commit hook failures:**
```bash
# Run hooks manually
pre-commit run --all-files

# Skip hooks (use sparingly)
git commit --no-verify
```

**Test failures:**
```bash
# Run with verbose output
pytest tests/ -v --tb=long

# Run specific failing test
pytest tests/unit/test_file.py::test_function -v
```

---

## Quick Reference

### Environment Setup

```bash
# Install dependencies
pip install -e ".[dev,test]"

# Install pre-commit hooks
pre-commit install

# Run health check
health-dashboard
```

### Common Operations

```bash
# Search scripts
grep -r "pattern" scripts/

# Run tests
pytest tests/ -v

# Generate docs
generate-docs

# Check system health
health-dashboard
```

### Git Operations

```bash
# Create feature branch
git checkout -b feature/description

# Commit with semantic message
git commit -m "feat: Add new feature"

# Push to remote
git push -u origin feature/description
```

---

## Work Files Preservation Protocol

### Critical Rules

- **NEVER use `/tmp/`** for work files - cleared on reboot
- **ALWAYS use session directories** for all intermediate files
- **SAVE before/after states** for verification
- **DOCUMENT all changes** in session README.md

### Session Directory Structure

```bash
SESSION_DIR="work/wordpress/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"

# Files follow this pattern:
# - {resource}_{id}_before.html  (original state)
# - {resource}_{id}_v1.html      (first edit)
# - {resource}_{id}_v2.html      (second edit)
# - {resource}_{id}_final.html   (ready to apply)
# - {resource}_{id}_after.html   (verified result)
# - README.md                    (session documentation)
```

---

## Related Documentation

- **README.md** - Project overview
- **CONTRIBUTING.md** - Contribution guidelines
- **PROJECT_ARCHITECTURE.md** - Detailed architecture
- **SECURITY.md** - Security policies
- **CHANGELOG.md** - Version history
- **.claude/workflows/** - Detailed workflow docs
- **.claude/protocols/** - Standard procedures

---

## AI Assistant Guidelines

When working with this codebase:

1. **Check before creating** - Search for existing scripts before creating new ones
2. **Follow naming conventions** - lowercase_with_underscores_v1.0.0.ext
3. **Use session directories** - Never work directly, always create session dirs
4. **Verify facts** - Check QUICK_FACTS_SHEET.md for campaign data
5. **Save before/after states** - Always capture original state before changes
6. **Run tests** - Validate changes with pytest
7. **Document changes** - Create README.md in session directories
8. **Never use /tmp/** - All work files in proper session directories

### Skills Creation Standards

When creating Claude Code skills:

```yaml
---
name: skill-name        # lowercase, hyphens only, max 64 chars
description: What this skill does and when to invoke it
---
```

**Name requirements:**
- Lowercase letters, numbers, hyphens ONLY
- Max 64 characters
- No spaces, underscores, or capitals

**Description requirements:**
- Clear explanation of function AND when to use
- Max 1024 characters
- Include trigger keywords

---

**Maintained by:** Skippy Development Team
**Repository:** github.com/eboncorp/skippy-system-manager
