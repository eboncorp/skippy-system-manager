# Ebon Server Cleanup Plan
**Date:** 2025-10-31
**Server:** ebon (HP Z4 G4) - 10.0.0.29
**Purpose:** Apply lowercase_with_underscores naming convention
**Status:** PLAN ONLY - Not yet executed

---

## Overview

Apply the same file/directory naming cleanup to ebon that was done on the main system (Oct 28, 2025).

**Standard:** `lowercase_with_underscores`
- No hyphens in names
- No CamelCase
- Exception: Standard directories (Music, Desktop, etc. can stay capitalized if needed)

---

## Items to Rename

### 🔴 CRITICAL - Docker Container Dependencies

These directories are mounted in active Docker containers and require container restart:

| Current Name | New Name | Used By | Action Required |
|--------------|----------|---------|-----------------|
| `jellyfin-cache/` | `jellyfin_cache/` | jellyfin container | Stop, rename, update config, restart |
| `jellyfin-config/` | `jellyfin_config/` | jellyfin container | Stop, rename, update config, restart |
| `nodered_data/` | Already correct ✅ | nodered container | No change needed |

**Impact:** Jellyfin container must be stopped and reconfigured

### 🟡 MEDIUM - Working Directories

These directories are not in active use by containers:

| Current Name | New Name | Notes |
|--------------|----------|-------|
| `claude-workspace/` | `claude_workspace/` | Claude workspace files |
| `media-import/` | `media_import/` | Media staging directory |
| `ScannedDocuments/` | `scanned_documents/` | Scanned document storage |
| `Skippy/` | `skippy/` | Skippy system files |

**Impact:** Low - Just rename directories

### 🟢 LOW - Configuration Files

| Current Name | New Name | Notes |
|--------------|----------|-------|
| `config-media.yaml` | `config_media.yaml` | NexusController config |
| `docker-compose.media.yml` | `docker_compose_media.yml` | Docker compose file |
| `docker-compose.yml` | `docker_compose.yml` | Docker compose file |
| `ebonhawk-maintenance.service` | `ebonhawk_maintenance.service` | Systemd service file |
| `nexus-media-monitor.service` | `nexus_media_monitor.service` | Systemd service file |

**Impact:** Need to update systemd service references

### 🔵 KEEP AS-IS

These should NOT be renamed:

| File/Directory | Reason |
|----------------|--------|
| `Dockerfile` | Standard Docker naming convention |
| `README.md` | Standard documentation naming |
| `Music/` | Standard user directory (XDG) |
| `.bash_history` | Hidden config file |
| `.home-server` | Hidden config file |
| `.unified-system-manager` | Hidden config file |
| `.wget-hsts` | Hidden config file |
| `noip-2.1.9-1/` | Third-party software (version in name) |
| `speedtest-cli` | Third-party tool (keep original name) |
| Archive files (`.tar.gz`) | Can be renamed but low priority |

---

## Docker Container Update Plan

### Jellyfin Container

**Current Configuration:**
```yaml
volumes:
  - /home/ebon/jellyfin-cache:/cache
  - /home/ebon/jellyfin-config:/config
  - /mnt/media/MUSIC_BY_ALBUM:/media/music:ro
```

**New Configuration:**
```yaml
volumes:
  - /home/ebon/jellyfin_cache:/cache
  - /home/ebon/jellyfin_config:/config
  - /mnt/media/MUSIC_BY_ALBUM:/media/music:ro
```

**Update Steps:**
1. Stop jellyfin container
2. Rename directories
3. Update docker-compose.yml or docker run command
4. Restart container
5. Verify Jellyfin accessible at http://10.0.0.29:8096

---

## Systemd Service Updates

### Services to Update

1. **ebonhawk-maintenance.service** → `ebonhawk_maintenance.service`
   - Location: `/etc/systemd/system/`
   - Action: Rename file, reload systemd daemon

2. **nexus-media-monitor.service** → `nexus_media_monitor.service`
   - Location: `/etc/systemd/system/`
   - Action: Rename file, reload systemd daemon

**Commands:**
```bash
sudo systemctl stop ebonhawk-maintenance.service
sudo mv /etc/systemd/system/ebonhawk-maintenance.service /etc/systemd/system/ebonhawk_maintenance.service
sudo systemctl daemon-reload
sudo systemctl enable ebonhawk_maintenance.service
sudo systemctl start ebonhawk_maintenance.service
```

---

## Execution Plan

### Phase 1: Preparation (No Changes)
**Estimated Time:** 5 minutes

```bash
# 1. Create backup directory
ssh ebon "mkdir -p ~/backups/pre_cleanup_$(date +%Y%m%d)"

# 2. Backup current Docker configurations
ssh ebon "docker inspect jellyfin > ~/backups/pre_cleanup_$(date +%Y%m%d)/jellyfin_config.json"
ssh ebon "cp docker-compose*.yml ~/backups/pre_cleanup_$(date +%Y%m%d)/ 2>/dev/null || true"

# 3. Document current service status
ssh ebon "systemctl status ebonhawk-maintenance.service nexus-media-monitor.service > ~/backups/pre_cleanup_$(date +%Y%m%d)/services_status.txt 2>&1 || true"

# 4. Take directory listing snapshot
ssh ebon "ls -laR /home/ebon > ~/backups/pre_cleanup_$(date +%Y%m%d)/directory_before.txt"
```

### Phase 2: Stop Services
**Estimated Time:** 2 minutes

```bash
# 1. Stop Docker containers
ssh ebon "docker stop jellyfin"

# 2. Stop systemd services (if running)
ssh ebon "sudo systemctl stop ebonhawk-maintenance.service 2>/dev/null || true"
ssh ebon "sudo systemctl stop nexus-media-monitor.service 2>/dev/null || true"
```

### Phase 3: Rename Directories (Low Risk First)
**Estimated Time:** 2 minutes

```bash
# Non-critical directories first
ssh ebon "cd /home/ebon && mv claude-workspace claude_workspace 2>/dev/null || true"
ssh ebon "cd /home/ebon && mv media-import media_import 2>/dev/null || true"
ssh ebon "cd /home/ebon && mv ScannedDocuments scanned_documents 2>/dev/null || true"
ssh ebon "cd /home/ebon && mv Skippy skippy 2>/dev/null || true"
```

### Phase 4: Rename Docker Volume Directories
**Estimated Time:** 1 minute

```bash
# Critical directories (Docker mounts)
ssh ebon "cd /home/ebon && mv jellyfin-cache jellyfin_cache"
ssh ebon "cd /home/ebon && mv jellyfin-config jellyfin_config"
```

### Phase 5: Rename Configuration Files
**Estimated Time:** 2 minutes

```bash
ssh ebon "cd /home/ebon && mv config-media.yaml config_media.yaml 2>/dev/null || true"
ssh ebon "cd /home/ebon && mv docker-compose.media.yml docker_compose_media.yml 2>/dev/null || true"
ssh ebon "cd /home/ebon && mv docker-compose.yml docker_compose.yml 2>/dev/null || true"
```

### Phase 6: Update Docker Configuration
**Estimated Time:** 3 minutes

**Option A: Update docker-compose.yml**
```bash
# Edit docker_compose.yml to update volume paths
ssh ebon "sed -i 's|jellyfin-cache|jellyfin_cache|g' docker_compose*.yml"
ssh ebon "sed -i 's|jellyfin-config|jellyfin_config|g' docker_compose*.yml"
```

**Option B: Docker run command (if not using compose)**
```bash
# You'll need to provide the current docker run command
# We'll update it with new paths
```

### Phase 7: Update Systemd Services
**Estimated Time:** 2 minutes

```bash
# Rename service files
ssh ebon "sudo mv /etc/systemd/system/ebonhawk-maintenance.service /etc/systemd/system/ebonhawk_maintenance.service 2>/dev/null || true"
ssh ebon "sudo mv /etc/systemd/system/nexus-media-monitor.service /etc/systemd/system/nexus_media_monitor.service 2>/dev/null || true"

# Reload systemd
ssh ebon "sudo systemctl daemon-reload"

# Re-enable services with new names
ssh ebon "sudo systemctl enable ebonhawk_maintenance.service 2>/dev/null || true"
ssh ebon "sudo systemctl enable nexus_media_monitor.service 2>/dev/null || true"
```

### Phase 8: Restart Services
**Estimated Time:** 2 minutes

```bash
# Start Docker containers
ssh ebon "docker start jellyfin"

# Start systemd services
ssh ebon "sudo systemctl start ebonhawk_maintenance.service 2>/dev/null || true"
ssh ebon "sudo systemctl start nexus_media_monitor.service 2>/dev/null || true"
```

### Phase 9: Verification
**Estimated Time:** 5 minutes

```bash
# 1. Check Docker container status
ssh ebon "docker ps --filter name=jellyfin"

# 2. Check Jellyfin health
ssh ebon "curl -s http://localhost:8096/health || echo 'Jellyfin not responding'"

# 3. Check systemd services
ssh ebon "systemctl status ebonhawk_maintenance.service --no-pager"
ssh ebon "systemctl status nexus_media_monitor.service --no-pager"

# 4. Verify Jellyfin accessible
curl -s http://10.0.0.29:8096/health

# 5. Check directory structure
ssh ebon "ls -la /home/ebon | grep -E 'jellyfin|claude|media|Scanned|Skippy'"
```

---

## Rollback Plan

If anything goes wrong:

```bash
# Stop all services
ssh ebon "docker stop jellyfin"
ssh ebon "sudo systemctl stop ebonhawk_maintenance.service nexus_media_monitor.service 2>/dev/null || true"

# Restore from backup
BACKUP_DATE=$(date +%Y%m%d)
ssh ebon "cd /home/ebon && mv jellyfin_cache jellyfin-cache"
ssh ebon "cd /home/ebon && mv jellyfin_config jellyfin-config"
ssh ebon "cd /home/ebon && mv claude_workspace claude-workspace"
ssh ebon "cd /home/ebon && mv media_import media-import"
ssh ebon "cd /home/ebon && mv scanned_documents ScannedDocuments"
ssh ebon "cd /home/ebon && mv skippy Skippy"

# Restore Docker configs
ssh ebon "cp ~/backups/pre_cleanup_$BACKUP_DATE/docker-compose*.yml /home/ebon/"

# Restore systemd services
ssh ebon "sudo mv /etc/systemd/system/ebonhawk_maintenance.service /etc/systemd/system/ebonhawk-maintenance.service 2>/dev/null || true"
ssh ebon "sudo systemctl daemon-reload"

# Restart services
ssh ebon "docker start jellyfin"
```

---

## Risk Assessment

### Low Risk ✅
- Renaming non-Docker directories: `claude-workspace`, `media-import`, `ScannedDocuments`, `Skippy`
- Renaming config files not currently in use
- Total downtime: <1 minute

### Medium Risk ⚠️
- Renaming Docker volume directories
- Updating docker-compose.yml
- Jellyfin downtime: 2-5 minutes
- Risk: Config might not update correctly (rollback available)

### High Risk 🔴
- Renaming systemd service files
- Risk: Services might not start with new names
- Mitigation: Keep old service definitions as backup

---

## Benefits

1. ✅ **Consistency** - Matches naming convention across all systems
2. ✅ **Standards compliance** - Follows lowercase_with_underscores standard
3. ✅ **Easier scripting** - No need to escape hyphens or handle CamelCase
4. ✅ **Professional** - Standardized infrastructure

---

## Timeline

**Total Estimated Time:** 25 minutes
- Preparation: 5 min
- Execution: 15 min
- Verification: 5 min

**Best Time to Execute:**
- During low-usage period
- When Jellyfin downtime acceptable (2-5 minutes)
- Not during media streaming

---

## Summary

### Files to Rename: 13 items
- 4 directories (CRITICAL - Docker mounts)
- 4 directories (LOW risk)
- 3 config files
- 2 systemd service files

### Services Affected:
- Jellyfin (restart required)
- ebonhawk-maintenance (optional)
- nexus-media-monitor (optional)

### Downtime:
- Jellyfin: 2-5 minutes
- Other services: 0-1 minute

---

## Next Steps

1. **Review this plan** - Make sure you're comfortable with the changes
2. **Choose execution time** - When is Jellyfin downtime acceptable?
3. **Execute or skip** - Your choice:
   - Execute: Follow phases 1-9
   - Skip: Ebon is stable, leave as-is
   - Partial: Only rename non-Docker directories (low risk)

---

**Status:** ✅ Plan complete, ready for review
**Created:** 2025-10-31
**Reviewed:** Pending user decision

---

## ADDENDUM: Script and Conversation Migration

### Scripts Found on Ebon

**Total Scripts:** 73 Python/Shell scripts in `/home/ebon/`

**Categories Identified:**
1. **Music Organization** (13 scripts) - One-time use, can archive
2. **Setup/Installation** (15 scripts) - One-time use, can archive  
3. **System Monitoring** (8 scripts) - Move to skippy/scripts/monitoring/
4. **Automation** (12 scripts) - Move to skippy/scripts/automation/
5. **Backup** (5 scripts) - Move to skippy/scripts/backup/
6. **NexusController/Maintenance** (10 scripts) - Move to skippy/scripts/monitoring/
7. **Utilities** (10 scripts) - Move to skippy/scripts/utility/

### Conversations Found on Ebon

**Location:** `/home/ebon/Skippy/conversations/`
**Total:** 12 conversation files (Aug-Sep 2025)

**Status:** ✅ Already present in `/home/dave/skippy/conversations/`
- These were copied during previous sessions
- ebon copies can be archived/deleted

### Migration Plan

#### Phase 1: Copy Scripts to Main System

```bash
# Create temporary staging directory
mkdir -p /tmp/ebon_scripts_migration

# Copy all scripts from ebon
scp ebon:/home/ebon/*.{py,sh} /tmp/ebon_scripts_migration/ 2>/dev/null

# Review and categorize
ls -lh /tmp/ebon_scripts_migration/
```

#### Phase 2: Categorize and Move to Skippy

```bash
# Music organization scripts (archive - one-time use)
mkdir -p /home/dave/skippy/scripts/archive/music_organization/
mv /tmp/ebon_scripts_migration/album*.py /home/dave/skippy/scripts/archive/music_organization/
mv /tmp/ebon_scripts_migration/music_*.py /home/dave/skippy/scripts/archive/music_organization/
mv /tmp/ebon_scripts_migration/*music*.sh /home/dave/skippy/scripts/archive/music_organization/

# Setup scripts (archive - one-time use)
mkdir -p /home/dave/skippy/scripts/archive/setup/
mv /tmp/ebon_scripts_migration/setup_*.sh /home/dave/skippy/scripts/archive/setup/
mv /tmp/ebon_scripts_migration/configure_*.sh /home/dave/skippy/scripts/archive/setup/

# Active monitoring scripts
mv /tmp/ebon_scripts_migration/ebon_maintenance_agent.py /home/dave/skippy/scripts/monitoring/ebon_maintenance_agent_v1.0.0.py
mv /tmp/ebon_scripts_migration/system_monitor.sh /home/dave/skippy/scripts/monitoring/system_monitor_v1.0.0.sh
mv /tmp/ebon_scripts_migration/enhanced_media_monitor.py /home/dave/skippy/scripts/monitoring/enhanced_media_monitor_v1.0.0.py

# Automation scripts
mv /tmp/ebon_scripts_migration/watchdog.sh /home/dave/skippy/scripts/automation/watchdog_v1.0.0.sh
mv /tmp/ebon_scripts_migration/auto_recovery.sh /home/dave/skippy/scripts/automation/auto_recovery_v1.0.0.sh

# Backup scripts  
mv /tmp/ebon_scripts_migration/simple_backup.sh /home/dave/skippy/scripts/backup/simple_backup_v1.0.0.sh
mv /tmp/ebon_scripts_migration/gdrive_backup.sh /home/dave/skippy/scripts/backup/gdrive_backup_v1.0.0.sh

# Utility scripts
mv /tmp/ebon_scripts_migration/update_jellyfin_library.sh /home/dave/skippy/scripts/utility/update_jellyfin_library_v1.0.0.sh
mv /tmp/ebon_scripts_migration/expand_lvm.sh /home/dave/skippy/scripts/utility/expand_lvm_v1.0.0.sh
```

#### Phase 3: Apply Naming Convention

```bash
# Rename to lowercase_with_underscores and add versioning
cd /home/dave/skippy/scripts/

# This will be done file-by-file during migration
# Using the script_saving_protocol.md standards
```

#### Phase 4: Clean Up Ebon

```bash
# After verifying scripts are safely copied to skippy:

# Archive scripts on ebon
ssh ebon "mkdir -p ~/scripts_archived_$(date +%Y%m%d)"
ssh ebon "mv ~/*.py ~/*.sh ~/scripts_archived_$(date +%Y%m%d)/ 2>/dev/null || true"

# Archive Skippy directory
ssh ebon "mv ~/Skippy ~/skippy_archived_$(date +%Y%m%d)"

# Verify only Docker/config files remain
ssh ebon "ls -la ~/ | grep -E '(\.py|\.sh|Skippy)'"
```

### Script Migration Checklist

- [ ] Copy all 73 scripts from ebon to staging directory
- [ ] Review each script and determine:
  - [ ] Active use (move to appropriate skippy category)
  - [ ] One-time use (archive)
  - [ ] Duplicate of existing (delete)
  - [ ] Obsolete (delete)
- [ ] Apply semantic versioning (v1.0.0)
- [ ] Apply lowercase_with_underscores naming
- [ ] Add to appropriate skippy/scripts/ categories
- [ ] Update script index
- [ ] Test critical scripts still work
- [ ] Archive originals on ebon (don't delete yet)
- [ ] Verify backups before cleaning ebon

### Estimated Impact

**Scripts to Migrate:**
- Active/Keep: ~20 scripts (monitoring, automation, backup, utility)
- Archive: ~40 scripts (one-time setup, music organization)
- Delete/Duplicate: ~13 scripts (duplicates of existing)

**Storage Impact:**
- Main system: +~500KB (active scripts)
- Archive: +~2MB (historical scripts)
- ebon cleanup: Frees ~3MB in home directory

**Time Estimate:**
- Script migration: 30-45 minutes
- Review and categorization: 20 minutes  
- Testing: 15 minutes
- **Total: ~1.5 hours**

### Benefits

1. ✅ All scripts centralized in skippy repository
2. ✅ Consistent naming across all scripts
3. ✅ Proper version control
4. ✅ Clean ebon home directory (only Docker/configs)
5. ✅ Better discoverability (all scripts in one place)
6. ✅ Proper categorization and archival

