# Skippy System Manager - Project Architecture

**Version**: 1.0.0
**Last Updated**: 2025-11-05
**Maintainer**: Skippy Development Team

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Directory Structure](#directory-structure)
4. [Core Components](#core-components)
5. [Data Flow](#data-flow)
6. [Integration Points](#integration-points)
7. [Technology Stack](#technology-stack)
8. [Development Workflow](#development-workflow)

---

## Project Overview

### Purpose

Skippy System Manager is a comprehensive automation and management suite designed to handle:
- Infrastructure automation and monitoring
- WordPress website management
- System administration tasks
- Backup and disaster recovery
- Security auditing and compliance
- Document processing and organization

### Project Statistics

- **Total Scripts**: 319+ automation tools
- **Languages**: Python (156), Bash (163), Node.js
- **MCP Tools**: 43+ specialized tools
- **Protocols**: 16+ documented workflows
- **Test Suites**: Unit, Integration, Smoke, Security, WordPress
- **CI/CD**: GitHub Actions with 8 job stages

### Target Environment

- **Primary OS**: Linux (Ubuntu/Debian)
- **Primary Hosting**: GoDaddy shared hosting
- **Local Environment**: Home server infrastructure
- **Remote Management**: SSH-based automation

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SKIPPY SYSTEM MANAGER                     │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  MCP SERVER   │    │   SCRIPT      │    │  PROTOCOL     │
│   (v2.0.0)    │    │   LIBRARY     │    │   SYSTEM      │
│               │    │               │    │               │
│ • 43+ Tools   │    │ • 319 Scripts │    │ • 16 Protocols│
│ • FastMCP     │    │ • 19 Categories│   │ • Workflows   │
│ • Python 3.12 │    │ • Versioned   │    │ • Standards   │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                    │                     │
        └────────────────────┼─────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  WORDPRESS   │    │    SYSTEM    │    │   BACKUP &   │
│  MANAGEMENT  │    │  MONITORING  │    │   RECOVERY   │
│              │    │              │    │              │
│ • WP-CLI     │    │ • Resource   │    │ • Automated  │
│ • Themes     │    │   Tracking   │    │ • Verified   │
│ • Plugins    │    │ • Logs       │    │ • Scheduled  │
│ • Database   │    │ • Alerts     │    │ • Cloud Sync │
└──────────────┘    └──────────────┘    └──────────────┘
```

### Architecture Layers

#### 1. **Interface Layer**
- **MCP Server**: Primary programmatic interface
- **CLI Scripts**: Direct command-line automation
- **Protocols**: Human-readable workflow documentation

#### 2. **Service Layer**
- **WordPress Operations**: Theme, plugin, database management
- **System Operations**: Monitoring, resource management
- **Network Operations**: Remote server connectivity
- **Security Operations**: Scanning, auditing, credential management

#### 3. **Data Layer**
- **Conversations**: Session logs and documentation
- **Protocols**: Process documentation
- **Backups**: WordPress and system backups
- **Logs**: System and application logs

#### 4. **Infrastructure Layer**
- **Local Server**: Development and testing
- **Remote Server (ebon)**: Production WordPress hosting
- **Cloud Storage**: Google Drive backup sync
- **Version Control**: GitHub repository

---

## Directory Structure

```
skippy-system-manager/
│
├── .github/
│   └── workflows/
│       └── ci.yml                    # CI/CD pipeline (8 jobs)
│
├── mcp-servers/
│   └── general-server/
│       ├── server.py                 # Main MCP server (43+ tools)
│       ├── .env                      # Server configuration (gitignored)
│       └── README.md                 # MCP server documentation
│
├── scripts/                          # 319+ automation scripts
│   ├── automation/                   # 27 automation scripts
│   ├── backup/                       # 9 backup scripts
│   ├── Blockchain/                   # 3 blockchain scripts
│   ├── data_processing/              # Data processing tools
│   ├── deployment/                   # Deployment automation
│   ├── disaster_recovery/            # DR scripts
│   ├── maintenance/                  # System maintenance
│   ├── monitoring/                   # Monitoring tools
│   ├── network/                      # Network management
│   ├── optimization/                 # Performance optimization
│   ├── security/                     # Security tools
│   ├── testing/                      # Test frameworks
│   ├── utility/                      # General utilities
│   ├── wordpress/                    # WordPress management
│   ├── legacy_system_managers/       # 49+ legacy scripts (maintenance mode)
│   └── archive/                      # 100+ deprecated scripts
│
├── documentation/
│   ├── protocols/                    # 16+ protocol documents
│   │   ├── script_saving_protocol.md
│   │   ├── error_logging_protocol.md
│   │   ├── git_workflow_protocol.md
│   │   ├── wordpress_maintenance_protocol.md
│   │   └── ...
│   └── guides/                       # User and developer guides
│
├── conversations/                    # 180+ session logs
│   ├── automation_sessions/
│   ├── security_sessions/
│   ├── wordpress_sessions/
│   └── test_reports/
│
├── app-to-deploy/                    # Deployment artifacts
│   └── NexusController/              # (Currently empty)
│
├── SCRIPT_INDEX.json                 # Comprehensive script catalog
├── SCRIPT_STATUS.md                  # Active vs deprecated tracking
├── PROJECT_ARCHITECTURE.md           # This file
├── SECURITY.md                       # Security policies and procedures
├── README.md                         # Project overview
└── .gitignore                        # 114 ignore rules

```

---

## Core Components

### 1. MCP Server (`/mcp-servers/general-server/`)

**Purpose**: Primary programmatic interface for Claude AI integration

**Technology**: Python 3.12 + FastMCP

**Key Features**:
- 43+ specialized tools organized by function
- Timeout protection (5-120 seconds per operation)
- SSH connectivity to remote servers
- WordPress management via WP-CLI
- Git operations and credential scanning
- Database queries (read-only safety)
- Docker container management
- Log file analysis

**Tool Categories**:
1. File Operations (read, write, search, list)
2. System Monitoring (disk, memory, processes, services)
3. Remote Server Management (SSH to ebon)
4. Web Requests (HTTP GET/POST)
5. WordPress Management (WP-CLI, backups, database)
6. Git Operations (status, diff, credential scanning)
7. Skippy Script Management (search, info)
8. Protocol and Conversation Access
9. Docker Container Management
10. Log File Analysis
11. Database Queries (safe read-only)

**Configuration**:
- Uses `.env` file for credentials (gitignored)
- Hardcoded paths (see Issue #1 in improvements)

### 2. Script Library (`/scripts/`)

**Purpose**: Comprehensive automation toolkit

**Organization**: 19 categories by function

**Naming Convention**: `script_name_vMAJOR.MINOR.PATCH.ext`

**Key Scripts**:
- **Testing**: `test_runner_v1.0.0.sh` - Master test framework
- **Backup**: `full_home_backup_v1.0.0.sh` - Complete backup
- **WordPress**: Multiple WP management scripts
- **Security**: Vulnerability scanning, credential checking
- **Monitoring**: System dashboards, resource tracking

**Script Lifecycle**:
1. Active scripts in category directories
2. Legacy scripts in `/legacy_system_managers/`
3. Deprecated scripts in `/archive/`
4. Documented in `SCRIPT_STATUS.md`

### 3. Protocol System (`/documentation/protocols/`)

**Purpose**: Standardized workflow documentation

**Protocol Categories**:
1. **Development Protocols**
   - Script Saving Protocol
   - Git Workflow Protocol
   - Testing Standards Protocol

2. **Operations Protocols**
   - WordPress Maintenance Protocol
   - Backup Strategy Protocol
   - Disaster Recovery Protocol

3. **Security Protocols**
   - Credential Management Protocol
   - Security Audit Protocol
   - Incident Response Protocol

4. **Configuration Protocols**
   - Configuration Variables Protocol
   - Environment Setup Protocol

**Format**: Markdown with structured sections
- Context
- Guidelines
- Step-by-step procedures
- Examples
- Related protocols

### 4. CI/CD Pipeline (`/.github/workflows/ci.yml`)

**Purpose**: Automated testing and deployment

**Trigger Events**:
- Push to main/develop branches
- Pull requests to main
- Daily schedule (2 AM)
- Manual workflow dispatch

**Pipeline Jobs**:
1. **ShellCheck** - Lint shell scripts
2. **Test** - Run unit, smoke, security tests
3. **Security Scan** - TruffleHog secret detection
4. **WordPress Validation** - WP-CLI tests
5. **Dashboard** - Generate system dashboard
6. **Deploy** - Production deployment (main branch only)
7. **Backup Check** - Weekly backup verification
8. **Notify** - Pipeline status notifications

**Current Status**: Some jobs use placeholders (see improvements)

---

## Data Flow

### Typical Workflow: WordPress Update

```
User Request
    │
    ▼
MCP Server (wordpress_update tool)
    │
    ├─→ Read protocol: /documentation/protocols/wordpress_maintenance_protocol.md
    │
    ├─→ SSH to remote server (ebon@10.0.0.29)
    │
    ├─→ Execute WP-CLI commands
    │   ├─ wp core update
    │   ├─ wp plugin update --all
    │   └─ wp theme update --all
    │
    ├─→ Create backup
    │   └─ Call: /scripts/backup/full_home_backup_v1.0.0.sh
    │
    ├─→ Log conversation
    │   └─ Write: /conversations/wordpress_sessions/update_YYYY-MM-DD.md
    │
    └─→ Return results to user
```

### Typical Workflow: System Monitoring

```
Scheduled Task (cron)
    │
    ▼
MCP Server (monitor_system tool)
    │
    ├─→ Check disk usage (psutil)
    │
    ├─→ Check memory usage (psutil)
    │
    ├─→ Check running processes
    │
    ├─→ Check system services
    │
    ├─→ Analyze logs
    │   └─ /var/log/syslog, /var/log/auth.log
    │
    ├─→ Generate dashboard
    │   └─ /scripts/monitoring/system_dashboard_v1.0.0.sh
    │
    ├─→ Check thresholds
    │   └─ If exceeded → Alert
    │
    └─→ Log results
        └─ /conversations/monitoring_reports/
```

### Typical Workflow: Backup Verification

```
CI/CD Schedule (weekly)
    │
    ▼
GitHub Actions: backup-check job
    │
    ├─→ Checkout code
    │
    ├─→ Execute: /scripts/backup/backup_verification_test_v1.0.0.sh
    │   │
    │   ├─→ Check backup files exist
    │   ├─→ Verify backup integrity
    │   ├─→ Test restore procedure
    │   └─→ Generate report
    │
    ├─→ Upload report artifact
    │   └─ /conversations/backup_reports/
    │
    └─→ Notify on failure
```

---

## Integration Points

### External Services

#### 1. **GitHub**
- **Purpose**: Version control, CI/CD
- **Integration**: Git operations, GitHub Actions
- **Authentication**: SSH keys, GitHub tokens
- **Endpoints**:
  - Repository: `https://github.com/eboncorp/skippy-system-manager`
  - API: GitHub REST API v3

#### 2. **GoDaddy Shared Hosting**
- **Purpose**: Production WordPress hosting
- **Integration**: SSH (ebon@10.0.0.29)
- **Limitations**:
  - Shared environment restrictions
  - No root access
  - Resource constraints
- **Management**: WP-CLI, FTP/SFTP

#### 3. **Google Drive**
- **Purpose**: Cloud backup storage
- **Integration**: `rclone`, `gdrive-backup` scripts
- **Authentication**: OAuth tokens (`.env`)
- **Sync Frequency**: Daily/weekly (configurable)

#### 4. **WordPress (rundaverun.org)**
- **Version**: Latest WordPress core
- **Integration**: WP-CLI via SSH
- **Components**:
  - Core: WordPress installation
  - Themes: Custom and third-party
  - Plugins: Security, performance, SEO
  - Database: MySQL (GoDaddy managed)

### Internal Dependencies

#### Python Packages
```
mcp[cli]>=1.1.0      # MCP server framework
fastmcp              # FastMCP implementation
psutil               # System monitoring
httpx                # HTTP requests
paramiko             # SSH connectivity
sqlalchemy           # Database operations (future)
pytest               # Testing framework (to be added)
```

#### System Dependencies
```
bash >= 4.0          # Shell scripts
wp-cli               # WordPress management
git                  # Version control
jq                   # JSON processing
curl                 # HTTP requests
gpg                  # Encryption
shellcheck           # Shell linting
```

---

## Technology Stack

### Languages

| Language | Usage | Scripts | Purpose |
|----------|-------|---------|---------|
| **Python** | 49% | 156 | MCP server, automation, data processing |
| **Bash** | 51% | 163 | System scripts, deployment, monitoring |
| **JavaScript** | <1% | Few | Node.js utilities |
| **Markdown** | - | 180+ | Documentation, protocols, logs |

### Frameworks & Libraries

#### Python
- **FastMCP**: MCP server framework
- **psutil**: System monitoring
- **httpx**: Async HTTP client
- **pathlib**: File operations

#### Bash
- **Set options**: `set -euo pipefail` (error handling)
- **jq**: JSON processing
- **wp-cli**: WordPress management

### Development Tools

- **Version Control**: Git + GitHub
- **CI/CD**: GitHub Actions
- **Linting**: ShellCheck (Bash), pylint/flake8 (Python - to be added)
- **Testing**: Custom test framework, pytest (to be added)
- **Security**: TruffleHog (secret scanning)
- **Documentation**: Markdown, protocols

### Infrastructure

- **OS**: Linux (Ubuntu/Debian primary)
- **Container**: Docker (optional, some scripts)
- **Package Manager**: apt, pip3
- **Process Manager**: systemd, cron
- **Monitoring**: psutil, custom dashboards

---

## Development Workflow

### Adding New Features

```
1. Plan
   └─→ Review protocols: /documentation/protocols/

2. Develop
   ├─→ Create feature branch: git checkout -b feature/name
   ├─→ Write script: scripts/category/script_name_v1.0.0.ext
   ├─→ Follow naming convention
   └─→ Add documentation

3. Test
   ├─→ Write tests (if applicable)
   ├─→ Run: scripts/testing/test_runner_v1.0.0.sh
   └─→ Verify locally

4. Document
   ├─→ Update SCRIPT_INDEX.json
   ├─→ Update SCRIPT_STATUS.md
   └─→ Log conversation: conversations/

5. Commit
   ├─→ Follow git workflow protocol
   ├─→ Use descriptive commit messages
   └─→ Push to feature branch

6. Deploy
   ├─→ Create pull request
   ├─→ Wait for CI/CD (tests, security scan)
   ├─→ Merge to main
   └─→ Auto-deploy (if configured)
```

### Git Branching Strategy

```
main
 ├── develop (integration branch)
 ├── feature/* (new features)
 ├── bugfix/* (bug fixes)
 ├── hotfix/* (urgent production fixes)
 └── release/* (release preparation)
```

### Code Review Process

1. **Self-review**: Check code quality, documentation
2. **Automated review**: CI/CD pipeline (linting, tests)
3. **Peer review**: (If team members available)
4. **Merge**: After all checks pass

### Release Process

1. **Version bump**: Update version numbers
2. **Changelog**: Document changes
3. **Tag**: Create git tag (e.g., `v1.2.0`)
4. **Release notes**: Publish to GitHub
5. **Deploy**: Trigger production deployment

---

## Security Considerations

### Credential Management

- **Storage**: `.env` files (gitignored)
- **Permissions**: 600 (owner read/write only)
- **Types**: SSH passwords, API tokens, database credentials
- **Rotation**: Regular credential rotation (recommended)

### Access Control

- **SSH**: Password authentication (should migrate to keys)
- **File Permissions**: Restrictive permissions on sensitive files
- **Sudo**: Limited sudo access (configured in `/etc/sudoers.d/`)

### Security Scanning

- **Secrets**: TruffleHog in CI/CD pipeline
- **Vulnerabilities**: Regular security scans
- **Monitoring**: Log analysis for suspicious activity

### Compliance

- **Data Protection**: Backup encryption (to be implemented)
- **Audit Trail**: Conversation logs, git history
- **Incident Response**: Documented in security protocol

---

## Performance Considerations

### Resource Usage

- **Disk**: ~500MB-2GB (scripts, logs, backups)
- **Memory**: Minimal (<100MB for most scripts)
- **CPU**: Low (except during backups, scans)

### Optimization Strategies

1. **Caching**: Conversation logs, dashboard data
2. **Parallel Execution**: Independent operations
3. **Lazy Loading**: Load data only when needed
4. **Cleanup**: Regular log rotation, old backup removal

### Scalability

- **Current**: Single server, limited resources
- **Future**:
  - Microservices architecture
  - Containerization (Docker)
  - Load balancing (if needed)
  - Distributed backups

---

## Monitoring & Observability

### Metrics Tracked

- **System**: Disk, memory, CPU usage
- **Services**: Service status, uptime
- **Backups**: Success rate, size, duration
- **WordPress**: Plugin/theme status, update availability
- **Security**: Failed login attempts, credential leaks

### Logging

- **System Logs**: `/var/log/syslog`, `/var/log/auth.log`
- **Application Logs**: `/conversations/` (structured logs)
- **Error Logs**: Stderr output from scripts
- **Audit Logs**: Git history, credential usage

### Alerting

- **Critical Errors**: Email/webhook notifications
- **Resource Thresholds**: Disk >90%, memory >80%
- **Backup Failures**: Immediate notification
- **Security Events**: Suspicious login attempts

---

## Troubleshooting

### Common Issues

#### Issue 1: Hardcoded Paths
**Symptom**: Scripts fail with "file not found"
**Cause**: Paths hardcoded to `/home/dave/skippy`
**Solution**:
- Use environment variables
- See: Configuration improvement (#3)

#### Issue 2: SSH Authentication Failures
**Symptom**: "Permission denied" when connecting to ebon
**Cause**: Password expired or incorrect in `.env`
**Solution**:
- Update `EBON_PASSWORD` in `.env`
- Consider migrating to SSH keys

#### Issue 3: WordPress Update Failures
**Symptom**: WP-CLI commands timeout or fail
**Cause**: GoDaddy resource limits
**Solution**:
- Increase timeout in MCP server
- Run updates during low-traffic periods

### Debug Mode

Enable debug output in scripts:
```bash
export DEBUG=1
./scripts/automation/script_name_v1.0.0.sh
```

Enable verbose logging in MCP server:
```python
logging.basicConfig(level=logging.DEBUG)
```

---

## Future Enhancements

### Planned Improvements

1. **Configuration Management** ✅ (In progress)
   - Centralized config.env
   - Environment variable validation
   - Multi-environment support

2. **Testing Infrastructure** ✅ (In progress)
   - pytest framework
   - Unit tests for Python scripts
   - Integration tests
   - Code coverage tracking

3. **Security Hardening**
   - SSH key authentication
   - Secrets management (HashiCorp Vault)
   - Input validation library
   - Regular security audits

4. **Code Quality**
   - pylint/flake8 configuration
   - Pre-commit hooks
   - Code style guide
   - Automated formatting

5. **Observability**
   - Centralized logging
   - Metrics dashboard
   - Alerting system
   - Performance profiling

### Roadmap

**Q4 2025** (Current)
- ✅ Protocol system
- ✅ CI/CD pipeline
- 🔄 Configuration management
- 🔄 Testing infrastructure

**Q1 2026**
- Security hardening
- Code quality improvements
- Documentation completion
- Legacy code cleanup

**Q2 2026**
- Microservices architecture
- Container orchestration
- Advanced monitoring
- Performance optimization

---

## Related Documentation

- **Script Status**: `SCRIPT_STATUS.md` - Active vs deprecated scripts
- **Security Policy**: `SECURITY.md` - Security procedures
- **MCP Server**: `/mcp-servers/general-server/README.md` - MCP documentation
- **Protocols**: `/documentation/protocols/` - Workflow documentation
- **Contributing**: `CONTRIBUTING.md` - Development guide (to be created)

---

## Questions & Support

**Documentation Issues**: File an issue or submit a PR

**Script Questions**: Check `SCRIPT_STATUS.md` or search conversations

**Security Concerns**: See `SECURITY.md` for reporting procedures

**Contributing**: Follow protocols in `/documentation/protocols/`

---

**Last Updated**: 2025-11-05
**Version**: 1.0.0
**Maintainer**: Skippy Development Team
