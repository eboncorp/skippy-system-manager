# Skippy System Manager

## Overview
Automation suite: infrastructure, WordPress (rundaverun.org), backups, security, MCP servers.
1,600+ scripts (Python: 1,422, Bash: 224) | 147 MCP tools | 8 CI/CD stages

## Directory Structure
```
scripts/          # automation/, backup/, wordpress/, security/, monitoring/, utility/, etc.
bin/              # CLI tools (PATH executable)
mcp-servers/      # general-server (67 tools), wordpress-validator
tests/            # unit/, integration/, security/, performance/
documentation/    # protocols/, guides/
conversations/    # Session logs
lib/python/       # Python library modules
```

## Before Creating Scripts
Always search first: `grep -r "keyword" scripts/` or `skippy-script search "keyword"`

## Script Header
```bash
#!/bin/bash
# Script Name v1.0.0
# Brief description
# Usage: script_name [options] arguments
# Created: YYYY-MM-DD
```

## Testing
- ShellCheck for shell, pylint/flake8 for Python, pytest for unit tests
- Run: `pytest tests/ -v` | By marker: `pytest -m unit|security|integration`
- Markers: `@pytest.mark.unit`, `.integration`, `.security`, `.slow`, `.wordpress`, `.ssh`

## CI/CD Pipeline
ShellCheck → Tests → Security Scan (Bandit, TruffleHog, Safety) → WP Validation → Deploy

## MCP Tools Summary

| Server | Tools | Categories |
|--------|-------|------------|
| general-server | 67 | Files, System, WordPress, Git, Docker, Skippy |
| github | 26 | Repos, PRs, Issues, Code Search |
| chrome-devtools | 25 | Browser, Screenshots, Performance |
| crypto-portfolio | 28 | Portfolio, Staking, DeFi, Cronos AI |
| brave-search | 2 | Web/local search |
| coinbase-agentkit | 14 | Wallet, ERC-20, NFT, WETH |

## Key Config Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python config, dependencies |
| `.pre-commit-config.yaml` | Pre-commit hooks |
| `.github/workflows/ci.yml` | CI/CD pipeline |
| `.claude/settings.json` | Claude Code permissions |

## Security
- Never commit: API keys, `.env`, private keys, credentials
- Secrets in environment variables. Pre-commit handles credential scanning
- Claude Code restricts access to `.env*`, `.ssh/`, credentials, business/personal dirs
