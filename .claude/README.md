# Claude Code Configuration - Skippy Project

**Version:** 2.1.0
**Last Updated:** 2025-12-02

---

## Quick Start

### Primary Configuration Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Main project instructions (AI reads this) |
| `settings.json` | Permissions and tool access rules |
| `mcp.json` | MCP server documentation |

---

## Directory Structure

```
.claude/
├── CLAUDE.md                # Main AI instructions (545 lines)
├── settings.json            # Permissions configuration
├── settings.local.json      # Local permission overrides
├── mcp.json                 # MCP servers documentation
├── README.md                # This file
│
├── commands/                # 32 slash commands
│   ├── content-approve.md   # Approve WordPress content
│   ├── deploy-verify.md     # Deployment verification
│   ├── ebon-status.md       # Remote server status
│   ├── error-logs.md        # View error logs
│   ├── fact-check.md        # Campaign fact validation
│   ├── fix-permissions.md   # Fix file permissions
│   ├── gdrive-upload.md     # Google Drive upload
│   ├── git-branches.md      # Git branch management
│   ├── mcp-status.md        # MCP server status
│   ├── recover-session.md   # Context recovery
│   ├── screenshot.md        # Screenshot capture
│   ├── session-summary.md   # Session documentation
│   ├── status.md            # System status dashboard
│   ├── stock-photo.md       # Pexels stock photos
│   ├── transcript.md        # Session transcript
│   └── wordpress-debug.md   # WordPress diagnostics
│
├── agents/                  # Custom agent definitions
│   └── code-reviewer.md     # Code review agent
│
├── output-styles/           # Output formatting
│   └── wordpress-dev.md     # WordPress dev formatting
│
├── permission-profiles/     # Reusable permission sets
│   ├── README.md            # Profile documentation
│   ├── wordpress-permissive.json
│   └── script-dev-restrictive.json
│
├── reference/               # Quick reference docs
│   └── quick_facts.md       # Campaign facts sheet
│
├── workflows/               # Step-by-step processes
│   └── wordpress_update_workflow.md
│
└── protocols/               # Standard procedures
    └── file_naming_standards.md
```

---

## Slash Commands (32 total)

### System & Health
| Command | Description |
|---------|-------------|
| `/status` | Unified system dashboard |
| `/mcp-status` | MCP server status |
| `/ebon-status` | Remote server health |
| `/error-logs` | Aggregated error logs |

### WordPress
| Command | Description |
|---------|-------------|
| `/wordpress-debug` | 15-layer diagnostic |
| `/deploy-verify` | Verify deployment |
| `/content-approve` | Approve content updates |
| `/fact-check` | Validate campaign facts |

### Files & Media
| Command | Description |
|---------|-------------|
| `/screenshot` | Recent screenshots |
| `/stock-photo` | Pexels stock photos |
| `/gdrive-upload` | Google Drive upload |

### Git & Session
| Command | Description |
|---------|-------------|
| `/git-branches` | Branch management |
| `/session-summary` | Generate summary |
| `/transcript` | Create transcript |
| `/recover-session` | Context recovery |

### Utilities
| Command | Description |
|---------|-------------|
| `/fix-permissions` | Fix file permissions |

---

## MCP Servers (6 servers, 146 tools)

| Server | Tools | Purpose |
|--------|-------|---------|
| general-server | 67 | Skippy system management |
| github | 26 | GitHub API |
| chrome-devtools | 26 | Browser automation |
| crypto-portfolio | 11 | Crypto portfolio tracking |
| brave-search | 2 | Web search |
| coinbase-agentkit | 14 | Wallet, ERC-20, NFT, WETH |

See `mcp.json` for full documentation.

---

## Permission Profiles

### wordpress-permissive.json
- Full WP-CLI access
- Database read/write
- For trusted WordPress operations

### script-dev-restrictive.json
- Read-only file access
- No system commands
- For safe script development

---

## Agents

### code-reviewer
- Type: code-review
- Tools: All standard tools
- Purpose: Code quality review

---

## Configuration Hierarchy

1. **User-level** (`~/.claude/`) - Personal skills, hooks, credentials
2. **Project-level** (`skippy/.claude/`) - This directory, project-specific

Project settings override user settings when both exist.

---

## Related Documentation

| Location | Content |
|----------|---------|
| `~/.claude/CLAUDE.md` | Global AI instructions (73 skills, 12 hooks) |
| `~/.claude/skills/` | 73 skill directories |
| `~/.claude/hooks/` | 12 automation hooks |
| `/home/dave/skippy/documentation/` | Project docs |

---

## Usage Examples

**Check system status:**
```
/status
```

**Fact-check content:**
```
/fact-check "content to verify"
```

**Approve WordPress update:**
```
/content-approve --page-id=105 --approver=dave --notes="description"
```

**Debug WordPress:**
```
/wordpress-debug
```

---

**Status:** Active
**Last Audit:** 2025-12-02
