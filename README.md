# Skippy System Manager

[![CI/CD Pipeline](https://github.com/eboncorp/skippy-system-manager/workflows/Skippy%20CI/CD/badge.svg)](https://github.com/eboncorp/skippy-system-manager/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> A comprehensive automation and management suite for infrastructure, WordPress, and system administration

## 🚀 Features

- **🤖 MCP Server v2.0.0**: 43+ tools for AI-powered automation
- **📜 319+ Scripts**: Organized automation across 19 categories
- **🔒 Security First**: Input validation, credential management, security scanning
- **📊 System Monitoring**: Real-time resource tracking and alerting
- **🌐 WordPress Management**: Automated updates, backups, and deployment
- **☁️ Cloud Integration**: Google Drive backup sync
- **🔄 CI/CD Pipeline**: Automated testing and deployment
- **📖 Comprehensive Documentation**: 16+ protocols and guides

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Documentation](#documentation)
- [Development](#development)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## ⚡ Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/eboncorp/skippy-system-manager.git
cd skippy-system-manager

# 2. Install dependencies
make setup

# 3. Configure environment
cp config.env.example config.env
nano config.env  # Edit with your settings

# 4. Validate configuration
make validate-config

# 5. Run tests
make test

# 6. Start using Skippy!
./scripts/monitoring/system_dashboard_v1.0.0.sh
```

## 📦 Installation

### Prerequisites

- **OS**: Linux (Ubuntu/Debian recommended)
- **Python**: 3.8 or higher
- **Bash**: 4.0 or higher
- **Git**: 2.0 or higher

### Option 1: Standard Installation

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip jq curl gpg shellcheck

# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# Set up configuration
cp config.env.example config.env
chmod 600 config.env
# Edit config.env with your settings

# Validate setup
bash scripts/utility/validate_config.sh
```

### Option 2: Docker Installation

```bash
# Build Docker image
docker-compose build

# Start services
docker-compose up -d

# Access MCP server
docker-compose exec skippy-mcp python mcp-servers/general-server/server.py
```

## ⚙️ Configuration

Skippy uses a centralized configuration system via `config.env`:

```bash
# Required settings
export SKIPPY_BASE_PATH="/path/to/skippy"
export WORDPRESS_BASE_PATH="/path/to/wordpress"
export EBON_HOST="user@remote-server"
export EBON_PASSWORD="your-password"  # Or use SSH keys

# Optional settings
export WP_SITE_URL="https://yoursite.com"
export GDRIVE_CLIENT_ID="your-google-client-id"
export GITHUB_TOKEN="your-github-token"
```

**See [config.env.example](config.env.example) for all available options.**

### Configuration Validation

```bash
source config.env
bash scripts/utility/validate_config.sh
```

## 🎯 Usage

### MCP Server (AI Integration)

```bash
# Start MCP server
cd mcp-servers/general-server
python server.py

# Available tools:
# - File operations (read, write, search)
# - System monitoring (disk, memory, processes)
# - WordPress management (updates, backups)
# - Remote server access (SSH commands)
# - And 39 more...
```

### Script Usage

```bash
# System monitoring
./scripts/monitoring/system_dashboard_v1.0.0.sh snapshot

# WordPress backup
./scripts/backup/full_home_backup_v1.0.0.sh

# Run tests
./scripts/testing/test_runner_v1.0.0.sh run unit

# Disaster recovery
./scripts/disaster_recovery/dr_automation_v1.0.0.sh
```

### Finding Scripts

```bash
# List all active scripts
make list-scripts

# Search for specific functionality
grep -r "backup" scripts/ --include="*.sh"

# Check script status (active/deprecated)
cat SCRIPT_STATUS.md
```

## 📚 Documentation

### Core Documentation

- **[PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md)** - System architecture and design
- **[SCRIPT_STATUS.md](SCRIPT_STATUS.md)** - Active vs deprecated script tracking
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Developer guide and coding standards
- **[SECURITY.md](SECURITY.md)** - Security policies and procedures

### Protocols (Systematic Workflows)

Located in `documentation/protocols/` - **30+ operational protocols**

**Branch Structure:**
- `master` - Stable, production-ready protocols
- `protocols/dev` - Active protocol development

**Key Protocols:**
- **Branch Workflow Protocol** - Protocol branch management
- **Script Saving Protocol** - How to save and version scripts
- **Git Workflow Protocol** - Branching and commit standards
- **WordPress Site Diagnostic Protocol** - Complete site diagnostics
- **Fact Checking Protocol** - Comprehensive verification procedures
- **Emergency Rollback Protocol** - Production incident recovery
- **WordPress Backup Protocol** - Backup and recovery procedures
- **And 23 more...**

See [documentation/protocols/README.md](documentation/protocols/README.md) for complete index.

### MCP Server Documentation

See [mcp-servers/general-server/README.md](mcp-servers/general-server/README.md) for:
- Tool reference (all 43+ tools)
- API documentation
- Integration examples
- Configuration options

### Testing Documentation

See [tests/README.md](tests/README.md) for:
- Running tests
- Writing new tests
- Test coverage requirements
- CI/CD integration

## 🛠️ Development

### Setting Up Development Environment

```bash
# Install development dependencies
make dev-setup

# Install pre-commit hooks
pre-commit install

# Run linters
make lint

# Format code
make format

# Run all tests with coverage
make test-coverage
```

### Project Structure

```
skippy-system-manager/
├── .github/workflows/      # CI/CD pipeline
├── mcp-servers/            # MCP server (43+ tools)
├── scripts/                # 319+ automation scripts
│   ├── automation/         # Document scanning, music management
│   ├── backup/             # Backup and restore operations
│   ├── deployment/         # Deployment automation
│   ├── monitoring/         # System monitoring
│   ├── security/           # Security tools
│   ├── wordpress/          # WordPress management
│   └── ...                 # 13 more categories
├── lib/python/             # Shared Python libraries
│   ├── skippy_logger.py    # Centralized logging
│   └── skippy_validator.py # Input validation
├── tests/                  # Test suite (unit, integration)
├── documentation/          # Protocols and guides
└── config.env.example      # Configuration template
```

### Common Development Tasks

```bash
# Create new feature branch
git checkout -b feature/my-feature

# Run tests before committing
make test

# Check code quality
make lint

# Run specific test category
pytest -m unit
pytest -m integration

# Generate coverage report
make coverage-html
open htmlcov/index.html
```

## 🧪 Testing

### Running Tests

```bash
# All tests
make test

# Specific test categories
pytest -m unit          # Fast unit tests
pytest -m integration   # Integration tests
pytest -m security      # Security tests
pytest -m wordpress     # WordPress tests

# With coverage
make test-coverage

# Parallel execution
pytest -n auto
```

### Test Requirements

- **Minimum coverage**: 60% overall
- **New code**: 80% coverage required
- **Critical components**: 90% coverage (MCP server, security, backups)

### CI/CD Pipeline

Tests run automatically on:
- Push to `main` or `develop`
- Pull requests to `main`
- Daily schedule (2 AM)
- Manual trigger

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Development setup guide
- Coding standards (Python & Bash)
- Testing requirements
- Git workflow
- Pull request process
- Code review guidelines

### Quick Contribution Guide

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes
4. **Write** tests for new functionality
5. **Run** tests and linters (`make test lint`)
6. **Commit** with descriptive message (`git commit -m 'feat: add amazing feature'`)
7. **Push** to your fork (`git push origin feature/amazing-feature`)
8. **Open** a pull request

## 📊 Project Statistics

- **Total Scripts**: 319+
- **Script Categories**: 19
- **MCP Tools**: 43+
- **Test Coverage**: 60%+ (growing)
- **Documentation Files**: 180+
- **Protocols**: 16+
- **Active Contributors**: Growing!

## 🔒 Security

### Reporting Security Issues

**Please do not open public issues for security vulnerabilities.**

Email: security@example.com (or see [SECURITY.md](SECURITY.md))

### Security Features

- ✅ Input validation library (path traversal, SQL injection prevention)
- ✅ Command injection prevention
- ✅ Credential scanning in CI/CD (TruffleHog)
- ✅ Secure configuration management (`.env` gitignored)
- ✅ Security audit protocols
- ✅ Regular dependency updates

## 📈 Roadmap

### Q1 2026
- [ ] Microservices architecture
- [ ] Enhanced monitoring dashboard
- [ ] SSH key authentication migration
- [ ] Backup encryption

### Q2 2026
- [ ] Advanced AI integration
- [ ] Multi-environment support
- [ ] Performance optimization
- [ ] Extended WordPress toolkit

See [PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) for detailed roadmap.

## 🙏 Acknowledgments

- Built with ❤️ by the Skippy Development Team
- Powered by [FastMCP](https://github.com/jlowin/fastmcp)
- Inspired by modern DevOps practices

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support & Contact

- **Documentation**: Check `/documentation` directory
- **Issues**: [GitHub Issues](https://github.com/eboncorp/skippy-system-manager/issues)
- **Discussions**: [GitHub Discussions](https://github.com/eboncorp/skippy-system-manager/discussions)
- **Email**: support@example.com

## 🌟 Star History

If you find Skippy useful, please consider giving it a star! ⭐

## 🔗 Related Projects

- [FastMCP](https://github.com/jlowin/fastmcp) - Model Context Protocol implementation
- [WP-CLI](https://wp-cli.org/) - WordPress command-line interface

---

**Made with ❤️ for automating the boring stuff**

[⬆ Back to top](#skippy-system-manager)
