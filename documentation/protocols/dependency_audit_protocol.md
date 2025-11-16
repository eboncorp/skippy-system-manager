# Dependency Audit Protocol

**Version**: 1.0.0
**Last Updated**: 2025-11-16
**Owner**: System Administration

---

## Context

This protocol ensures all software dependencies (Python packages, npm modules, system packages) are kept secure, up-to-date, and properly tracked to prevent vulnerabilities and compatibility issues.

## Purpose

- Identify vulnerable dependencies
- Track dependency versions
- Enforce version pinning
- Plan safe upgrades
- Prevent supply chain attacks

---

## Dependency Inventory

### Python Packages (pip)

**Location**: `/home/dave/skippy/mcp-servers/general-server/.venv/`

```bash
# List all installed packages
pip list --format=freeze > requirements_current.txt

# Check for outdated packages
pip list --outdated

# Check for vulnerabilities
pip-audit  # if installed

# Or use safety
pip install safety
safety check -r requirements.txt
```

### System Packages (apt)

```bash
# List installed packages
dpkg -l > /home/dave/skippy/system_packages.txt

# Check for security updates
sudo apt update
apt list --upgradable 2>/dev/null | grep -i security
```

### JavaScript/Node (npm)

```bash
# If any npm projects exist
npm audit
npm outdated
```

### WordPress Plugins

```bash
# Via WP-CLI or direct check
wp plugin list --fields=name,version,update_version
```

---

## Weekly Audit Script

```bash
#!/bin/bash
# dependency_audit_v1.0.0.sh

REPORT_FILE="/home/dave/skippy/conversations/dependency_audit_$(date +%Y%m%d).md"

echo "# Dependency Audit Report" > "$REPORT_FILE"
echo "**Date:** $(date)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Python Packages
echo "## Python Packages" >> "$REPORT_FILE"

cd /home/dave/skippy/mcp-servers/general-server
if [ -d ".venv" ]; then
    source .venv/bin/activate

    echo "### Outdated Packages" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
    pip list --outdated >> "$REPORT_FILE" 2>&1
    echo '```' >> "$REPORT_FILE"

    echo "### Vulnerability Check" >> "$REPORT_FILE"
    if command -v pip-audit &> /dev/null; then
        echo '```' >> "$REPORT_FILE"
        pip-audit >> "$REPORT_FILE" 2>&1
        echo '```' >> "$REPORT_FILE"
    else
        echo "pip-audit not installed. Install with: pip install pip-audit" >> "$REPORT_FILE"
    fi

    deactivate
fi

# System Packages
echo "" >> "$REPORT_FILE"
echo "## System Packages" >> "$REPORT_FILE"

SECURITY_UPDATES=$(apt list --upgradable 2>/dev/null | grep -i security | wc -l)
echo "Security updates available: $SECURITY_UPDATES" >> "$REPORT_FILE"

if [ "$SECURITY_UPDATES" -gt 0 ]; then
    echo "### Security Updates Pending" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
    apt list --upgradable 2>/dev/null | grep -i security >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
fi

# WordPress Plugins
echo "" >> "$REPORT_FILE"
echo "## WordPress Plugins" >> "$REPORT_FILE"

WP_PATH="/home/dave/skippy/rundaverun_local_site/app/public"
if [ -d "$WP_PATH" ]; then
    OUTDATED_PLUGINS=$(grep "Version:" $WP_PATH/wp-content/plugins/*/**.php 2>/dev/null | head -20)
    echo "### Plugin Versions" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
    ls -la $WP_PATH/wp-content/plugins/ | grep "^d" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
fi

# Summary
echo "" >> "$REPORT_FILE"
echo "## Action Required" >> "$REPORT_FILE"

if [ "$SECURITY_UPDATES" -gt 5 ]; then
    echo "- **HIGH PRIORITY**: $SECURITY_UPDATES security updates pending" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"
echo "Report saved: $REPORT_FILE"
```

---

## Version Pinning Policy

### Requirements Files

**Always pin exact versions:**

```txt
# requirements.txt - GOOD
requests==2.32.5
google-api-python-client==2.187.0
slack-sdk==3.37.0

# requirements.txt - BAD (unpinned)
requests
google-api-python-client>=2.0
slack-sdk
```

### Generate Pinned Requirements

```bash
# Export exact versions
pip freeze > requirements_pinned.txt

# Review before committing
diff requirements.txt requirements_pinned.txt
```

### Lock Files

- Use `requirements.txt` with exact versions
- Consider `pip-compile` for better dependency resolution
- Keep `requirements_backup.txt` before major upgrades

---

## Upgrade Procedure

### Step 1: Audit Current State

```bash
# Create snapshot
pip freeze > before_upgrade.txt
cp package.json before_upgrade_npm.json 2>/dev/null
```

### Step 2: Check for Breaking Changes

```bash
# Review changelogs for major version bumps
# Check compatibility matrix
# Review deprecated features
```

### Step 3: Upgrade in Development First

```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate

# Install updated packages
pip install -r requirements_new.txt

# Run tests
python -m pytest tests/
```

### Step 4: Validate Functionality

```bash
# Test critical paths
# Verify API compatibility
# Check performance metrics
# Monitor for errors
```

### Step 5: Deploy to Production

```bash
# Update production after successful testing
pip install -r requirements_pinned.txt

# Document the change
echo "$(date): Upgraded [package] from [old] to [new]" >> upgrade_log.txt
```

---

## Vulnerability Response

### Critical (CVE with active exploits)

**Response Time**: Immediate (same day)

1. Verify vulnerability affects your usage
2. Check if patch available
3. Apply patch or implement workaround
4. Monitor for exploitation attempts

### High (Known vulnerability, no exploit)

**Response Time**: Within 1 week

1. Schedule upgrade
2. Test in development
3. Deploy to production
4. Update requirements file

### Medium/Low

**Response Time**: Next regular maintenance window

1. Add to upgrade queue
2. Include in next audit cycle
3. Update documentation

---

## Dependency Health Checks

### Daily (Automated)

```bash
# Check for critical vulnerabilities
safety check -r requirements.txt --short

# Result: 0 vulnerabilities = OK
```

### Weekly (Manual Review)

- Review outdated packages
- Check security advisories
- Verify backup requirements exist
- Test critical integrations

### Monthly (Comprehensive)

- Full vulnerability scan
- License compliance check
- Dependency tree analysis
- Update documentation

---

## Dependency Tree Analysis

```bash
# Show dependency tree
pip show [package] | grep Requires

# Full tree visualization
pip install pipdeptree
pipdeptree

# Find conflicts
pipdeptree --warn conflict
```

---

## License Compliance

```bash
# Check licenses
pip install pip-licenses
pip-licenses

# Export license report
pip-licenses --format=csv > licenses.csv

# Check for problematic licenses
pip-licenses | grep -E "GPL|AGPL|LGPL"
```

---

## Supply Chain Security

### Best Practices

1. **Use verified packages** from PyPI/npm
2. **Pin exact versions** to prevent auto-update surprises
3. **Verify checksums** when possible
4. **Review package source** before adding new dependencies
5. **Limit dependencies** to necessary packages only

### Red Flags

- Package with very few downloads
- Package name similar to popular package (typosquatting)
- New package with no history
- Package from unknown maintainer
- Package requesting excessive permissions

---

## Backup and Recovery

### Before Major Upgrades

```bash
# Create full backup
pip freeze > /home/dave/skippy/backups/requirements_$(date +%Y%m%d).txt

# Backup virtual environment
tar -czf venv_backup_$(date +%Y%m%d).tar.gz .venv/
```

### Recovery from Failed Upgrade

```bash
# Restore from backup
pip install -r /home/dave/skippy/backups/requirements_YYYYMMDD.txt

# Or restore entire venv
rm -rf .venv/
tar -xzf venv_backup_YYYYMMDD.tar.gz
```

---

## Quick Reference

```bash
# Check outdated
pip list --outdated

# Check vulnerabilities (if pip-audit installed)
pip-audit

# Pin versions
pip freeze > requirements.txt

# Upgrade specific package
pip install --upgrade [package]==X.Y.Z

# System security updates
sudo apt update && sudo apt upgrade -y
```

---

## Integration with Other Protocols

- **Health Check Protocol**: Include dependency health in checks
- **Update and Maintenance Protocol**: Schedule regular audits
- **Security Protocol**: Respond to vulnerabilities
- **Incident Response**: Handle compromised packages

---

**Generated**: 2025-11-16
**Status**: Active
**Next Review**: 2025-12-16
