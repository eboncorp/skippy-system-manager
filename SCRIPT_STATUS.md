# Script Status Reference

**Last Updated**: 2025-11-05
**Purpose**: Track active vs deprecated scripts across the Skippy System Manager

## Status Legend

- 🟢 **ACTIVE**: Current, maintained, recommended for use
- 🟡 **MAINTENANCE**: Legacy but still functional, use with caution
- 🔴 **DEPRECATED**: Archived, do not use in new projects
- 📦 **ARCHIVED**: Historical reference only, not operational

---

## Active Scripts by Category

### Automation (27 scripts)
All scripts in `/scripts/automation/` are **ACTIVE** unless noted:

| Script | Version | Status | Purpose |
|--------|---------|--------|---------|
| `epson_v39_smart_scanner_v2.0.0.sh` | v2.0.0 | 🟢 | Smart document scanning (current version) |
| `music_optimizer_v2.0.0.sh` | v2.0.0 | 🟢 | Music library optimization (current version) |
| `nexus_intelligent_agent_v2.0.0.py` | v2.0.0 | 🟢 | Intelligent automation agent (current version) |
| `epson_v39_smart_scanner_v1.0.0.sh` | v1.0.0 | 🟡 | Older scanner version, use v2.0.0 |
| `music_optimizer_v1.0.0.sh` | v1.0.0 | 🟡 | Older music optimizer, use v2.0.0 |
| `nexus_intelligent_agent_v1.0.0.py` | v1.0.0 | 🟡 | Older agent version, use v2.0.0 |

**Recommendation**: When multiple versions exist, use the highest version number (v2.0.0 > v1.0.0)

### Backup (9 scripts)
All scripts in `/scripts/backup/` are **ACTIVE**:

| Script | Version | Status | Purpose |
|--------|---------|--------|---------|
| `backup_verification_test_v1.0.0.sh` | v1.0.0 | 🟢 | Verify backup integrity |
| `full_home_backup_v1.0.0.sh` | v1.0.0 | 🟢 | Complete home directory backup |
| `gdrive_backup_v1.0.0.sh` | v1.0.0 | 🟢 | Google Drive backup sync |
| `simple_backup_v1.0.0.sh` | v1.0.0 | 🟢 | Quick backup script |

### Blockchain (3 scripts)
All scripts in `/scripts/Blockchain/` are **ACTIVE**:

| Script | Version | Status | Purpose |
|--------|---------|--------|---------|
| `ethereum_node_setup_v1.0.0.sh` | v1.0.0 | 🟢 | Ethereum node setup |
| `chainlink_setup_creator_v1.0.0.sh` | v1.0.0 | 🟢 | Chainlink oracle setup |

### Deployment (scripts)
All scripts in `/scripts/deployment/` are **ACTIVE**

### Disaster Recovery (scripts)
All scripts in `/scripts/disaster_recovery/` are **ACTIVE**:

| Script | Version | Status | Purpose |
|--------|---------|--------|---------|
| `dr_automation_v1.0.0.sh` | v1.0.0 | 🟢 | Disaster recovery automation |

### Maintenance (scripts)
All scripts in `/scripts/maintenance/` are **ACTIVE**

### Monitoring (scripts)
All scripts in `/scripts/monitoring/` are **ACTIVE**

### Network (scripts)
All scripts in `/scripts/network/` are **ACTIVE**

### Optimization (scripts)
All scripts in `/scripts/optimization/` are **ACTIVE**:

| Script | Version | Status | Purpose |
|--------|---------|--------|---------|
| `performance_optimizer_v1.0.0.sh` | v1.0.0 | 🟢 | System performance optimization |

### Security (scripts)
All scripts in `/scripts/security/` are **ACTIVE**

### Testing (scripts)
All scripts in `/scripts/testing/` are **ACTIVE**:

| Script | Version | Status | Purpose |
|--------|---------|--------|---------|
| `test_runner_v1.0.0.sh` | v1.0.0 | 🟢 | Master test execution framework |

### WordPress (scripts)
All scripts in `/scripts/wordpress/` are **ACTIVE**

---

## Legacy System Managers (49+ scripts - MAINTENANCE MODE)

**Directory**: `/scripts/legacy_system_managers/`
**Status**: 🟡 **All scripts in this directory are LEGACY**

These scripts represent historical iterations of the Nexus system manager. They are functional but no longer actively developed.

### Notable Legacy Scripts

| Script | Purpose | Notes |
|--------|---------|-------|
| `nexus_stable_final_v1.0.0.py` | Final stable Nexus version | Use with caution |
| `nexus_api_server_enhanced_v2.0.0.py` | Enhanced API server | Consider MCP server instead |
| `unified_system_manager_v3_v1.0.0.py` | Unified manager v3 | Superseded by newer tools |
| `nexus_controller_v1.0.0.py` | Original Nexus controller | Historical reference |

**Migration Path**: For new projects, use the **MCP Server** (`/mcp-servers/general-server/`) instead of legacy Nexus scripts.

---

## Archived Scripts (DEPRECATED)

**Directory**: `/scripts/archive/`
**Status**: 🔴 **Do not use in new projects**

### Archive Categories

#### EbonHawk Scripts (4 scripts)
- `ebonhawk_agent_updater.py`
- `ebonhawk_dashboard.py`
- `ebonhawk_maintenance_agent.py`
- `ebonhawk_update_now.sh`

**Status**: Project discontinued

#### Music Organization (15 scripts)
Various music organization experiments from Aug 2025. Superseded by:
- `music_optimizer_v2.0.0.sh` (active)

#### Nexus Development (35+ scripts)
Historical Nexus system development iterations from Jul-Aug 2025. Superseded by:
- MCP Server (`/mcp-servers/general-server/`)

#### Setup Scripts (15 scripts)
Initial setup and configuration scripts from 2025. Many functionalities now integrated into active scripts.

---

## Version Management Guidelines

### When Multiple Versions Exist

1. **Always use the highest version number** (v2.0.0 > v1.0.0)
2. **Check modification dates** if versions are equal:
   ```bash
   ls -lt /path/to/scripts/
   ```
3. **Test before using** in production

### Version Numbering Convention

```
script_name_vMAJOR.MINOR.PATCH.ext

Example: nexus_intelligent_agent_v2.0.0.py
         └─ name ─────────────┘ └─ver─┘
```

- **MAJOR**: Breaking changes, new architecture
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, minor improvements

---

## Deprecation Policy

### How Scripts Are Deprecated

1. **Mark as MAINTENANCE** (🟡): Still works, but newer version exists
2. **Move to archive/** after 90 days
3. **Document replacement** in this file
4. **Remove after 1 year** if unused

### Current Deprecation Timeline

| Script | Deprecated Date | Replacement | Removal Date |
|--------|----------------|-------------|--------------|
| `epson_v39_smart_scanner_v1.0.0.sh` | 2025-10-31 | v2.0.0 | 2026-01-31 |
| `music_optimizer_v1.0.0.sh` | 2025-10-31 | v2.0.0 | 2026-01-31 |
| `nexus_intelligent_agent_v1.0.0.py` | 2025-10-31 | v2.0.0 | 2026-01-31 |

---

## Quick Reference: Which Script Should I Use?

### Common Tasks

| Task | Recommended Script | Location |
|------|-------------------|----------|
| Document scanning | `epson_v39_smart_scanner_v2.0.0.sh` | `/scripts/automation/` |
| System backup | `full_home_backup_v1.0.0.sh` | `/scripts/backup/` |
| Music organization | `music_optimizer_v2.0.0.sh` | `/scripts/automation/` |
| WordPress management | Use MCP Server tools | `/mcp-servers/general-server/` |
| System monitoring | Use MCP Server tools | `/mcp-servers/general-server/` |
| Disaster recovery | `dr_automation_v1.0.0.sh` | `/scripts/disaster_recovery/` |
| Testing | `test_runner_v1.0.0.sh` | `/scripts/testing/` |

### MCP Server vs Legacy Scripts

| Use Case | Use MCP Server | Use Legacy Scripts |
|----------|----------------|-------------------|
| WordPress operations | ✅ | ❌ |
| Remote server management | ✅ | ❌ |
| File operations | ✅ | ❌ |
| System monitoring | ✅ | ❌ |
| Docker management | ✅ | ❌ |
| Custom automation | ❌ | ✅ |
| Blockchain setup | ❌ | ✅ |

---

## Script Discovery

### Find All Active Scripts
```bash
# List all active scripts by category
find /home/dave/skippy/scripts \
  -type f \( -name "*.sh" -o -name "*.py" \) \
  ! -path "*/archive/*" \
  ! -path "*/legacy_system_managers/*" \
  | sort
```

### Search for Specific Functionality
```bash
# Search script descriptions
grep -r "backup" /home/dave/skippy/scripts --include="*.sh" --include="*.py"

# Use MCP Server script_search tool
# See: /mcp-servers/general-server/README.md
```

### Check Script Version
```bash
# Most scripts include version in filename
ls -1 /home/dave/skippy/scripts/automation/*v2.0.0*
```

---

## Contributing New Scripts

When adding new scripts, follow these guidelines:

1. **Use semantic versioning**: `script_name_v1.0.0.ext`
2. **Place in appropriate category directory**
3. **Add description to SCRIPT_INDEX.json**
4. **Update this file (SCRIPT_STATUS.md)**
5. **Follow protocol**: See `/documentation/protocols/script_saving_protocol.md`

---

## Maintenance Schedule

- **Weekly**: Review new scripts, update status
- **Monthly**: Archive deprecated scripts (>90 days)
- **Quarterly**: Remove archived scripts (>1 year)
- **Annually**: Major version cleanup

---

## Related Documentation

- **Project Architecture**: `PROJECT_ARCHITECTURE.md`
- **Script Saving Protocol**: `/documentation/protocols/script_saving_protocol.md`
- **MCP Server Docs**: `/mcp-servers/general-server/README.md`
- **Contributing Guide**: `CONTRIBUTING.md`

---

**Questions or Issues?**
File an issue or update this documentation following the Change Management Protocol.
